#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -e

echo "generate_setup.sh"

INVENIO_VERSION_LBL=$1

REQ_FILE="upload/requirements-${INVENIO_VERSION_LBL}.txt"
REQ_FILE_TEST="upload/requirements-${INVENIO_VERSION_LBL}test.txt"
SETUP_PY='oarepo/setup.py'
VERSION_PY='oarepo/oarepo/version.py'
TAG_TXT='oarepo/oarepo/tag.txt'

test -s "$REQ_FILE" || { echo "ERR: REQ_FILE not exists or empty"; exit 1; }

python -m pip install --upgrade pip
pip install bump

# 1st two digits of fixed invenio version from the requirements file:
INVENIO_VERSION=$(sed -n '/^invenio==/ {s/^invenio==\([0-9]\+\.[0-9]\+\)\(\.[0-9]\+\)\?$/\1/; p;}' "$REQ_FILE")
# 1st two digits of previous version from version.py:
PREV_INVENIO_VERSION=$(sed -n '/^__version__ / {s/^[^"\x27]\+["\x27]\([0-9]\+\.[0-9]\)\(\.[0-9]\+\)*["\x27]$/\1/;p}' "$VERSION_PY")

# if there is new invenio version, update 1st two numbers accordingly:
if [[ "$PREV_INVENIO_VERSION" != "$INVENIO_VERSION" ]]; then
  sed -i "/^__version__ / {s/[\"'][0-9.]\+[\"']/\"$INVENIO_VERSION\"/}" "$VERSION_PY"
fi
# bump version.py (ignore 4th number) + catch new value:
NEWTAG=$(sed -n '/^__version__ / {s/\.[0-9]"/"/;p}' "$VERSION_PY" | bump - /dev/null)

echo "PREV_INVENIO_VERSION:$PREV_INVENIO_VERSION INVENIO_VERSION:$INVENIO_VERSION NEWTAG:$NEWTAG"
echo "$NEWTAG" > "$TAG_TXT"

# modify version.py:
sed -i "/^__version__ / {s/\"[0-9.]\+\"/\"$NEWTAG\"/}" "$VERSION_PY"

# modify setup.py:
sed -e "s/^\(.*\)\$/    '\1',/" ${REQ_FILE} \
 | sed -i '/^install_requires/,/^\]/!b;//!d;/^install_requires/r /dev/stdin' ${SETUP_PY}
sed -e '/pytest-invenio/ s/^pytest-invenio==\([0-9\.]\+\)$/pytest-invenio[docs]==\1/' -e "s/^\(.*\)\$/        '\1',/" ${REQ_FILE_TEST} \
 | sed -i '/^extras_require/,/^\]/!b;/^    \x27tests\x27: \[/,/^    \]/!b;//!d;r /dev/stdin' ${SETUP_PY}

echo "Done."
