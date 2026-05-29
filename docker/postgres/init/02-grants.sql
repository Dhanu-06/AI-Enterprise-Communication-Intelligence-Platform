-- Grant privileges to the application database user.
-- Runs after PostgreSQL creates POSTGRES_USER / POSTGRES_DB from env vars.

GRANT ALL PRIVILEGES ON DATABASE comm_intel_db TO comm_intel;
GRANT ALL PRIVILEGES ON SCHEMA public TO comm_intel;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO comm_intel;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO comm_intel;
