-- Runs only for a new, empty database volume under the image's initialization user.
-- Password values are read inside PostgreSQL, not expanded into shell commands.
\set ON_ERROR_STOP on
\getenv database_name LIBERTY_DB
SELECT format('CREATE ROLE liberty_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', btrim(pg_read_file('/run/secrets/postgres_app_password'))) \gexec
SELECT format('CREATE ROLE liberty_metrics LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', btrim(pg_read_file('/run/secrets/postgres_metrics_password'))) \gexec
GRANT pg_monitor TO liberty_metrics;
CREATE DATABASE :"database_name" OWNER liberty_app;
REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"database_name" TO liberty_metrics;
