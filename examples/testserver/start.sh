#!/bin/bash

echo
echo "Server will be started."
echo "Config used: '$LAUNCHPAD_CFG'"
echo "Test URLs with HTTPS and Basic Auth (user: muleuser, pw: thepassword):"
echo "https://localhost:8080/add/v0/sum?x1=3&x2=2"
echo "https://localhost:8080/iris/v0/varieties?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1"
echo

ORIGPATH=$PWD
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

cd "$SCRIPTPATH/.."
if gunicorn --workers 2 --bind 127.0.0.1:5000 mllaunchpad.wsgi >>"$SCRIPTPATH/mllaunchpad.log" 2>&1 &
then
  SERVERPID=$!
  echo Started mllaunchpad gunicorn server in backgroud, pid $SERVERPID
else
  echo Failed starting mllaunchpad gunicorn server. Aborting.
  exit 1
fi

mkdir -p "$SCRIPTPATH/temp"

# Option -E (preserve environment variables) is considered unsafe.
# This is just for test purposes.
sudo -E nginx -c "$SCRIPTPATH/nginx.conf" -p "$SCRIPTPATH"

echo Stopping gunicorn...
kill $SERVERPID

cd "$ORIGPATH"
