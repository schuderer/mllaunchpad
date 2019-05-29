#!/bin/bash

echo
echo "Server will be started."
echo "Test URL with HTTPS and Basic Auth (user: muleuser, pw: thepassword):"
echo "https://localhost:8080/iris/v0?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1"
echo

ORIGPATH=$PWD
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

cd "$SCRIPTPATH/.."
if gunicorn --workers 2 --bind 127.0.0.1:5000 launchpad.wsgi & #>>"$SCRIPTPATH/launchpad.log" 2>&1 &
then
  SERVERPID=$!
  echo Started launchpad gunicorn server in backgroud, pid $SERVERPID
else
  echo Failed starting launchpad gunicorn server. Aborting.
  exit 1
fi

mkdir -p "$SCRIPTPATH/temp"

nginx -c "$SCRIPTPATH/nginx.conf" -p "$SCRIPTPATH"

echo Stopping gunicorn...
kill $SERVERPID

cd "$ORIGPATH"
