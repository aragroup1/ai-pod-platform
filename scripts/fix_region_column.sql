DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trends' AND column_name = 'geography'
    ) THEN
        ALTER TABLE trends RENAME COLUMN geography TO region;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trends' AND column_name = 'region'
    ) THEN
        ALTER TABLE trends ADD COLUMN region VARCHAR(10) DEFAULT 'GB';
    END IF;
    
    ALTER TABLE trends DROP CONSTRAINT IF EXISTS trends_keyword_region_key;
    ALTER TABLE trends ADD CONSTRAINT trends_keyword_region_key UNIQUE (keyword, region);
END $$;
