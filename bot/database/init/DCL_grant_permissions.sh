#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    do \$\$
    begin
        if not exists (select from pg_catalog.pg_user where usename = '$BOT_DB_USER') then
            create user $BOT_DB_USER with password '$BOT_DB_PASSWORD';
        end if;
    end
    \$\$;

    grant usage on schema api to $BOT_DB_USER;
    grant select on all tables in schema api to $BOT_DB_USER;

    grant execute on all functions in schema api to $BOT_DB_USER;
    grant execute on all procedures in schema api to $BOT_DB_USER;

    alter default privileges in schema api grant select on tables to $BOT_DB_USER;
    alter default privileges in schema api grant execute on functions to $BOT_DB_USER;

    grant usage on schema dwh to $BOT_DB_USER;
    grant select on dwh.d_calendar to $BOT_DB_USER;
    grant select on dwh.d_product to $BOT_DB_USER;
EOSQL