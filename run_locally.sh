#!/bin/bash

# TODO: read environment vars from .github/workflows/main.yml
OAREPO_VERSION=12
export OAREPO_VERSION

APP_RDM_PRODUCTION_VERSION="invenio-app-rdm[opensearch2,s3]>=12.0.0b2.dev1,<13"
APP_RDM_TEST_VERSION="invenio-app-rdm[opensearch2,s3,tests]>=12.0.0b2.dev1,<13"
export APP_RDM_PRODUCTION_VERSION
export APP_RDM_TEST_VERSION


PYTHON="python3.10"
export PYTHON

# END OF TODO

set -e

cd "$(dirname "$0")"

EXCLUDED_STEPS=( "Test opensearch on port" "Test postgres version" )

IFS=$'\n'
STEPS=( $(cat .github/workflows/main.yml | yq -o=j -I=0 '.jobs.start_and_test.steps[]') )

GITHUB_WORKSPACE="$(pwd)/.workspace"
export GITHUB_WORKSPACE

GITHUB_ENV="$GITHUB_WORKSPACE/.github_env"
export GITHUB_ENV

GITHUB_OUTPUT="$GITHUB_WORKSPACE/.github_output"
export GITHUB_OUTPUT

if [ -d "$GITHUB_WORKSPACE" ]; then
  rm -rf "$GITHUB_WORKSPACE"
fi

mkdir "$GITHUB_WORKSPACE"

ls | while read; do
  if [ "$REPLY" != ".workspace" ]; then
    cp -r "$REPLY" "$GITHUB_WORKSPACE"
  fi
done

cd $GITHUB_WORKSPACE

for step in "${STEPS[@]}"; do
  step_name=$(echo "$step" | jq -r '.name')
  step_uses=$(echo "$step" | jq -r '.uses')
  step_with=$(echo "$step" | jq -r '.with')
  step_run=$(echo "$step" | jq -r '.run')
  SKIPPED=""
  for excluded_step in "${EXCLUDED_STEPS[@]}"; do
    if [[ "$step_name" =~ $excluded_step ]]; then
      SKIPPED="true"
    fi
  done
  if [ "$SKIPPED" == "true" ]; then
    echo "skipping step: $step_name"
    continue
  fi
  echo "==========================================="
  echo ""
  echo ""
  echo "Running step: '$step_name'"
  echo ""
  echo ""
  if [ "$step_uses" == "actions/checkout@v4" ] ; then
    if [ "$step_with" != "null" ]; then
      repository=$(echo "$step_with" | jq -r '.repository')
      ref=$(echo "$step_with" | jq -r '.ref' | sed "s/\\\${{ env\\.OAREPO_VERSION }}/${OAREPO_VERSION}/")
      path=$(echo "$step_with" | jq -r '.path')
      echo "cloning repository: '$repository' ref: '$ref' path: '$path'"
      git clone --depth=1 --branch="$ref" https://github.com/"$repository" "$GITHUB_WORKSPACE/$path"
    fi
  fi
  if [ "$step_run" != "null" ] ; then
    echo "----------------------------------------"
    echo "$step_run" | sed 's/^/  > /'
    {
      cd "$GITHUB_WORKSPACE"
      eval "$step_run"
      cd "$GITHUB_WORKSPACE"
    }
    echo "----------------------------------------"
  fi
done