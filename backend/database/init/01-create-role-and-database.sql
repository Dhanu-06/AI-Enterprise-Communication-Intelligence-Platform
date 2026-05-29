-- Manual PostgreSQL bootstrap (non-Docker).
-- Run as a superuser, e.g.:
--   psql -U postgres -f backend/database/init/01-create-role-and-database.sql

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'comm_intel') THEN
        CREATE ROLE comm_intel WITH LOGIN PASSWORD 'comm_intel_secret';
    END IF;
END
$$;

SELECT 'CREATE DATABASE comm_intel_db OWNER comm_intel'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'comm_intel_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE comm_intel_db TO comm_intel;
