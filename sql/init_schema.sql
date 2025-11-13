-- GraphRAG Progress Tracking Database Schema
-- PostgreSQL 15+
--
-- This schema tracks processing progress for the microservices architecture

-- ============================================================
-- PROJECTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    completed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_projects_name ON projects(project_name);
CREATE INDEX idx_projects_status ON projects(status);

COMMENT ON TABLE projects IS 'Tracks each project and its overall processing status';

-- ============================================================
-- FILES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS files (
    file_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(project_id, file_hash)
);

CREATE INDEX idx_files_project_id ON files(project_id);
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_files_hash ON files(file_hash);
CREATE INDEX idx_files_path ON files(file_path);

COMMENT ON TABLE files IS 'Tracks individual PDF files and their processing status';

-- ============================================================
-- PROCESSING TASKS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS processing_tasks (
    task_id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    worker_id VARCHAR(100),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_tasks_file_id ON processing_tasks(file_id);
CREATE INDEX idx_tasks_status ON processing_tasks(status);
CREATE INDEX idx_tasks_type ON processing_tasks(task_type);
CREATE INDEX idx_tasks_worker ON processing_tasks(worker_id);

COMMENT ON TABLE processing_tasks IS 'Tracks individual processing tasks (extract, vectorize, graph_build, storage)';

-- ============================================================
-- CHUNKS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
    chunk_identifier VARCHAR(255) NOT NULL,
    page_number INTEGER,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(file_id, chunk_identifier)
);

CREATE INDEX idx_chunks_file_id ON chunks(file_id);
CREATE INDEX idx_chunks_identifier ON chunks(chunk_identifier);

COMMENT ON TABLE chunks IS 'Stores extracted text chunks from PDFs';

-- ============================================================
-- EMBEDDINGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    embedding_index INTEGER NOT NULL,
    chromadb_id VARCHAR(500),
    model_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chunk_id)
);

CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_chromadb_id ON embeddings(chromadb_id);

COMMENT ON TABLE embeddings IS 'Tracks which chunks have been vectorized and their ChromaDB IDs';

-- ============================================================
-- KNOWLEDGE GRAPH ENTITIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS kg_entities (
    entity_id SERIAL PRIMARY KEY,
    entity_name VARCHAR(500) NOT NULL,
    project_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    total_mentions INTEGER DEFAULT 1,
    is_cross_project BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(entity_name)
);

CREATE INDEX idx_kg_entities_name ON kg_entities(entity_name);
CREATE INDEX idx_kg_entities_cross_project ON kg_entities(is_cross_project);

COMMENT ON TABLE kg_entities IS 'Stores unique entities extracted from knowledge graphs';

