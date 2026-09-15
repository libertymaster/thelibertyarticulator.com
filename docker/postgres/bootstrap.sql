\set ON_ERROR_STOP on

DO $bootstrap$
DECLARE
    app_password text;
    metrics_password text;
BEGIN
    app_password := btrim(
        pg_read_file('/run/secrets/postgres_app_password'),
        E' \t\r\n'
    );

    metrics_password := btrim(
        pg_read_file('/run/secrets/postgres_metrics_password'),
        E' \t\r\n'
    );

    IF app_password = '' THEN
        RAISE EXCEPTION 'postgres_app_password is empty';
    END IF;

    IF metrics_password = '' THEN
        RAISE EXCEPTION 'postgres_metrics_password is empty';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'liberty_app'
    ) THEN
        EXECUTE format(
            'CREATE ROLE liberty_app LOGIN INHERIT
             NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
             PASSWORD %L',
            app_password
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE liberty_app LOGIN INHERIT
             NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
             PASSWORD %L',
            app_password
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'liberty_metrics'
    ) THEN
        EXECUTE format(
            'CREATE ROLE liberty_metrics LOGIN INHERIT
             NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
             PASSWORD %L',
            metrics_password
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE liberty_metrics LOGIN INHERIT
             NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
             PASSWORD %L',
            metrics_password
        );
    END IF;
END
$bootstrap$;

SELECT
    'CREATE DATABASE liberty_articulator OWNER liberty_app'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'liberty_articulator'
)
\gexec

DO $verify_database$
DECLARE
    database_owner name;
BEGIN
    SELECT pg_get_userbyid(datdba)
      INTO database_owner
      FROM pg_database
     WHERE datname = 'liberty_articulator';

    IF database_owner IS NULL THEN
        RAISE EXCEPTION 'liberty_articulator database was not created';
    END IF;

    IF database_owner <> 'liberty_app' THEN
        RAISE EXCEPTION
            'Unexpected owner for liberty_articulator: %',
            database_owner;
    END IF;
END
$verify_database$;

REVOKE ALL
ON DATABASE liberty_articulator
FROM PUBLIC;

GRANT CONNECT, TEMPORARY
ON DATABASE liberty_articulator
TO liberty_app;

GRANT CONNECT
ON DATABASE liberty_articulator
TO liberty_metrics;


DO $grant_monitor$
BEGIN
    IF NOT pg_has_role('liberty_metrics', 'pg_monitor', 'MEMBER') THEN
        GRANT pg_monitor TO liberty_metrics;
    END IF;
END
$grant_monitor$;

DO $revoke_monitor$
BEGIN
    IF pg_has_role('liberty_app', 'pg_monitor', 'MEMBER') THEN
        REVOKE pg_monitor FROM liberty_app;
    END IF;
END
$revoke_monitor$;
