-- Enable PostgreSQL extensions used by the platform.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- pg_trgm supports future fuzzy subject/sender search at the DB layer.
