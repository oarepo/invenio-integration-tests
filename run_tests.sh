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

echo "DB init, create:"
invenio db init
invenio db create
echo "user create:"
invenio users create -a noreply@cesnet.cz --password 112233
echo "user test:"
invenio shell -c 'from invenio_accounts.models import User; User.query.all()'
invenio shell -c 'from invenio_accounts.models import User; User.query.all()[0].email'

echo "pip freeze"
pip freeze > upload/requirements-py${TRAVIS_PYTHON_VERSION}-${REQUIREMENTS}.txt
grep -F -e invenio= -e invenio-base upload/requirements-py${TRAVIS_PYTHON_VERSION}-${REQUIREMENTS}.txt
