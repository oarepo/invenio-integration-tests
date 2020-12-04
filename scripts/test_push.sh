#!/bin/bash

set -e

echo "test-push.sh"
echo "GITHUB_RUN_NUMBER: $GITHUB_RUN_NUMBER"

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
echo $DATE > upload/test.txt
git add upload/test.txt
git commit -m "travis commit $DATE (build:$GITHUB_RUN_NUMBER)" -m "[skip ci]"
git push origin master

echo "Done: $?"
