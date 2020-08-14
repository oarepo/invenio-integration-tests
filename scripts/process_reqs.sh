#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -e

echo "process_reqs.sh"

#OAREPO_BRANCH="invenio-3.2"
OAREPO_BRANCH="integration-tests"
SETUP_URL="https://raw.githubusercontent.com/oarepo/oarepo/${OAREPO_BRANCH}/setup.py"
REQ_FILE="requirements-py3.8-invenio3.2.txt"

cd upload
mkdir setup

SETUP_PY=$(mktemp "${HOME}/gitrepo.XXXXXX")
trap "rm '${SETUP_PY}'" EXIT

curl -sf "${SETUP_URL}" -o "${SETUP_PY}"

sed -e "s/^\(.*\)$/  '\1',/" ${REQ_FILE} \
 | sed "${SETUP_PY}" \
    -e "/^INVENIO_VERSION = / s/ = '[0-9.]\+'/ = '3.2.0'/" \
    -e "/^install_requires/ r /dev/stdin" \
    > setup/setup.py
echo "Done."
