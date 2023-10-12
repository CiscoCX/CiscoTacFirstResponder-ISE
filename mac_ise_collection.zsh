#!/bin/zsh

cat << EOF
Welcome to the Cisco First Responder installer for MacOS.

This script will download and install a local copy of python3
in your home directory and then install the necessary dependencies
in a virtualenv.

Then it will execute a python script that will connect to ISE and run a collection script.

The script will be installed in ~/.cisco_firstresponder/ and can be easily removed by deleting that directory.
EOF

printf "Do you want to continue (Y/n)? "
read answer

if [ "$answer" != "${answer#[Yy]}" ] ;then 
    echo "Starting...."
else
    exit 0
fi


if test -d ~/.cisco_firstresponder/opt/Python.framework; then
    echo "Python already installed in the ~/.cisco_firstresponder"
    cd ~/.cisco_firstresponder/opt/Python.framework
else
    echo "Fetch python from python.org and install in ~/.cisco_firstresponder/"
    mkdir -p ~/.cisco_firstresponder/opt/Python.framework
    cd ~/.cisco_firstresponder/opt/Python.framework
    curl -L -O https://www.python.org/ftp/python/3.12.0/python-3.12.0-macos11.pkg
    
    # normally you would need to run `sudo installer -pkg <package name> -target /` but we are going to do it manually
    # because we don't want to run a sudo command
    xar -xf python-3.12.0-macos11.pkg
    for i in `find . | grep Payload`; do mv $i $i.gz; gunzip $i.gz; done
    for i in `find . | grep Payload`; do cpio -i < $i ; done
    # Fix the broken symlinks
    file * | grep broken | while read line; do
        # example: `python3:                          broken symbolic link to ../../../Library/Frameworks/Python.framework/Versions/3.12/bin/python3``
        # delete the broken link "python3"
        # extract the path "../../../Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
        # and change it to to "./Versions/3.12/bin/python3"
        # then link that to the current directory        
        FILETODELETE=`echo $line | awk '{ split($1,a,":"); print a[1] }'`
        rm $FILETODELETE
        FILETOLINK=`echo $line | awk '{ gsub(/.*Python.framework/, "."); print }'`
        ln -s $FILETOLINK
    done
fi;

# These environment variables are necessary to get python to run 
# from the directory it is installed in rather than the system directories
export DYLD_FRAMEWORK_PATH=~/.cisco_firstresponder/opt/:$DYLD_FRAMEWORK_PATH
export DYLD_LIBRARY_PATH=~/.cisco_firstresponder/opt/Python.framework/Versions/3.12/lib:$DYLD_LIBRARY_PATH
export PYTHONHOME=~/.cisco_firstresponder/opt/Python.framework/Versions/Current


# Now we need to setup a virtualenv and install any dependencies
cd ~/.cisco_firstresponder/
if test -d ~/.cisco_firstresponder/venv; then
    echo "Virtualenv already exists"
    source ./venv/bin/activate
else
    echo "Create a virtualenv and install dependencies"
    ./opt/Python.framework/python3 -m venv ./venv
    source ./venv/bin/activate
    python3 -m pip install --upgrade pip wheel
    python3 -m pip install --upgrade setuptools
    python3 -m pip install httpx "scrapli[asyncssh]"
fi;

curl https://raw.githubusercontent.com/CiscoCX/CiscoTacFirstResponder-ISE/main/mac_ise_collection.py > ~/.cisco_firstresponder/mac_ise_collection.py
python3 ~/.cisco_firstresponder/mac_ise_collection.py

