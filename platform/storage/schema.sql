-- platform/storage/schema.sql

-- 1. Definisi Tipe Status yang ketat
CREATE TYPE finding_status AS ENUM (
    'new', 'triaged', 'needs_review', 'confirmed', 
    'false_positive', 'fixed', 'accepted_risk'
);

-- 2. Tabel Targets (Metadata Repositori/API)
CREATE TABLE targets (
    id UUID PRIMARY KEY,
    repository_url VARCHAR(255),
    commit_hash VARCHAR(40),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabel Scans (Melacak setiap eksekusi alat)
CREATE TABLE scans (
    id UUID PRIMARY KEY,
    target_id UUID REFERENCES targets(id) ON DELETE CASCADE,
    scanner_name VARCHAR(100) NOT NULL,
    scanned_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- 4. Tabel Findings (Sangat ramping, tanpa raw_output)
CREATE TABLE findings (
    fingerprint VARCHAR(64) PRIMARY KEY, -- SHA256 Hash
    scan_id UUID REFERENCES scans(id),
    target_id UUID REFERENCES targets(id),
    title VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status finding_status DEFAULT 'new',
    artifact_id VARCHAR(255), -- Path referensi ke MinIO: "artifacts/{scan_id}/{fingerprint}.json"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Tabel Audit Logs (History Tracking)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint VARCHAR(64) REFERENCES findings(fingerprint) ON DELETE CASCADE,
    previous_status finding_status,
    new_status finding_status NOT NULL,
    changed_by VARCHAR(100) NOT NULL, -- 'worker', 'ai-agent', atau UUID analis manusia
    notes TEXT,
    correlation_id UUID, -- Untuk tracing dari Ingestor Gateway
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
