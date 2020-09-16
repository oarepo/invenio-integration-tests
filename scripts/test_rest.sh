#!/bin/bash

set -e

err() { printf "$0[error]: %s\n" "$*" >&2; exit 2; }

REST_URL="https://${INVENIO_SERVER_NAME}/api/records"

echo "list records:"
RESULT=$(curl -sk -XGET "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq '.hits.total')
[[ "$VAL" == "0" ]] || err "unexpected records (total:\"$VAL\"/0)"
echo "OK total: $VAL"
sleep 1

echo "ADD (POST) new record:"
RESULT=$(curl -sk -H 'Content-Type:application/json' -d '{"title": "Test Record 1"}' -XPOST "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.id')
[[ "$VAL" == "null" ]] && err "wrong id (\"$VAL\"/0)"
ID1="$VAL"
CN1=$(echo "$RESULT" | jq -r '.metadata.control_number')
echo "OK new id: $ID1  control_number: $CN1"
sleep 1
RESULT=$(curl -sk -H 'Content-Type:application/json' -d '{"title": "Test Record 2"}' -XPOST "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.id')
[[ "$VAL" == "null" ]] && err "wrong id (\"$VAL\"/0)"
ID2="$VAL"
CN2=$(echo "$RESULT" | jq -r '.metadata.control_number')
echo "OK new id: $ID2  control_number: $CN2"
sleep 1
echo "list records:"
RESULT=$(curl -sk -XGET "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.hits.total')
[[ "$VAL" == "2" ]] || err "wrong number of records (total:\"$VAL\"/2)"
echo "OK total: $VAL"
sleep 1

echo "UPDATE (PUT) existing record:"
RESULT=$(curl -sk -H 'Content-Type:application/json' -d '{"title": "Test Record 1 UPDATED","control_number": "'"$CN1"'"}' -XPUT "$REST_URL/$ID1"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.id')
[[ "$VAL" == "$ID1" ]] || err "wrong id (\"$VAL\"/$ID1)"
VAL=$(echo "$RESULT" | jq -r '.metadata.title')
[[ "$VAL" == "Test Record 1 UPDATED" ]] || err "wrong title (\"$VAL\"/\"Test Record 1 UPDATED\")"
echo "OK updated, new title: \"$VAL\""
sleep 1
echo "list records:"
RESULT=$(curl -sk -XGET "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.hits.total')
[[ "$VAL" == "2" ]] || err "wrong number of records (total:\"$VAL\"/2)"
echo "OK total: $VAL"
sleep 1
echo "search records:"
RESULT=$(curl -sk -XGET "$REST_URL/?q=updated"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.hits.total')
[[ "$VAL" == "1" ]] || err "wrong number of records (total:\"$VAL\"/1)"
echo "OK total: $VAL"
VAL=$(echo "$RESULT" | jq -r '.hits.hits[]|select(.id == "'"$ID1"'").metadata.title')
[[ "$VAL" == "Test Record 1 UPDATED" ]] || err "wrong title (\"$VAL\"/\"Test Record 1 UPDATED\")"
echo "OK found title: \"$VAL\""
sleep 1

echo "DELETE existing record:"
RESULT=$(curl -sk -XDELETE "$REST_URL/$ID1"); echo "status: $?"
[[ "$RESULT" == "" ]] || err "error (\"$RESULT\"/1)"
echo "OK deleted"
sleep 1
echo "list records:"
RESULT=$(curl -sk -XGET "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.hits.total')
[[ "$VAL" == "1" ]] || err "wrong number of records (total:\"$VAL\"/1)"
echo "OK total: $VAL"
VAL=$(echo "$RESULT" | jq -r '.hits.hits[]|select(.id == "'"$ID2"'").metadata.title')
[[ "$VAL" == "Test Record 2" ]] || err "wrong title (\"$VAL\"/\"Test Record 2\")"
sleep 1

echo "DELETE existing record:"
RESULT=$(curl -sk -XDELETE "$REST_URL/$ID2"); echo "status: $?"
[[ "$RESULT" == "" ]] || err "error (\"$RESULT\"/1)"
echo "OK deleted"
sleep 1
echo "list records:"
RESULT=$(curl -sk -XGET "$REST_URL/"); echo "status: $?"
VAL=$(echo "$RESULT" | jq -r '.hits.total')
[[ "$VAL" == "0" ]] || err "wrong number of records (total:\"$VAL\"/0)"
echo "OK total: $VAL"
sleep 1
