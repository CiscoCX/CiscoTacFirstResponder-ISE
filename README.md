# CiscoTacFirstResponder-ISE

Cisco TAC First Responder script for ISE.

These hosted scripts streamline the generation and transmission of diagnositic data from a ISE deployment to Cisco TAC.

## Collect a DART on Windows

Work - in - Progress

````

## Collect on MAC

The script is written for zsh, the default shell for the `Terminal.app` (Since Mac OS Catalina). Have the user open the `Terminal.app` and then paste the following in (with the `cxdUsername` and `cxdToken` replaced with the values you received from the Cisco TAC Engineer).

The script will do the following:
    - Download and install a copy of python into the following director ~/.cisco_firstresponder
    - Setup a virtual environment for the python install and install the python dependencies
        - scrapli[asyncssh]
        - httpx
    - Download the script `mac_ise_collection.py` into the following directory ~/.cisco_firstresponder
    - Execute the mac_ise_collection.py script which does:
        - Asks the user for the ISE hostname or IP address and user/password (ssh)
        - Connect to the server and find the deployment info
        - Ask the user for which nodes to collect data from.  For each node selected:
            - Connect via SSH
            - Collect a "show tech-support" and upload it to the CX Drive (CXD)
            - Configure a "repository" on the ISE node (sftp to cxd.cisco.com)
            - Collect a diagnostic bundle and upload it to the CX Drive (CXD)

```zsh
curl https://raw.githubusercontent.com/CiscoCX/CiscoTacFirstResponder-ISE/main/mac_ise_collection.zsh | cxdUsername=611111111 cxdToken=mkDOLk2YO9SyuEkz zsh -s
````

Example Output:

```
➜  ~ zsh mac_ise_collection.zsh
Welcome to the Cisco First Responder installer for MacOS.

This script will download and install a local copy of python3
in your home directory and then install the necessary dependencies
in a virtualenv.

Then it will execute a python script that will connect to ISE and run a collection script.

The script will be installed in ~/.cisco_firstresponder/ and can be easily removed by deleting that directory.
Do you want to continue (Y/n)? y
Starting....
Fetch python from python.org and install in ~/.cisco_firstresponder/
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 43.2M  100 43.2M    0     0  41.7M      0  0:00:01  0:00:01 --:--:-- 41.8M
126822 blocks
2318 blocks
5 blocks
./Resources: Can't replace existing directory with non-directory
214309 blocks
Create a virtualenv and install dependencies
Requirement already satisfied: pip in ./venv/lib/python3.12/site-packages (23.2.1)
Collecting wheel
  Obtaining dependency information for wheel from https://files.pythonhosted.org/packages/b8/8b/31273bf66016be6ad22bb7345c37ff350276cfd46e389a0c2ac5da9d9073/wheel-0.41.2-py3-none-any.whl.metadata
  Using cached wheel-0.41.2-py3-none-any.whl.metadata (2.2 kB)
Using cached wheel-0.41.2-py3-none-any.whl (64 kB)
Installing collected packages: wheel
Successfully installed wheel-0.41.2
Collecting setuptools
  Obtaining dependency information for setuptools from https://files.pythonhosted.org/packages/bb/26/7945080113158354380a12ce26873dd6c1ebd88d47f5bc24e2c5bb38c16a/setuptools-68.2.2-py3-none-any.whl.metadata
  Using cached setuptools-68.2.2-py3-none-any.whl.metadata (6.3 kB)
Using cached setuptools-68.2.2-py3-none-any.whl (807 kB)
Installing collected packages: setuptools
Successfully installed setuptools-68.2.2
Collecting httpx
  Obtaining dependency information for httpx from https://files.pythonhosted.org/packages/33/0d/d9ce469af019741c8999711d36b270ff992ceb1a0293f73f9f34fdf131e9/httpx-0.25.0-py3-none-any.whl.metadata
  Using cached httpx-0.25.0-py3-none-any.whl.metadata (7.6 kB)
Collecting scrapli[asyncssh]
  Obtaining dependency information for scrapli[asyncssh] from https://files.pythonhosted.org/packages/12/17/54ad25ba7c475a5ad1861c98bc58f35376ee4fed4bf4efa358166f5aad1d/scrapli-2023.7.30-py3-none-any.whl.metadata
  Using cached scrapli-2023.7.30-py3-none-any.whl.metadata (9.9 kB)
Collecting certifi (from httpx)
  Obtaining dependency information for certifi from https://files.pythonhosted.org/packages/4c/dd/2234eab22353ffc7d94e8d13177aaa050113286e93e7b40eae01fbf7c3d9/certifi-2023.7.22-py3-none-any.whl.metadata
  Using cached certifi-2023.7.22-py3-none-any.whl.metadata (2.2 kB)
