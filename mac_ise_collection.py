import asyncio
import datetime
import getpass
import io
import os
import re
import socket
import sys
import typing

import httpx
from scrapli.driver import AsyncGenericDriver
from scrapli.driver.core.cisco_iosxe.async_driver import AsyncIOSXEDriver
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliConnectionNotOpened
from scrapli.logging import enable_basic_logging


def parse_show_tech(show_tech_ouput: str) -> dict[str, list[str]]:
    """
    Takes the output of the show tech and parses it into a dictionary of sections
    """
    command_output = {}
    current_section_cmd = None
    current_section_content = []
    current_section_start = 0

    lines = show_tech_ouput.splitlines()
    for line_number, line in enumerate(lines):
        if current_section_cmd is None and "*" * 41 in line:
            current_section_cmd = lines[line_number + 1]
            current_section_start = line_number
        if line_number <= current_section_start + 2:
            continue
        if line == "*" * 41:
            command_output[current_section_cmd] = current_section_content
            current_section_cmd = lines[line_number + 1]
            current_section_start = line_number
            current_section_content = []
            continue
        current_section_content.append(line)

    command_output[current_section_cmd] = current_section_content
    return command_output


def parse_deployment(command_output: list[str]) -> list[dict]:
    """
    Takes the deployment information from the 'show tech' and parses out the nodes into a list of dictionaries
    """
    node_output_chunk = re.search(
        r"\-+\n(.*)DEPLOYMENT_ID", "\n".join(command_output), re.DOTALL
    )
    nodes = []
    for line in (l for l in node_output_chunk[1].splitlines() if l):
        node_info = re.search(
            r"^(?P<node>\S+)\s+(?P<persona>\S+)\s+(?P<role>\S+)\s+(?P<active>\S+)\s+(?P<replication>.*)$",
            line,
        )
        nodes.append(node_info.groupdict())
    return nodes


def collect_input_from_user() -> tuple[str, str, str, str, str]:
    """
    Collects the input from the user or envionment variables
    """
    sr_regex = re.compile(r"^6\d{8}$")
    if "CXD_SR" not in os.environ:
        sr = input("Please enter the TAC Case Number: ")
    else:
        sr = os.environ["CXD_SR"]

    if not sr_regex.search(sr):
        print("Error: TAC Case Number must be a valid SR number (6xxxxxxxx)")
        sys.exit(1)

    token_regex = re.compile(r"^\S{10,20}$")
    if "CXD_TOKEN" not in os.environ:
        token = input("Please enter the CXD Token provided by TAC: ")
    else:
        token = os.environ["CXD_TOKEN"]

    if not token_regex.search(token):
        print("Error: CXD Token must be a valid token")
        sys.exit(1)

    if "SSH_ADDRESS" not in os.environ:
        node = input("Please enter the hostname or IP address of the ISE node: ")
    else:
        username = os.environ["SSH_ADDRESS"]

    if "SSH_USERNAME" not in os.environ:
        username = input("Please enter the username to connect to the ISE node: ")
    else:
        username = os.environ["SSH_USERNAME"]

    if "SSH_PASSWORD" not in os.environ:
        password = getpass.getpass(
            prompt="Please enter the password to connect to the ISE node: "
        )
    else:
        password = os.environ["SSH_PASSWORD"]

    return sr, token, node, username, password


