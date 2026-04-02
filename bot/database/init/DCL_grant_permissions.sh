#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    create user $BOT_DB_USER with password '$BOT_DB_PASSWORD';
    
    grant usage on schema mart to $BOT_DB_USER;
    grant select, insert, update, delete on all tables in schema mart to $BOT_DB_USER;
    alter default privileges in schema mart grant select, insert, update, delete on tables to $BOT_DB_USER;
    
    grant usage on schema api to $BOT_DB_USER;
    grant execute on all procedures in schema api to $BOT_DB_USER;
    grant execute on all functions in schema api to $BOT_DB_USER;
EOSQL