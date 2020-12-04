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
BRANCH="master"

git clone -q -b "$BRANCH" --depth 10 "$URL" "$DIR"
cp "$REQFILE" $DIR/upload
cd "$DIR"
git add "$REQFILE"
git commit -m "test commit $DATE (build:$GITHUB_RUN_NUMBER)" -m "[skip ci]"
git push origin "$BRANCH"

echo "Done: $?"
