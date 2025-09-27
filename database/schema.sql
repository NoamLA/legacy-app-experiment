-- Legacy Interview App PostgreSQL Schema
-- Optimized for Agno session management and RAG capabilities

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";  -- For future RAG functionality
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- For text search optimization

-- =============================================================================
-- CORE PROJECT DATA
-- =============================================================================

-- Projects table - Core interview projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject_name VARCHAR(255) NOT NULL,
    subject_age INTEGER,
    relation VARCHAR(100) NOT NULL,
    background TEXT,
    interview_mode VARCHAR(20) NOT NULL CHECK (interview_mode IN ('self', 'family', 'hybrid')),
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    status VARCHAR(50) NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'seed_questions', 'themes_identified', 'deep_dive', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for fast retrieval
    INDEX idx_projects_status (status),
    INDEX idx_projects_created_at (created_at),
    INDEX idx_projects_subject_name (subject_name),
    INDEX idx_projects_metadata_gin (metadata USING gin)
);

-- Interview responses - Core conversation data
CREATE TABLE interview_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL DEFAULT 'seed' CHECK (question_type IN ('seed', 'followup', 'theme')),
    theme_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    followup_questions JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Indexes for fast retrieval
    INDEX idx_responses_project_id (project_id),
    INDEX idx_responses_timestamp (timestamp),
    INDEX idx_responses_question_type (question_type),
    INDEX idx_responses_theme_id (theme_id),
    INDEX idx_responses_answer_fts (answer USING gin(to_tsvector('english', answer))), -- Full-text search
    INDEX idx_responses_metadata_gin (metadata USING gin)
);

-- Interview themes - Identified patterns and topics
CREATE TABLE interview_themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    questions JSONB DEFAULT '[]',
    suggested_interviewer VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_themes_project_id (project_id),
    INDEX idx_themes_name (name),
    INDEX idx_themes_created_at (created_at)
);

-- =============================================================================
-- AGNO SESSION MANAGEMENT (Compatible with Agno's PostgresDb)
-- =============================================================================

-- Agent sessions - Agno's session management
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    agent_id VARCHAR(255),
    team_id VARCHAR(255),
    session_type VARCHAR(50) NOT NULL DEFAULT 'agent',
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (session_id),
    
    -- Indexes for Agno compatibility and fast retrieval
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_agent_id (agent_id),
    INDEX idx_sessions_team_id (team_id),
    INDEX idx_sessions_session_type (session_type),
    INDEX idx_sessions_created_at (created_at),
    INDEX idx_sessions_data_gin (session_data USING gin)
);

-- Agent runs - Individual agent executions
CREATE TABLE agent_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    agent_id VARCHAR(255),
    team_id VARCHAR(255),
    run_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_runs_session_id (session_id),
    INDEX idx_runs_agent_id (agent_id),
    INDEX idx_runs_team_id (team_id),
    INDEX idx_runs_created_at (created_at)
);

-- Messages - Conversation messages for agents
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    run_id UUID REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'function', 'tool')),
    content TEXT NOT NULL,
    message_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for fast message retrieval
    INDEX idx_messages_session_id (session_id),
    INDEX idx_messages_run_id (run_id),
    INDEX idx_messages_role (role),
    INDEX idx_messages_created_at (created_at),
    INDEX idx_messages_content_fts (content USING gin(to_tsvector('english', content)))
);

-- User memories - Persistent user information
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    memory TEXT NOT NULL,
    memory_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_memories_user_id (user_id),
    INDEX idx_memories_created_at (created_at),
    INDEX idx_memories_memory_fts (memory USING gin(to_tsvector('english', memory)))
);

-- Session summaries - Conversation summaries
CREATE TABLE session_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    summary_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_summaries_session_id (session_id),
    INDEX idx_summaries_created_at (created_at)
);

-- =============================================================================
-- RAG AND VECTOR STORAGE (Future-ready for embeddings)
-- =============================================================================

-- Knowledge documents - RAG document storage
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500),
    content TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'interview' CHECK (source_type IN ('interview', 'document', 'audio', 'transcript')),
    source_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_docs_project_id (project_id),
    INDEX idx_docs_source_type (source_type),
    INDEX idx_docs_created_at (created_at),
    INDEX idx_docs_content_fts (content USING gin(to_tsvector('english', content)))
);

-- Vector embeddings - For RAG semantic search
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimensions
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for vector similarity search
    INDEX idx_embeddings_document_id (document_id),
    INDEX idx_embeddings_chunk_index (chunk_index),
    INDEX idx_embeddings_vector_cosine (embedding vector_cosine_ops), -- Cosine similarity
    INDEX idx_embeddings_vector_l2 (embedding vector_l2_ops)          -- L2 distance
);

-- =============================================================================
-- PERFORMANCE AND MAINTENANCE
-- =============================================================================

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_sessions_updated_at BEFORE UPDATE ON agent_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_memories_updated_at BEFORE UPDATE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_summaries_updated_at BEFORE UPDATE ON session_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Complete project view with response counts
CREATE VIEW project_overview AS
SELECT 
    p.*,
    COUNT(ir.id) as response_count,
    COUNT(DISTINCT it.id) as theme_count,
    MAX(ir.timestamp) as last_response_at
FROM projects p
LEFT JOIN interview_responses ir ON p.id = ir.project_id
LEFT JOIN interview_themes it ON p.id = it.project_id
GROUP BY p.id;

-- Recent conversation view for agents
CREATE VIEW recent_conversations AS
SELECT 
    am.session_id,
    am.role,
    am.content,
    am.created_at,
    ROW_NUMBER() OVER (PARTITION BY am.session_id ORDER BY am.created_at DESC) as message_rank
FROM agent_messages am
WHERE am.created_at > NOW() - INTERVAL '7 days'
ORDER BY am.session_id, am.created_at DESC;

-- =============================================================================
-- INITIAL DATA AND CONFIGURATION
-- =============================================================================

-- Create indexes for optimal query performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_project_timestamp 
ON interview_responses(project_id, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_session_created 
ON agent_messages(session_id, created_at DESC);

-- Set up text search configuration for better multilingual support
CREATE TEXT SEARCH CONFIGURATION legacy_search (COPY = english);

-- Comments for documentation
COMMENT ON TABLE projects IS 'Core interview projects with subject information';
COMMENT ON TABLE interview_responses IS 'Individual Q&A pairs from interviews';
COMMENT ON TABLE interview_themes IS 'Identified themes and patterns from responses';
COMMENT ON TABLE agent_sessions IS 'Agno agent session management';
COMMENT ON TABLE agent_messages IS 'Conversation messages between users and agents';
COMMENT ON TABLE user_memories IS 'Persistent memories about users/subjects';
COMMENT ON TABLE knowledge_documents IS 'Documents for RAG knowledge base';
COMMENT ON TABLE document_embeddings IS 'Vector embeddings for semantic search';

-- Grant permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO legacy_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO legacy_app;
