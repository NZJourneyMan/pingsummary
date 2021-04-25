#!/bin/bash

progname=$(basename $0)
DEFAULT_INSTALL=/usr/local/pingsummary

usage() {
    echo "$progname: [-h] [install dir]"
    echo
    echo "Removes Ping summary from the system"
    echo
    echo "Install dir defaults to $DEFAULT_INSTALL"
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
    installDir=$DEFAULT_INSTALL
fi

echo -n "Delete $installDir? ([y]es/no): "
read a
if ! [ -z "$a" -o "$a" = y -o "$a" = yes ]; then
    echo "Quitting"
    exit
fi

if [ ! -d $installDir ]; then
    "Error: $installDir doesn't exist. Aborting"
    exit 1
fi

rmMac() {
    launchctl unload /Library/LaunchDaemons/uk.co.omzig.pingsummary.plist
    launchctl unload /Library/LaunchDaemons/uk.co.omzig.pingsummary_webapp.plist
    rm -f /Library/LaunchDaemons/uk.co.omzig.pingsummary.plist
    rm -f /Library/LaunchDaemons/uk.co.omzig.pingsummary_webapp.plist
    dscl . delete /Users/pingsumm
    dscl . delete /Groups/pingsumm
}

# Remove start up files
case $OSTYPE in
    linux*)
        echo "Soz, linux startup support not implemented yet"
        ;;
    darwin*)
        rmMac
        ;;
    *)
        echo "Soz, I don't know this OS: $OSTYPE"
        ;;
esac

echo "Running rm -r $installDir"
rm -r $installDir