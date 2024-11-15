#!/bin/bash

if [[ ! -d "/var/db" ]]; then
	mkdir -p /var/db
fi

if [[ -z "$(ls -A /var/db)" ]]; then
	echo "Initializing database at $PGDATA"
	chown -R postgres:postgres /var/db
	su postgres -c /usr/lib/postgres/16/bin/initdb
fi

# Run command passed in args
$@