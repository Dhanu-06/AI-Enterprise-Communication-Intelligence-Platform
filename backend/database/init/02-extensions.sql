-- Apply after connecting to comm_intel_db:
--   psql -U comm_intel -d comm_intel_db -f backend/database/init/02-extensions.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
