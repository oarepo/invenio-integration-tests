#!/bin/bash

set -e

echo "push results back"

DATE=$(date '+%y%m%d-%H%M%S%z')

git config --global user.name oarepo-bot
git config --global user.email noreply@cesnet.cz

URL="https://oarepo-bot:${OAR_BOT}@github.com/oarepo/invenio-integration-tests.git"
DIR="invenio-integration-tests"
REQFILE="upload/requirements-${REQUIREMENTS}.txt"
TRIG="upload/p2oarepo_action.trigger"
BRANCH="master"

git clone -q -b "$BRANCH" --depth 10 "$URL" "$DIR"
cp "$REQFILE" $DIR/upload
cd "$DIR"
git add "$REQFILE"
# only if not devel variant:
if [[ ! "$REQUIREMENTS" =~ ^devel ]]; then
  # if test variant => both variants finished => fire trigger:
  if [[ "$REQUIREMENTS" =~ test$ ]]; then
    echo "TRIG $(date '+%y%m%d-%H%M%S%z')" > "$TRIG"
    git add "$TRIG"
  fi
fi
git diff-index --quiet HEAD -- || {
  git commit -m "GH action commit $DATE (build:$GITHUB_RUN_NUMBER)" -m "[skip ci]"
  git push origin "$BRANCH"
}

echo "Done: $?"