Collecting httpcore<0.19.0,>=0.18.0 (from httpx)
  Obtaining dependency information for httpcore<0.19.0,>=0.18.0 from https://files.pythonhosted.org/packages/ac/97/724afbb7925339f6214bf1fdb5714d1a462690466832bf8fb3fd497649f1/httpcore-0.18.0-py3-none-any.whl.metadata
  Using cached httpcore-0.18.0-py3-none-any.whl.metadata (18 kB)
Collecting idna (from httpx)
  Using cached idna-3.4-py3-none-any.whl (61 kB)
Collecting sniffio (from httpx)
  Using cached sniffio-1.3.0-py3-none-any.whl (10 kB)
Collecting asyncssh<3.0.0,>=2.2.1 (from scrapli[asyncssh])
  Obtaining dependency information for asyncssh<3.0.0,>=2.2.1 from https://files.pythonhosted.org/packages/da/2d/153462da9ded3e63060be8c282276023d376f2846d2f22fb3519ddf524cc/asyncssh-2.14.0-py3-none-any.whl.metadata
  Using cached asyncssh-2.14.0-py3-none-any.whl.metadata (9.8 kB)
Collecting cryptography>=39.0 (from asyncssh<3.0.0,>=2.2.1->scrapli[asyncssh])
  Obtaining dependency information for cryptography>=39.0 from https://files.pythonhosted.org/packages/06/5d/f992c40471b60b762dca2b118c0a7837e446bea917f2be54b8f49802fe5e/cryptography-41.0.4-cp37-abi3-macosx_10_12_universal2.whl.metadata
  Using cached cryptography-41.0.4-cp37-abi3-macosx_10_12_universal2.whl.metadata (5.2 kB)
Collecting typing-extensions>=3.6 (from asyncssh<3.0.0,>=2.2.1->scrapli[asyncssh])
  Obtaining dependency information for typing-extensions>=3.6 from https://files.pythonhosted.org/packages/24/21/7d397a4b7934ff4028987914ac1044d3b7d52712f30e2ac7a2ae5bc86dd0/typing_extensions-4.8.0-py3-none-any.whl.metadata
  Using cached typing_extensions-4.8.0-py3-none-any.whl.metadata (3.0 kB)
Collecting anyio<5.0,>=3.0 (from httpcore<0.19.0,>=0.18.0->httpx)
  Obtaining dependency information for anyio<5.0,>=3.0 from https://files.pythonhosted.org/packages/36/55/ad4de788d84a630656ece71059665e01ca793c04294c463fd84132f40fe6/anyio-4.0.0-py3-none-any.whl.metadata
  Using cached anyio-4.0.0-py3-none-any.whl.metadata (4.5 kB)
Collecting h11<0.15,>=0.13 (from httpcore<0.19.0,>=0.18.0->httpx)
  Using cached h11-0.14.0-py3-none-any.whl (58 kB)
Collecting cffi>=1.12 (from cryptography>=39.0->asyncssh<3.0.0,>=2.2.1->scrapli[asyncssh])
  Obtaining dependency information for cffi>=1.12 from https://files.pythonhosted.org/packages/b4/f6/b28d2bfb5fca9e8f9afc9d05eae245bed9f6ba5c2897fefee7a9abeaf091/cffi-1.16.0-cp312-cp312-macosx_11_0_arm64.whl.metadata
  Using cached cffi-1.16.0-cp312-cp312-macosx_11_0_arm64.whl.metadata (1.5 kB)
Collecting pycparser (from cffi>=1.12->cryptography>=39.0->asyncssh<3.0.0,>=2.2.1->scrapli[asyncssh])
  Using cached pycparser-2.21-py2.py3-none-any.whl (118 kB)
Using cached httpx-0.25.0-py3-none-any.whl (75 kB)
Using cached asyncssh-2.14.0-py3-none-any.whl (351 kB)
Using cached httpcore-0.18.0-py3-none-any.whl (76 kB)
Using cached certifi-2023.7.22-py3-none-any.whl (158 kB)
Using cached scrapli-2023.7.30-py3-none-any.whl (141 kB)
Using cached anyio-4.0.0-py3-none-any.whl (83 kB)
Using cached cryptography-41.0.4-cp37-abi3-macosx_10_12_universal2.whl (5.3 MB)
Using cached typing_extensions-4.8.0-py3-none-any.whl (31 kB)
Using cached cffi-1.16.0-cp312-cp312-macosx_11_0_arm64.whl (177 kB)
Installing collected packages: typing-extensions, sniffio, scrapli, pycparser, idna, h11, certifi, cffi, anyio, httpcore, cryptography, httpx, asyncssh
Successfully installed anyio-4.0.0 asyncssh-2.14.0 certifi-2023.7.22 cffi-1.16.0 cryptography-41.0.4 h11-0.14.0 httpcore-0.18.0 httpx-0.25.0 idna-3.4 pycparser-2.21 scrapli-2023.7.30 sniffio-1.3.0 typing-extensions-4.8.0
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 16582  100 16582    0     0  40354      0 --:--:-- --:--:-- --:--:-- 40642

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




