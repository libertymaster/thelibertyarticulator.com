\set ON_ERROR_STOP on

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'app_user') \gexec
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_password') \gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'fusionauth_user', :'fusionauth_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'fusionauth_user') \gexec
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'fusionauth_user', :'fusionauth_password') \gexec

SELECT format('CREATE DATABASE %I OWNER %I ENCODING %L TEMPLATE template0', :'app_database', :'app_user', 'UTF8')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'app_database') \gexec

SELECT format('CREATE DATABASE %I OWNER %I ENCODING %L TEMPLATE template0', :'fusionauth_database', :'fusionauth_user', 'UTF8')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'fusionauth_database') \gexec

SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'app_database') \gexec
SELECT format('GRANT CONNECT, TEMPORARY ON DATABASE %I TO %I', :'app_database', :'app_user') \gexec
SELECT format('REVOKE CONNECT ON DATABASE %I FROM PUBLIC', :'fusionauth_database') \gexec
SELECT format('GRANT CONNECT, TEMPORARY ON DATABASE %I TO %I', :'fusionauth_database', :'fusionauth_user') \gexec

\connect :"app_database"
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

