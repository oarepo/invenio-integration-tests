#!/bin/bash

set -e

echo "travis-push.sh"

[[ "$1" == "dryrun" ]] && { echo "dryrun"; exit 0; }

DATE=$(date '+%y%m%d-%H%M%S')

git config --global user.name du-cesnet-travis
git config --global user.email noreply@cesnet.cz

URL="https://du-cesnet-travis:${GH_TOKEN}@github.com/oarepo/invenio-integration-tests.git"
DIR="invenio-integration-tests"

REQFILE="upload/requirements-${REQUIREMENTS}.txt"

git clone -q -b master --depth 10 "$URL" "$DIR" \
 && cp "$REQFILE" $DIR/upload \
 && cd "$DIR" \
 && git add "$REQFILE" \
 && git commit -m "travis commit $DATE (build:$TRAVIS_BUILD_NUMBER result:$TRAVIS_TEST_RESULT)" -m "[skip ci]" \
 && git push origin master 

echo "Done: $?"
