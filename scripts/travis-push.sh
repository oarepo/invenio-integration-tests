#!/bin/bash

set -e

echo "travis-push.sh"

[[ "$1" == "dryrun" ]] && { echo "dryrun"; exit 0; }

DATE=$(date '+%y%m%d-%H%M%S')

git config --global user.name du-cesnet-travis
git config --global user.email noreply@cesnet.cz

git checkout -q master \
 && git pull \
 && git add upload/requirements* \
 && git commit -m "travis commit $DATE (build:$TRAVIS_BUILD_NUMBER result:$TRAVIS_TEST_RESULT)" -m "[skip ci]" \
 && git remote add authenticated https://du-cesnet-travis:${GH_TOKEN}@github.com/oarepo/invenio-integration-tests.git > /dev/null 2>&1 \
 && git push authenticated master 
