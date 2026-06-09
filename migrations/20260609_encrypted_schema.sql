-- Bounce / TravelGenie encrypted-column migration for Neon PostgreSQL.
-- Run this in Neon SQL Editor before or during the deployment that includes the updated server.py.
-- This migration is intentionally non-destructive: it adds the encrypted/protected columns first.

BEGIN;

-- 1) Users table: keep google_user_id as the main Google OAuth identity.
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_user_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_encrypted TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at INTEGER;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_user_id
ON users (google_user_id)
WHERE google_user_id IS NOT NULL;

-- Optional temporary compatibility column.
-- Use this only if you still have old users that have email but no google_user_id.
-- After those users log in once and google_user_id is populated, you can drop users.email.
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;

-- 2) Itineraries table: encrypted/protected display columns plus full JSON payload.
CREATE TABLE IF NOT EXISTS itineraries (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    trip_name_encrypted TEXT,
    destination_encrypted TEXT,
    currency TEXT,
    budget REAL,
    days INTEGER,
    travelers INTEGER,
    itinerary_json TEXT,
    created_at INTEGER,
    updated_at INTEGER
);

ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS trip_name_encrypted TEXT;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS destination_encrypted TEXT;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS currency TEXT;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS budget REAL;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS days INTEGER;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS travelers INTEGER;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS itinerary_json TEXT;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS created_at INTEGER;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS updated_at INTEGER;

CREATE INDEX IF NOT EXISTS idx_itineraries_user_id
ON itineraries (user_id);

COMMIT;

-- After the updated app has run successfully and all users can log in, you may remove old plaintext columns.
-- Only run these after you confirm the app no longer needs them:
-- ALTER TABLE users DROP COLUMN IF EXISTS email;
-- ALTER TABLE itineraries DROP COLUMN IF EXISTS trip_name;
-- ALTER TABLE itineraries DROP COLUMN IF EXISTS destination;