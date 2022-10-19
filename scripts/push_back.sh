#!/bin/bash

set -e

echo "push results back"

DATE=$(date '+%y%m%d-%H%M%S%z')

git config --global user.name oarepo-bot
git config --global user.email noreply@cesnet.cz

URL="https://oarepo-bot:${TOK}@github.com/oarepo/invenio-integration-tests.git"
DIR="invenio-integration-tests"
REQFILE="upload/requirements-${REQUIREMENTS}.txt"
TRIG="upload/p2oarepo_action.trigger"
BRANCH="rdm-10"

git clone -q -b "$BRANCH" --depth 10 "$URL" "$DIR"
cp "$REQFILE" $DIR/upload
cd "$DIR"
git add "$REQFILE"
# only for non-devel variant:
if [[ ! "$REQUIREMENTS" =~ ^devel ]]; then
  # if regular non-test variant:
  if [[ ! "$REQUIREMENTS" =~ test$ ]]; then
    # something to commit => save the flag:
    if ! git diff-index --quiet HEAD -- ; then
      FLG="upload/p2oarepo_action-${REQUIREMENTS}-$GITHUB_RUN_NUMBER.flg"
      echo "FLG $(date '+%y%m%d-%H%M%S%z')" > "$FLG"
      git add "$FLG"
    fi
  # test variant:
  else
    REQS_NOTEST=$(sed 's/-test$//' <<<"$REQUIREMENTS")
    FLG="upload/p2oarepo_action-${REQS_NOTEST}-$GITHUB_RUN_NUMBER.flg"
    # if something to commit or flag from non-test variant exists:
    if ! git diff-index --quiet HEAD -- || [[ -f "$FLG" ]]; then
      # remove the flag
      [[ -f "$FLG" ]] && git rm "$FLG"
      # save the trigger
      echo "TRIG $(date '+%y%m%d-%H%M%S%z')" > "$TRIG"
      git add "$TRIG"
    fi
  fi
fi
# if something to commit:
if ! git diff-index --quiet HEAD -- ; then
  git commit -m "GH action commit $DATE (build:$GITHUB_RUN_NUMBER)"
  git push origin "$BRANCH"
fi

echo "Done: $?"
