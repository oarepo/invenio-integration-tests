#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -e

echo "invenio-integration-tests/run_tests.sh"

echo ".travis-requirements.txt:"
cat .travis-requirements.txt

echo "invenio shell:"
invenio shell --simple-prompt -c "app.config"

echo "psql version:"
psql --version
echo "DB init, create:"
invenio db init
invenio db create
# invenio >=3.3 only:
# echo "user create:"
# invenio users create -a noreply@cesnet.cz --password 112233

echo "es version:"
/tmp/elasticsearch/bin/elasticsearch --version
echo "es:"
curl -sX GET "http://127.0.0.1:9200" || cat /tmp/local-es.log

echo "pip freeze"
REQFILE="upload/requirements-py${TRAVIS_PYTHON_VERSION}-${REQUIREMENTS}.txt"
pip freeze > $REQFILE
grep -F -e invenio= -e invenio-base $REQFILE
