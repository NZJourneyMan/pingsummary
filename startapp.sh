#!/bin/bash

ROOTDIR=$(dirname $0)

gunicorn \
    --reload \
    --reload-extra-file $ROOTDIR/static/scripts/ping_summary.js \
    --reload-extra-file $ROOTDIR/templates/ping_summary.html \
    --bind 0.0.0.0:2233 \
    --access-logfile - \
    --log-file - \
    pingsumm_webapp:app