async def collect_show_tech_from_device(
    node: str,
    username: str,
    password: str,
    stop_after_getting_deployment_info: bool = False,
) -> bytes:
    """
    Connects to the node and collects the 'show tech' output.
    """

    comms_prompt_pattern = r"(^[\w.\-@/:]{1,63}>$)|(^[\w.\-@/:]{1,63}#$)|(^[\w.\-@/:]{1,63}\([\w.\-@/:+]{0,32}\)#$)|(^([\w.\-@/+>:]+\(tcl\)[>#]|\+>)$)"  # copied the IOSXE prompt
    comms_prompt_pattern_and_more = r"(^[\w.\-@/:]{1,63}>$)|(^[\w.\-@/:]{1,63}#$)|(^[\w.\-@/:]{1,63}\([\w.\-@/:+]{0,32}\)#$)|(^([\w.\-@/+>:]+\(tcl\)[>#]|\+>)$)|(--More--)"  # copied the IOSXE prompt and added --More--
    output = b""
    async with AsyncGenericDriver(
        host=node,
        auth_username=username,
        auth_password=password,
        auth_strict_key=False,
        timeout_socket=10,
        timeout_transport=3600,
        transport="asyncssh",
        comms_prompt_pattern=comms_prompt_pattern_and_more,
    ) as conn:
        # Execute the command then
        prompt = await conn.get_prompt()
        conn.channel.transport.write("show tech-support\n".encode())
        print(f"Connected to {node} - collecting 'show tech' this may take a while...")
        output += await conn.channel.transport.read()
        last_report = datetime.datetime.now(datetime.UTC)
        prompt_re = re.compile(pattern=comms_prompt_pattern, flags=re.MULTILINE)
        max_size_to_collect = 2097152  # 2MB
        while True:
            conn.channel.transport.write(" ".encode())
            chunk = await conn.channel.transport.read()
            output += chunk
            total_size = len(output)
            if (datetime.datetime.now(datetime.UTC) - last_report).total_seconds() > 5:
                print(f"{node} - Got {total_size} bytes")
                last_report = datetime.datetime.now(datetime.UTC)

            if (
                stop_after_getting_deployment_info
                and b"Displaying ISE Node Group Information" in output
            ):
                # The deployment information is close to the beginning of the show tech, so we can stop collecting now
                conn.channel.transport.write("q".encode())
                break

            if total_size > max_size_to_collect:
                # Stop collecting, we should have enough now
                break

            if prompt_re.search(output[-100:].decode(errors="ignore")):
                # Got back to prompt
                break

    # Strip out the control characters and the --More-- prompt
    return clean_chunk(output)


async def discover_deployment(node: str, username: str, password: str) -> list[dict]:
    """
    Connects to the node and collects the 'show tech' output and parses out the deployment information
    """
    show_tech = await collect_show_tech_from_device(
        node=node,
        username=username,
        password=password,
        stop_after_getting_deployment_info=True,
    )
    parsed_show_tech = parse_show_tech(show_tech.decode())
    return parse_deployment(parsed_show_tech["Displaying ISE deployment ... "])


def prompt_for_nodes_to_collect_from(nodes: list[dict]) -> list[dict]:
    """
    Asks the user which nodes to collect from. Returns a list of nodes
    """
    print("We found the following nodes in your deployment:")
    for node in nodes:
        print(f"NODE: {node['node']} - {node['persona']} - {node['role']}")
    print("\n\n")
    nodes_to_collect = []
    for node in nodes:
        collect = input(f"Collect from {node['node']} (Y/n): ")
        if collect.lower().startswith("y"):
            nodes_to_collect.append(node)
    return nodes_to_collect


async def upload_text_file_to_cxd(
    file_handle: typing.BinaryIO, filename: str, sr: str, token: str
):
    """
    Uploads the file to CXD (from this computer)
    """
    print(f"Uploading {filename} to CXD")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://cxd.cisco.com/home/",
            auth=(sr, token),
            files={filename: (filename, file_handle, "text/plain")},
            headers={"User-Agent": "curl/8.1.2"},
        )
        response_text = response.text
        # Sometimes CXD returns 302s, but the file is still uploaded.  So we'll ignore 302s
        if response.status_code not in (200, 302):
            print(
                f"Error uploading file '{filename}' to CXD: {response.status_code} - '{response_text}'"
            )
            raise ValueError(f"Error uploading file '{filename}' to CXD")
        print(f"Successfully uploaded {filename} to CXD")


