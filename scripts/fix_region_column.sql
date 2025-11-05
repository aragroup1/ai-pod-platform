DO $$ 
BEGIN
    -- Rename geography to region if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trends' AND column_name = 'geography'
    ) THEN
        ALTER TABLE trends RENAME COLUMN geography TO region;
    END IF;
    
    -- Add region column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trends' AND column_name = 'region'
    ) THEN
        ALTER TABLE trends ADD COLUMN region VARCHAR(10) DEFAULT 'GB';
    END IF;
    
    -- Remove duplicates before adding constraint
    DELETE FROM trends a USING trends b
    WHERE a.id < b.id 
    AND a.keyword = b.keyword 
    AND a.region = b.region;
    
    -- Drop old constraint if exists
    ALTER TABLE trends DROP CONSTRAINT IF EXISTS trends_keyword_region_key;
    
    -- Add new unique constraint
    ALTER TABLE trends ADD CONSTRAINT trends_keyword_region_key UNIQUE (keyword, region);
END $$;
