#!/bin/bash


usage() {
    echo "Usage: $(basename $0): [-h]"
}

if [ "$1" = -h ]; then
    usage
    exit 0
fi


ROOTDIR=$(dirname $0)

cd $ROOTDIR || exit 1

gunicorn \
    --reload \
    --bind 0.0.0.0:2233 \
    --access-logfile - \
    --log-file - \
    pingsumm_webapp:app
