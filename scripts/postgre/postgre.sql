-- Create programs table
CREATE TABLE programs (
    -- Primary key and basic information
    id VARCHAR(50) PRIMARY KEY,
    university VARCHAR(255) NOT NULL,
    program VARCHAR(255) NOT NULL,
    
    -- Academic fields (array type)
    fields TEXT[],
    
    -- Program type and location
    type VARCHAR(50),
    campus VARCHAR(255),
    intakes TEXT[],
    
    -- Tuition information
    tuition_nzd_per_year DECIMAL(10,2),
    
    -- English language requirements
    english_ielts DECIMAL(3,1),
    english_no_band_below DECIMAL(3,1),
    english_toefl_total INTEGER,
    english_toefl_writing INTEGER,
    
    -- Program duration information
    duration_years DECIMAL(3,1),
    level VARCHAR(50),
    
    -- Application requirements (array type)
    academic_reqs TEXT[],
    other_reqs TEXT[],
    
    -- Additional information
    url TEXT,
    source_updated DATE,
    content TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