Please enter the TAC Case Number: 611111111
Please enter the CXD Token provided by TAC: TICGSSiiMsIabcd
Please enter the hostname or IP address of the ISE node: 172.18.124.20
Please enter the username to connect to the ISE node: admin
Please enter the password to connect to the ISE node: *******
Starting
Connected to 172.18.124.20 - collecting 'show tech' this may take a while...
172.18.124.20 - Got 1879 bytes
172.18.124.20 - Got 3110 bytes
172.18.124.20 - Got 4365 bytes
We found the following nodes in your deployment:
NODE: ise-maibock - PAN,MNT,PSN - SECONDARY
NODE: ise-dunkel - PAN,MNT,PSN - PRIMARY
NODE: zer0k-ise2 - PSN,PXG - SECONDARY
NODE: zer0k-ise1 - PSN,PXG - SECONDARY



Collect from ise-maibock (Y/n): y
Collect from ise-dunkel (Y/n): n
Collect from zer0k-ise2 (Y/n): n
Collect from zer0k-ise1 (Y/n): n
Collecting a 'show tech' from ise-maibock
Connected to ise-maibock - collecting 'show tech' this may take a while...
ise-maibock - Got 1880 bytes
ise-maibock - Got 3182 bytes
ise-maibock - Got 4625 bytes
ise-maibock - Got 8494 bytes
ise-maibock - Got 8574 bytes
ise-maibock - Got 9749 bytes
ise-maibock - Got 213405 bytes
ise-maibock - Got 251129 bytes
ise-maibock - Got 320025 bytes
ise-maibock - Got 448533 bytes
ise-maibock - Got 562123 bytes
ise-maibock - Got 601399 bytes
ise-maibock - Got 601932 bytes
ise-maibock - Got 668673 bytes
ise-maibock - Got 679471 bytes
ise-maibock - Got 733802 bytes
ise-maibock - Got 837632 bytes
ise-maibock - Got 859386 bytes
ise-maibock - Got 865127 bytes
ise-maibock - Got 1071967 bytes
ise-maibock - Got 1254716 bytes
ise-maibock - Got 1425306 bytes
ise-maibock - Got 1575300 bytes
ise-maibock - Got 1714961 bytes
ise-maibock - Got 1858793 bytes
ise-maibock - Got 2009283 bytes
Successfully collected 'show tech' from ise-maibock
Uploading ise_show_tech_ise-maibock_20231012002023.txt to CXD
Successfully uploaded ise_show_tech_ise-maibock_20231012002023.txt to CXD
Successfully uploaded 'show tech' from ise-maibock
Repository already exists on ise-maibock
Creating 'Diagnostic Bundle' on ise-maibock and have the node upload to CXD directly.  This will take a while... ~45-90 minutes
2023-10-11T20:20:28.687476 NODE: ise-maibock - backup-logs ise-support-bundle-fr-ise-maibock repository TAC-695214455 public-key
Include Core and Heap dumps? (YES/NO):
2023-10-11T20:20:28.729728 NODE: ise-maibock - no

2023-10-11T20:20:28.850708 NODE: ise-maibock - % Creating log backup with timestamped filename: ise-support-bundle-fr-ise-maibock-pk-231011-2020.tar.gpg

2023-10-11T20:20:29.056068 NODE: ise-maibock - % supportbundle in progress: Copying database config files...10% completed

2023-10-11T20:25:51.952476 NODE: ise-maibock - % supportbundle in progress: Copying debug logs...20% completed

2023-10-11T20:27:41.047393 NODE: ise-maibock - Capturing information to file //ttcapture.20231011.2027.log

2023-10-11T20:28:24.956026 NODE: ise-maibock - % supportbundle in progress: Copying local logs...30% completed

2023-10-11T20:28:28.419665 NODE: ise-maibock - % supportbundle in progress: Copying monitor logs...40% completed

2023-10-11T20:28:34.767882 NODE: ise-maibock - % supportbundle in progress: Copying policy xml...50% completed
% supportbundle in progress: Copying system logs...60% completed

2023-10-11T20:40:14.296528 NODE: ise-maibock - % supportbundle in progress: Moving support bundle to the repository...75% completed

➜  ~
```
