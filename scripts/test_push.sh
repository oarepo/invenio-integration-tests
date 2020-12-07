#!/bin/bash

set -e

echo "push back"

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
  # if test variant - test the flag:
  if [[ "$REQUIREMENTS" =~ test$ ]]; then
    REQS_NOTEST=$(sed 's/test$//' <<<"$REQUIREMENTS")
    FLG="upload/travis_push-$REQS_NOTEST-$TRAVIS_BUILD_NUMBER.flg"
    # if regular variant finished (flag exists) - update trigger and remove the flag:
    if [[ -f "$FLG" ]]; then
      echo "TRIG $(date '+%y%m%d-%H%M%S%z')" > "$TRIG"
      git add "$TRIG"
      #git rm "$FLG"
      git rm upload/travis_push-$REQS_NOTEST-*.flg
    else
      echo "ERR: notest requirements haven't been finished."
      exit 1
    fi
  # regular variant - leave the flag:
  else
    FLG="upload/travis_push-$REQUIREMENTS-$TRAVIS_BUILD_NUMBER.flg"
    date '+%y%m%d-%H%M%S%z' > "$FLG"
    git add "$FLG"
  fi
fi
git diff-index --quiet HEAD -- || {
  git commit -m "GH action commit $DATE (build:$GITHUB_RUN_NUMBER)" -m "[skip ci]"
  git push origin "$BRANCH"
}

echo "Done: $?"
