#!/bin/sh
# Runs once, when the PostgreSQL data volume is first created (docker-entrypoint-initdb.d).
#
# Creates two least-privilege roles (threat T16, ASVS V13.2.2):
#   pramaan_owner  owns the "pramaan" schema; used only by the one-shot migrate container
#   pramaan_app    runtime role for the API and worker: read and write rows, no DDL,
#                  no role or database creation. Phase 20 also revokes UPDATE and DELETE
#                  on the transparency log tables from this role.
# The superuser (POSTGRES_USER) is used only here and is never given to the application.
#
# Passwords are passed as psql variables and quoted by psql (:'name'), never pasted into
# SQL text, so a password cannot change the statement.
set -eu

: "${PRAMAAN_DB_OWNER_PASSWORD:?PRAMAAN_DB_OWNER_PASSWORD is not set}"
: "${PRAMAAN_DB_APP_PASSWORD:?PRAMAAN_DB_APP_PASSWORD is not set}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v owner_pw="$PRAMAAN_DB_OWNER_PASSWORD" -v app_pw="$PRAMAAN_DB_APP_PASSWORD" <<'SQL'
SELECT current_database() AS dbname \gset

CREATE ROLE pramaan_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'owner_pw';
CREATE ROLE pramaan_app   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'app_pw';

REVOKE ALL ON DATABASE :"dbname" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"dbname" TO pramaan_owner, pramaan_app;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA pramaan AUTHORIZATION pramaan_owner;
GRANT USAGE ON SCHEMA pramaan TO pramaan_app;
ALTER DEFAULT PRIVILEGES FOR ROLE pramaan_owner IN SCHEMA pramaan
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pramaan_app;
ALTER DEFAULT PRIVILEGES FOR ROLE pramaan_owner IN SCHEMA pramaan
    GRANT USAGE, SELECT ON SEQUENCES TO pramaan_app;

ALTER ROLE pramaan_owner SET search_path = pramaan;
ALTER ROLE pramaan_app   SET search_path = pramaan;
SQL
