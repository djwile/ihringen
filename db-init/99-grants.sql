GRANT CONNECT ON DATABASE ihringen TO ihringen;
GRANT USAGE ON SCHEMA ihringen TO ihringen;
GRANT ALL ON ALL TABLES IN SCHEMA ihringen TO ihringen;
GRANT CONNECT ON DATABASE ihringen TO ihringen_appuser;
GRANT USAGE ON SCHEMA ihringen TO ihringen_appuser;
GRANT SELECT ON ALL TABLES IN SCHEMA ihringen TO ihringen_appuser;

ALTER DEFAULT PRIVILEGES IN SCHEMA ihringen
GRANT SELECT ON TABLES TO ihringen_appuser;
