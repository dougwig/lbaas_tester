#!/bin/sh

if [ -z "$OS_USERNAME" ]; then
  echo "ERROR: missing OS_USERNAME env variable; must define openstack creds"
  exit 1
fi

python test_lbaas.py $*
