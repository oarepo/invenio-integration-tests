#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -e

echo -e "\ninvenio-integration-tests/run_tests.sh"

echo ".travis-requirements.txt:"
cat .travis-requirements.txt

echo -e "\ninvenio shell, print(version.__version__):"
invenio shell --simple-prompt -c "from invenio import version; print (\"Invenio version:\", version.__version__)"

echo -e "\npsql version:"
psql --version
echo "invenio db init,create:"
invenio db init
invenio db create
# invenio >=3.3 only:
if [ "${REQUIREMENTS}" != "invenio3.2" ] ; then
  echo "user create:"
  invenio users create -a noreply@cesnet.cz --password 112233
fi

echo -e "\nelasticsearch GET:"
curl -sX GET "http://127.0.0.1:9200" || cat /tmp/local-es.log
echo "invenio index init,check,list:"
invenio index init
invenio index check
invenio index list

echo -e "\ninvenio run:"
export FLASK_ENV=development
export FLASK_RUN_HOST=127.0.0.1
export FLASK_RUN_PORT=5000
export INVENIO_SERVER_NAME=127.0.0.1:5000
invenio run --cert ./ssl/test.crt --key ./ssl/test.key 2>&1 > invenio_run.log &

curl -k -XGET https://127.0.0.1:5000/api/records/?prettyprint=1

#echo -e "\npip freeze"
#REQFILE="upload/requirements-${REQUIREMENTS}.txt"
#pip freeze > $REQFILE
#grep -F -e invenio= -e invenio-base -e invenio-search -e invenio-db $REQFILE
