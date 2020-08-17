#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -e

echo "process_reqs.sh"

REQ_FILE="upload/requirements-py3.8-invenio3.2.txt"
SETUP_PY='oarepo/setup.py'

sed -e "s/^\(.*\)$/  '\1',/" ${REQ_FILE} \
 | sed -i '/^install_requires/,/\]/!b;//!d;/^install_requires/r /dev/stdin' ${SETUP_PY}
echo "Done."
