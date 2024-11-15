#!/bin/bash

timer=3

until runuser -l postgres -c 'pg_isready' &>/dev/null; do
  echo "Postgres is unavailable - sleeping for $timer seconds"
  sleep $timer
done

if [[ -n $POSTGRES_DB ]]; then
	# Check if database exists, and if not, create it
	result=$(echo "SELECT 1 FROM pg_database WHERE datname = :'db_name'" | psql -U postgres -v db_name="keycloakdb" -XAt)
	if ! [ "$result" = '1' ]; then
		echo "Creating new database $POSTGRES_DB"
		createdb -U postgres "$POSTGRES_DB"
	fi
fi

# Run command passed in args
echo "Database available, starting keycloak"
exec /opt/keycloak/bin/kc.sh start-dev