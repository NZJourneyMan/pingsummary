#!/bin/bash

set -e

REPO="https://github.com/NZJourneyMan/pingsummary.git"

USEPYTHON=""
progname=$(basename $0)
DEFAULT_INSTALL=/usr/local/pingsummary

usage() {
    echo "$progname: [-h] [install dir]"
    echo
    echo "Install dir defaults to $DEFAULT_INSTALL"
    echo "This script is idempotent, so can be rerun without causing problems"
    echo
}

# Install autostart for Macs
mkMac() {
    if ! id pingsumm &>/dev/null; then
        LastUID=`dscl . -list /Users UniqueID | awk '{print $2}' | sort -n | tail -1`
        let LastUID++
        LastGID=`dscl . -list /Groups UniqueID | awk '{print $2}' | sort -n | tail -1`
        if [ -z "$LastGID" ]; then
            LastGID=$LastUID
        else
            let LastGID++
        fi

        dscl . create /Groups/pingsumm
        dscl . create /Groups/pingsumm gid $LastGID

        dscl . create /Users/pingsumm
        dscl . create /Users/pingsumm RealName "Ping Summary Web user"
        dscl . create /Users/pingsumm UniqueID $LastUID
        dscl . create /Users/pingsumm PrimaryGroupID $LastGID
        dscl . create /Users/pingsumm UserShell /bin/false
        dscl . create /Users/pingsumm NFSHomeDirectory $installDir
    fi
    cp mac/uk.co.omzig.pingsummary.plist /Library/LaunchDaemons/
    cp mac/uk.co.omzig.pingsummary_webapp.plist /Library/LaunchDaemons/
    launchctl load /Library/LaunchDaemons/uk.co.omzig.pingsummary.plist
    launchctl load /Library/LaunchDaemons/uk.co.omzig.pingsummary_webapp.plist
}

# Check python 3 version is 3.6 or up
okPython3() {
    $1 --version 2>/dev/null | egrep "3\.([6789]|1[[:digit:]])" &>/dev/null
}


if [ "$1" = -h -o "$1" == --help ]; then
    usage
    exit
fi

if [ $(id -u) -ne 0 ]; then
    echo -n "Requires root privileges. Shall I run sudo? ([y]es/no): "
    read a
    if [ -z "$a" -o "$a" = y -o "$a" = yes ]; then
        echo "Rerunning with sudo (<Ctrl-C> to quit)"
        exec sudo $0 "$@"
    else
        echo "Quitting"
        exit 1
    fi
fi

if [ "$1" ]; then
    installDir="$1"
else
    installDir=$DEFAULT_INSTALL
fi

echo -n "Install into $installDir? ([y]es/no): "
read a
if ! [ -z "$a" -o "$a" = y -o "$a" = yes ]; then
    echo "Quitting"
    exit
fi

if [ ! -d $installDir ]; then
    mkdir -p $installDir || exit 1
fi

USEPYTHON=""
for py in python3.10 python3.9 python3.8 python3.7 python3.6 python; do
    if okPython3 $py; then
        USEPYTHON=$(which $py)
        break
    fi
done
if [ -z "$USEPYTHON" ]; then
    echo "Please install python 3.6 - 3.10 along with the matching python3.X-venv"
    exit 1
fi


if ! which git &>/dev/null; then
    echo "Please install git"
    exit 1
fi

cd $installDir || exit 1

if [ -d .git ]; then
    echo "git pull $REPO"
    if ! git pull $REPO; then
        echo "WARNING: Could not update $REPO"
    fi
else
    echo "git clone $REPO ."
    if ! git clone $REPO .; then
        echo "Could not clone $REPO"
        exit 1
    fi
fi

if [ ! -d venv ]; then
    echo "$USEPYTHON -m venv venv"
    if ! $USEPYTHON -m venv venv
    then
        echo "VENV installation failed"
        exit 1
    fi
else
    echo "venv already exists, skipping"
fi

source venv/bin/activate

if ! which pip &>/dev/null; then
    echo "Pip is not found. Please install python3.X-venv to match $USEPYTHON"
    exit 1
fi

echo "pip install -r requirements.txt"
if ! pip install -r requirements.txt; then
    echo "Pip installation failed"
    exit 1
fi

echo
echo "#### Environment smoke test: Running \"./startenv ./pingsumm.py -h\""
if ! ./startenv ./pingsumm.py -h; then
    echo "Something is broken with pingsumm.py"
else
    echo "#### Test succeeded"
fi
echo

# Install start up files
case $OSTYPE in
    linux*)
        echo "Soz, linux startup support not implemented yet"
        ;;
    darwin*)
        mkMac
        ;;
    *)
        echo "Soz, I don't know this OS: $OSTYPE"
        ;;
esac
