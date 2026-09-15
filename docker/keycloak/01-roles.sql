\set ON_ERROR_STOP on
SELECT format('CREATE ROLE keycloak_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', btrim(pg_read_file('/run/secrets/keycloak_database_password'))) \gexec
CREATE DATABASE keycloak OWNER keycloak_app;
REVOKE ALL ON DATABASE keycloak FROM PUBLIC;
