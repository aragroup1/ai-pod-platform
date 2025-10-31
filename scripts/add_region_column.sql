-- Add region column if geography exists
DO $$ 
BEGIN
    -- If geography column exists, rename it to region
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trends' AND column_name = 'geography'
    ) THEN
        ALTER TABLE trends RENAME COLUMN geography TO region;
    END IF;
    
    -- If neither exists, add region column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trends' AND column_name = 'region'
    ) THEN
        ALTER TABLE trends ADD COLUMN region VARCHAR(10) DEFAULT 'GB';
    END IF;
END $$;