async def create_and_upload_diag_bundle(
    node: str, sr: str, token: str, username: str, password: str
):
    async with AsyncIOSXEDriver(
        host=node,
        auth_username=username,
        auth_password=password,
        auth_strict_key=False,
        timeout_socket=10,
        timeout_transport=3600,
        transport="asyncssh",
    ) as conn:
        await conn.get_prompt()
        repository_name = f"TAC-{sr}"
        # Check if the repository already exists
        show_repo_output = await generic_send_command(
            conn=conn, command="show running-config repository"
        )
        await conn.get_prompt()
        if repository_name in show_repo_output:
            print(f"Repository already exists on {node}")
        else:
            # Make sure the node can connect to the Cisco SFTP server
            print(f"Adding CXD repository to {node}")
            ssh_key = await conn.send_command(
                "crypto host_key add host cxd.cisco.com", timeout_ops=10
            )
            cxd_rsa_sha256_fingerprint = (
                "SHA256:acJn5OmbrtHv6jsm0tdBnOU0Cv1VOIv+G4uN6/H6akI"
            )
            cxd_ed22519_sha256_fingerprint = (
                "SHA256:GtnA5oZQ0x6J+73apOIGQUse+qHVj/Jn3sJ8+XHjjW"
            )
            if not any(
                [
                    cxd_rsa_sha256_fingerprint in ssh_key.result,
                    cxd_ed22519_sha256_fingerprint in ssh_key.result,
                ]
            ):
                raise ValueError(
                    "SSH Fingerprint doesn't match expected ones.  Can't validate that we are connecting to Cisco SFTP server. Aborting."
                )
            await conn.send_configs(
                [
                    f"repository {repository_name}",
                    "url sftp://cxd.cisco.com/",
                    f"user {sr} password plain {token}",
                    "end",
                ],
                timeout_ops=3,
            )
            print(f"Successfully added CXD repository to {node}")
        await conn.get_prompt()
        await generate_and_upload_diag_bundle(node=node, sr=sr, conn=conn)
        print(f"Successfully created and uploaded 'Diagnostic Bundle' from {node}")


async def collect_from_node(
    node: str, sr: str, token: str, username: str, password: str
):
    print(f"Collecting a 'show tech' from {node}")
    show_tech_output = await collect_show_tech_from_device(
        node=node,
        username=username,
        password=password,
        stop_after_getting_deployment_info=False,
    )
    print(f"Successfully collected 'show tech' from {node}")
    show_tech_output_file = io.BytesIO(show_tech_output)
    now = datetime.datetime.now(datetime.UTC)
    now_str = datetime.datetime.strftime(now, "%Y%m%d%H%M%S")
    await upload_text_file_to_cxd(
        file_handle=show_tech_output_file,
        filename=f"ise_show_tech_{node}_{now_str}.txt",
        sr=sr,
        token=token,
    )
    print(f"Successfully uploaded 'show tech' from {node}")
    await create_and_upload_diag_bundle(
        node=node, sr=sr, token=token, username=username, password=password
    )
    print(f"Successfully collected all necessary from node {node}")


def clean_chunk(b: bytes) -> bytes:
    # Strip out the control characters and the --More-- prompt
    b = b.replace(b"\x1b[7m--More--\x1b[27m\x1b[8D\x1b[K", b"")
    b = b.replace(b"\x1b[01;31m\x1b[K", b"")
    b = b.replace(b"\x1b[7m(END)\x1b[27m\x1b[5D\x1b[K", b"")
    return b.replace(b"\r", b"")


async def generic_send_command(conn: AsyncGenericDriver, command: str) -> str:
    comms_prompt_pattern = r"(^[\w.\-@/:]{1,63}>$)|(^[\w.\-@/:]{1,63}#$)|(^[\w.\-@/:]{1,63}\([\w.\-@/:+]{0,32}\)#$)|(^([\w.\-@/+>:]+\(tcl\)[>#]|\+>)$)"  # copied the IOSXE prompt
    prompt_re = re.compile(pattern=comms_prompt_pattern, flags=re.MULTILINE)
    conn.channel.transport.write(f"{command}\n".encode())
    output = await conn.channel.transport.read()
    while True:
        conn.channel.transport.write(" ".encode())
        chunk = await conn.channel.transport.read()
        output = clean_chunk(output + chunk)
        if prompt_re.search(output[-100:].decode(errors="ignore")):
            # Got back to prompt
            break
    return output.decode()


