#!/bin/bash

set -e

REPO="https://github.com/NZJourneyMan/pingsummary.git"

USEPYTHON=""
progname=$(basename $0)

usage() {
    echo "$progname: [-h] [install dir]"
    echo
    echo "Install dir defaults to /usr/local/pingsumm"
    echo "This script is idempotent, so can be rerun without causing problems"
    echo
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
    installDir="/usr/local/pingsumm"
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

# Find python 3
if ! python --version 2>/dev/null | grep " 3" &>/dev/null; then
    if ! python3 --version 2>/dev/null | grep " 3" &>/dev/null; then
        echo "Please install python 3 to continue"
        exit 1
    else
        USEPYTHON=$(which python3)
    fi
else
    USEPYTHON=$(which python)
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

echo "$USEPYTHON -m venv venv"
if ! $USEPYTHON -m venv venv
then
    echo "VENV installation failed"
    exit 1
fi

source venv/bin/activate

if ! which pip &>/dev/null; then
    echo "Pip is not found, it should have come with the python 3 VENV"
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
        exit 1
        ;;
    darwin*)
        cp mac/pingsummary.plist /Library/LaunchDaemons/
        cp mac/pingsummary_webapp.plist /Library/LaunchDaemons/
        launchctl load /Library/LaunchDaemons/uk.co.omzig.pingsummary.plist
        launchctl load /Library/LaunchDaemons/uk.co.omzig.pingsummary_webapp.plist
        ;;
    *)
        echo "Soz, I don't know this OS: $OSTYPE"
        exit 1
        ;;
esac