-- ============================================================
-- KNOWLEDGE GRAPH RELATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS kg_relations (
    relation_id SERIAL PRIMARY KEY,
    head_entity_id INTEGER REFERENCES kg_entities(entity_id) ON DELETE CASCADE,
    tail_entity_id INTEGER REFERENCES kg_entities(entity_id) ON DELETE CASCADE,
    relation_type VARCHAR(255) NOT NULL,
    project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
    source_chunk_id INTEGER REFERENCES chunks(chunk_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_kg_relations_head ON kg_relations(head_entity_id);
CREATE INDEX idx_kg_relations_tail ON kg_relations(tail_entity_id);
CREATE INDEX idx_kg_relations_type ON kg_relations(relation_type);
CREATE INDEX idx_kg_relations_project ON kg_relations(project_id);

COMMENT ON TABLE kg_relations IS 'Stores relationships between entities';

-- ============================================================
-- SERVICE HEALTH TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS service_health (
    health_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(service_name)
);

CREATE INDEX idx_service_health_name ON service_health(service_name);
CREATE INDEX idx_service_health_heartbeat ON service_health(last_heartbeat);

COMMENT ON TABLE service_health IS 'Tracks health status of all microservices';

-- ============================================================
-- CIRCUIT BREAKERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS circuit_breakers (
    breaker_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    target_service VARCHAR(100) NOT NULL,
    state VARCHAR(50) DEFAULT 'closed',
    failure_count INTEGER DEFAULT 0,
    last_failure_time TIMESTAMP,
    next_retry_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service_name, target_service)
);

CREATE INDEX idx_circuit_breakers_service ON circuit_breakers(service_name);
CREATE INDEX idx_circuit_breakers_state ON circuit_breakers(state);

COMMENT ON TABLE circuit_breakers IS 'Tracks circuit breaker state for service resilience';

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_files_updated_at
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON processing_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_circuit_breakers_updated_at
    BEFORE UPDATE ON circuit_breakers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- HELPER VIEWS
-- ============================================================

-- Project progress summary view
CREATE OR REPLACE VIEW project_progress AS
SELECT
    p.project_id,
    p.project_name,
    p.status as project_status,
    COUNT(f.file_id) as total_files,
    COUNT(CASE WHEN f.status = 'completed' THEN 1 END) as completed_files,
    COUNT(CASE WHEN f.status = 'failed' THEN 1 END) as failed_files,
    COUNT(CASE WHEN f.status = 'in_progress' THEN 1 END) as in_progress_files,
    COUNT(CASE WHEN f.status = 'pending' THEN 1 END) as pending_files,
    ROUND(
        100.0 * COUNT(CASE WHEN f.status = 'completed' THEN 1 END) / NULLIF(COUNT(f.file_id), 0),
        2
    ) as completion_percentage
FROM projects p
LEFT JOIN files f ON p.project_id = f.project_id
GROUP BY p.project_id, p.project_name, p.status;

COMMENT ON VIEW project_progress IS 'Summary view of project processing progress';

-- Task statistics view
CREATE OR REPLACE VIEW task_statistics AS
SELECT
    task_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    AVG(retry_count) as avg_retries
FROM processing_tasks
WHERE started_at IS NOT NULL
GROUP BY task_type, status;

COMMENT ON VIEW task_statistics IS 'Statistics on task processing performance';

-- Service health summary
CREATE OR REPLACE VIEW service_health_summary AS
SELECT
    service_name,
    status,
    last_heartbeat,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) as seconds_since_heartbeat,
    error_count,
    CASE
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) > 60 THEN 'STALE'
        WHEN status = 'healthy' THEN 'OK'
        ELSE 'WARNING'
    END as health_status
FROM service_health;

COMMENT ON VIEW service_health_summary IS 'Real-time service health with staleness detection';

-- ============================================================
-- SEED DATA (Optional - for development)
-- ============================================================

-- Insert default service health records
INSERT INTO service_health (service_name, status, error_count) VALUES
    ('file-watcher', 'unknown', 0),
    ('orchestrator', 'unknown', 0),
    ('pdf-processor', 'unknown', 0),
    ('vectorization', 'unknown', 0),
    ('graph-construction', 'unknown', 0),
    ('storage', 'unknown', 0),
    ('api', 'unknown', 0)
ON CONFLICT (service_name) DO NOTHING;

-- ============================================================
-- PERMISSIONS (Optional - for production)
-- ============================================================

-- Create read-only user for monitoring/reporting
-- CREATE USER graphrag_readonly WITH PASSWORD 'readonly_pass';
-- GRANT CONNECT ON DATABASE graphrag_progress TO graphrag_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO graphrag_readonly;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO graphrag_readonly;

-- ============================================================
-- HELPFUL QUERIES
-- ============================================================

-- Query examples (commented out, use as reference):

-- Get all projects with progress
-- SELECT * FROM project_progress ORDER BY completion_percentage DESC;

-- Find stalled tasks (in_progress for > 1 hour)
-- SELECT * FROM processing_tasks
-- WHERE status = 'in_progress'
--   AND started_at < CURRENT_TIMESTAMP - INTERVAL '1 hour';

-- Get failed tasks by type
-- SELECT task_type, COUNT(*) as failures
-- FROM processing_tasks
-- WHERE status = 'failed'
-- GROUP BY task_type;

-- Find files needing retry
-- SELECT f.file_path, t.task_type, t.retry_count, t.error_message
-- FROM files f
-- JOIN processing_tasks t ON f.file_id = t.file_id
-- WHERE t.status = 'failed' AND t.retry_count < t.max_retries;

-- Check service health
-- SELECT * FROM service_health_summary;

-- Monitor circuit breakers
-- SELECT * FROM circuit_breakers WHERE state != 'closed';
