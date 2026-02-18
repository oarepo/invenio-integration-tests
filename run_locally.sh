#!/usr/bin/env bash

set -e
set -o pipefail
set -u

cd "$(dirname "$0")"

# if [ -d .venv ]; then
#     rm -rf .venv
# fi
# uv venv --python=3.14
# source .venv/bin/activate
# uv pip install -e .

invenio-integration-tests setup invenio-forks.yaml test.json
# create --patch arguments from test.json

patches=()
while IFS= read -r patch; do
  patches+=(--patch "$patch")
done < <(jq -r '.patches[]' test.json)


invenio-testrig setup --verbose  --repository oarepo/inveniordm-reference-repo \
  --patch-mode pinned-rebase "${patches[@]}" 