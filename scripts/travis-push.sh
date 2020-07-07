#!/bin/bash

DATE=$(date '+%y%m%d-%H%M%S')

git config --global user.name du-cesnet-travis
git config --global user.email noreply@cesnet.cz

git checkout master \
 && git add upload/requirements.txt \
 && git commit -m "travis test 12" -m "($DATE build $TRAVIS_BUILD_NUMBER result $TRAVIS_TEST_RESULT)" -m "[skip ci]" \
 && git remote add authenticated https://du-cesnet-travis:${GH_TOKEN}@github.com/oarepo/invenio-integration-tests.git \
 && git push authenticated master 

