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
VER=$(invenio shell --simple-prompt -c "from invenio import __version__; __version__")
echo "invenio version: $VER"

echo "pip freeze"
pip freeze > upload/requirements-py${TRAVIS_PYTHON_VERSION}-${REQUIREMENTS}.txt
