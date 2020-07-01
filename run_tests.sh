#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -e

echo "invenio-integration-tests/run_tests.sh"

echo ".requirements.txt:"
cat .requirements.txt

echo "invenio shell:"
invenio shell --simple-prompt -c "app.config"
