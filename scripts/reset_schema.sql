-- This script completely wipes and resets the public schema.
-- It's safe for development but DANGEROUS for production.
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
