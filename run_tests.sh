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

echo -e "\ninvenio run (testing REST):"
#export FLASK_ENV=development
export FLASK_RUN_HOST=127.0.0.1
export FLASK_RUN_PORT=5000
export INVENIO_SERVER_NAME=127.0.0.1:5000
export INVENIO_SEARCH_ELASTIC_HOSTS=127.0.0.1:9200
export INVENIO_JSONSCHEMAS_HOST=repozitar.cesnet.cz
export JSONSCHEMAS_HOST=repozitar.cesnet.cz
export APP_ALLOWED_HOSTS=127.0.0.1:5000
sed -i '/^RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY/ s/deny_all/allow_all/; /^RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY/ s/deny_all/allow_all/; /^RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY/ s/deny_all/allow_all/' /home/travis/virtualenv/python3.8.0/lib/python3.8/site-packages/invenio_records_rest/config.py
invenio run --cert ./ssl/test.crt --key ./ssl/test.key > invenio_run.log 2>&1 &
sleep 20
curl -sk -XGET https://127.0.0.1:5000/api/records/?prettyprint=1
sleep 1
curl -sk -H 'Content-Type:application/json' -d '{"title": "Test Record 1"}' -XPOST https://127.0.0.1:5000/api/records/?prettyprint=1
sleep 2
curl -sk -XGET https://127.0.0.1:5000/api/records/?prettyprint=1
sleep 1
curl -sk -H 'Content-Type:application/json' -d '{"title": "Test Record 1 UPDATED","control_number": "1"}' -XPUT https://27.0.0.1:5000/api/records/1?prettyprint=1
sleep 2
curl -sk -XGET https://127.0.0.1:5000/api/records/?prettyprint=1
sleep 1
curl -sk -XDELETE https://127.0.0.1:5000/api/records/1?prettyprint=1
sleep 2
curl -sk -XGET https://127.0.0.1:5000/api/records/?prettyprint=1
sleep 1

cat invenio_run.log

#echo -e "\npip freeze"
#REQFILE="upload/requirements-${REQUIREMENTS}.txt"
#pip freeze > $REQFILE
#grep -F -e invenio= -e invenio-base -e invenio-search -e invenio-db $REQFILE
