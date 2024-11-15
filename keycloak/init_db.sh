#!/bin/bash

if [[ -z "$(ls -A /var/db)" ]]; then
	echo "Initializing database at $PGDATA"
	su postgres -c /usr/lib/postgres/16/bin/initdb
fi

# Run command passed in args
$@