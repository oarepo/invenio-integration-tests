#!/bin/bash

set -e

echo "test-push.sh"

DATE=$(date '+%y%m%d-%H%M%S%z')

git config --global user.name du-cesnet-travis
git config --global user.email noreply@cesnet.cz

URL="https://oarepo-bot:${OAR_BOT}@github.com/oarepo/invenio-integration-tests.git"
DIR="invenio-integration-tests"
REQFILE="upload/requirements-${REQUIREMENTS}.txt"
TRIG="upload/p2oarepo_action.trigger"

git clone -q -b master --depth 10 "$URL" "$DIR"
cp "$REQFILE" $DIR/upload
cd "$DIR"
pwd
ls -l upload
tail -n 20 $REQFILE