async def generate_and_upload_diag_bundle(node: str, sr: str, conn: AsyncGenericDriver):
    print(
        f"Creating 'Diagnostic Bundle' on {node} and have the node upload to CXD directly.  This will take a while... ~45-90 minutes"
    )
    filename = f"ise-support-bundle-fr-{node}"
    repository_name = f"TAC-{sr}"
    comms_prompt_pattern = r"(^[\w.\-@/:]{1,63}>$)|(^[\w.\-@/:]{1,63}#$)|(^[\w.\-@/:]{1,63}\([\w.\-@/:+]{0,32}\)#$)|(^([\w.\-@/+>:]+\(tcl\)[>#]|\+>)$)"  # copied the IOSXE prompt
    prompt_re = re.compile(pattern=comms_prompt_pattern, flags=re.MULTILINE)

    # First enter the command and then answer the prompts
    await conn.get_prompt()
    conn.channel.transport.write(
        f"backup-logs {filename} repository {repository_name} public-key\n".encode()
    )
    output = await conn.channel.transport.read()
    output = clean_chunk(output).decode()
    while "Include Core and Heap dumps? (YES/NO):" not in output:
        output += clean_chunk(await conn.channel.transport.read()).decode()
    conn.channel.transport.write("no\n".encode())
    now = datetime.datetime.now()
    print(f"{now.isoformat()} NODE: {node} - {output}")
    while True:
        chunk = await conn.channel.transport.read()
        output = clean_chunk(output.encode() + chunk).decode()
        now = datetime.datetime.now()
        print(f"{now.isoformat()} NODE: {node} - {clean_chunk(chunk).decode()}")
        if prompt_re.search(output[-100:]):
            # Got back to prompt
            break

    return


async def main(sr: str, token: str, node: str, username: str, password: str):
    print("Starting")
    try:
        nodes = await discover_deployment(
            node=node, username=username, password=password
        )
    except ScrapliAuthenticationFailed as e:
        if str(e) == "all authentication methods failed":
            print(
                "Authentication failed.  Please check the username and password and try again."
            )
        if "timed out" in str(e):
            print(
                f"Timeout connecting to {node}.  Please check the IP address and try again."
            )
        return
    except socket.gaierror as e:
        print(f"Error connecting to {node}: {e}")
        return

    nodes_to_collect = prompt_for_nodes_to_collect_from(nodes=nodes)
    collection_results = await asyncio.gather(
        *[
            collect_from_node(
                node=node["node"],
                sr=sr,
                token=token,
                username=username,
                password=password,
            )
            for node in nodes_to_collect
        ],
        return_exceptions=True,
    )
    for node, result in zip(nodes_to_collect, collection_results):
        if isinstance(result, Exception):
            if isinstance(result, ScrapliConnectionNotOpened):
                print(f"Collection on node {node['node']} timed out")
            else:
                print(f"A problem occurred on {node['node']}: {result}")

    print("Successfully collected all necessary data from all nodes")


if __name__ == "__main__":
    print(
        """
    Welcome to the CX-FirstResponder ISE TAC Log Backup Tool.

    This tool will walk you through the process of backing up the logs from your ISE node and uploading
    them to the TAC Case for analysis.

    It will go through the following steps:
    1 - Connect to your ISE node via SSH
    2 - Find the nodes in your deployment
    3 - Ask you which nodes to collect diagnostics from
    4 - For each of the selected nodes, it will in parallel:
        a - Validate that the ISE node has connectivity the Cisco SFTP server
        b - Validate the SFTP server's SSH fingerprint to make sure it will be sending to Cisco's SFTP server
        c - Create a repository on the ISE node to store the logs called TAC-<TAC Case Number>
        d - Create a "show tech-support"
        e - Upload it to the TAC Case
        f - Create a "support diagnostic bundle"
        g - Upload it to the TAC Case
        h - Remove the repository from the ISE node

    The process of collecting diagnostics from your ISE node can take up to 45 minutes per node.  Please be patient.



    """
    )
    if os.environ.get("DEBUG") == "TRUE":
        enable_basic_logging(file=True, level="DEBUG")
    sr, token, node, username, password = collect_input_from_user()
    asyncio.run(
        main(sr=sr, token=token, node=node, username=username, password=password)
    )
