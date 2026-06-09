-- Use this only if your itineraries table has both columns:
--   trip_name_encrypted
--   tripname_encrypted
-- The app standardizes on trip_name_encrypted.

BEGIN;

-- If trip_name_encrypted was created as BYTEA, convert it to TEXT first.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'itineraries'
      AND column_name = 'trip_name_encrypted'
      AND data_type = 'bytea'
  ) THEN
    ALTER TABLE itineraries
    ALTER COLUMN trip_name_encrypted TYPE TEXT
    USING encode(trip_name_encrypted, 'hex');
  END IF;
END $$;

ALTER TABLE itineraries
ADD COLUMN IF NOT EXISTS trip_name_encrypted TEXT;

-- Copy values from the accidental no-underscore column if it exists.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'itineraries'
      AND column_name = 'tripname_encrypted'
  ) THEN
    UPDATE itineraries
    SET trip_name_encrypted = COALESCE(trip_name_encrypted, tripname_encrypted)
    WHERE tripname_encrypted IS NOT NULL;

    ALTER TABLE itineraries DROP COLUMN tripname_encrypted;
  END IF;
END $$;

COMMIT;