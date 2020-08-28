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
SETUP_PY='oarepo/setup.py'
VERSION_PY='oarepo/oarepo/version.py'
TAG_TXT='oarepo/oarepo/tag.txt'

test -s "$REQ_FILE" || { echo "ERR: REQ_FILE not exists or empty"; exit 1; }

pip install bump

# version bump
INVENIO_VERSION=$(sed -n '/^invenio==/ {s/^invenio==//; p;}' "$REQ_FILE")
PREV_INVENIO_VERSION=$(sed -n '/^__version__ / {s/^[^"]\+"\([0-9.]\+\)\.[0-9]"$/\1/;p}' "$VERSION_PY")
if [[ "$PREV_INVENIO_VERSION" == "$INVENIO_VERSION" ]]; then
  # bump utility probably can't use four-number format, temporarily switched to three-number format without major ver.num.:
  MAJOR=$(sed -n '/^__version__ / {s/^[^"]\+"\([0-9]\+\)\..*$/\1/;p}' "$VERSION_PY")
  BUMP_INPUT=$(sed -n '/^__version__ / {s/^[^"]\+"[0-9]\.\([0-9.]\+\)"[^"]*$/\1/;p}' "$VERSION_PY")
  BUMPED=$(sed -n '/^__version__ / {s/"[0-9]\./"/;p}' "$VERSION_PY" | bump - /dev/null)
  # and back with major ver.num.:
  NEWTAG="$MAJOR.$BUMPED"
else
  NEWTAG="$INVENIO_VERSION.0"
fi
echo "PREV_INVENIO_VERSION:$PREV_INVENIO_VERSION INVENIO_VERSION:$INVENIO_VERSION NEWTAG:$NEWTAG"
echo "$NEWTAG" > "$TAG_TXT"

# modify version.py
sed -i "/^__version__ / {s/\"[0-9.]\+\"/\"$NEWTAG\"/}" "$VERSION_PY"

sed -e "s/^\(.*\)$/  '\1',/" ${REQ_FILE} \
 | sed -i '/^install_requires/,/\]/!b;//!d;/^install_requires/r /dev/stdin' ${SETUP_PY}
echo "Done."
