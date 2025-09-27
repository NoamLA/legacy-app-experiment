-- Legacy Interview App PostgreSQL Schema (Corrected)
-- Updated to match actual implementation and data structures
-- Optimized for Agno session management and current API usage

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- For text search optimization
-- Note: pgvector extension commented out until installed
-- CREATE EXTENSION IF NOT EXISTS "pgvector";  -- For future RAG functionality

-- =============================================================================
-- CORE PROJECT DATA (Updated to match actual implementation)
-- =============================================================================

-- Projects table - Updated to match current API structure
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject_info JSONB NOT NULL,  -- Contains: name, age, relation, background, language
    interview_mode VARCHAR(20) NOT NULL CHECK (interview_mode IN ('self', 'family', 'hybrid')),
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    status VARCHAR(50) NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'seed_questions', 'themes_identified', 'deep_dive', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- New fields to match actual API usage
    themes JSONB DEFAULT '[]',  -- Legacy theme format for backward compatibility
    enhanced_themes JSONB DEFAULT '[]',  -- New enhanced theme format with assignments
    participants JSONB DEFAULT '[]',  -- Project participants with roles and assignments
    admin_id VARCHAR(255),  -- Project administrator ID
    seed_questions JSONB DEFAULT '[]',  -- Cached generated questions
    extra_metadata JSONB DEFAULT '{}'
);

-- Create indexes after table creation
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_subject_info_gin ON projects USING gin(subject_info);
CREATE INDEX idx_projects_admin_id ON projects(admin_id);
CREATE INDEX idx_projects_themes_gin ON projects USING gin(themes);
CREATE INDEX idx_projects_enhanced_themes_gin ON projects USING gin(enhanced_themes);

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
    extra_metadata JSONB DEFAULT '{}'
);

-- Create indexes after table creation
CREATE INDEX idx_responses_project_id ON interview_responses(project_id);
CREATE INDEX idx_responses_timestamp ON interview_responses(timestamp);
CREATE INDEX idx_responses_question_type ON interview_responses(question_type);
CREATE INDEX idx_responses_theme_id ON interview_responses(theme_id);
CREATE INDEX idx_responses_answer_fts ON interview_responses USING gin(to_tsvector('english', answer));
CREATE INDEX idx_responses_metadata_gin ON interview_responses USING gin(extra_metadata);

-- Interview themes - Identified patterns and topics
CREATE TABLE interview_themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    questions JSONB DEFAULT '[]',
    suggested_interviewer VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extra_metadata JSONB DEFAULT '{}'
);

-- Create indexes after table creation
CREATE INDEX idx_themes_project_id ON interview_themes(project_id);
CREATE INDEX idx_themes_name ON interview_themes(name);
CREATE INDEX idx_themes_created_at ON interview_themes(created_at);

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
    
    PRIMARY KEY (session_id)
);

-- Create indexes after table creation
CREATE INDEX idx_sessions_user_id ON agent_sessions(user_id);
CREATE INDEX idx_sessions_agent_id ON agent_sessions(agent_id);
CREATE INDEX idx_sessions_team_id ON agent_sessions(team_id);
CREATE INDEX idx_sessions_session_type ON agent_sessions(session_type);
CREATE INDEX idx_sessions_created_at ON agent_sessions(created_at);
CREATE INDEX idx_sessions_data_gin ON agent_sessions USING gin(session_data);

-- Agent runs - Individual agent executions
CREATE TABLE agent_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    agent_id VARCHAR(255),
    team_id VARCHAR(255),
    run_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes after table creation
CREATE INDEX idx_runs_session_id ON agent_runs(session_id);
CREATE INDEX idx_runs_agent_id ON agent_runs(agent_id);
CREATE INDEX idx_runs_team_id ON agent_runs(team_id);
CREATE INDEX idx_runs_created_at ON agent_runs(created_at);

-- Messages - Conversation messages for agents
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    run_id UUID REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'function', 'tool')),
    content TEXT NOT NULL,
    message_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes after table creation
CREATE INDEX idx_messages_session_id ON agent_messages(session_id);
CREATE INDEX idx_messages_run_id ON agent_messages(run_id);
CREATE INDEX idx_messages_role ON agent_messages(role);
CREATE INDEX idx_messages_created_at ON agent_messages(created_at);
CREATE INDEX idx_messages_content_fts ON agent_messages USING gin(to_tsvector('english', content));

-- User memories - Persistent user information
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    memory TEXT NOT NULL,
    memory_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes after table creation
CREATE INDEX idx_memories_user_id ON user_memories(user_id);
CREATE INDEX idx_memories_created_at ON user_memories(created_at);
CREATE INDEX idx_memories_memory_fts ON user_memories USING gin(to_tsvector('english', memory));

-- Session summaries - Conversation summaries
CREATE TABLE session_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    summary_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes after table creation
CREATE INDEX idx_summaries_session_id ON session_summaries(session_id);
CREATE INDEX idx_summaries_created_at ON session_summaries(created_at);

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
    extra_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes after table creation
CREATE INDEX idx_docs_project_id ON knowledge_documents(project_id);
CREATE INDEX idx_docs_source_type ON knowledge_documents(source_type);
CREATE INDEX idx_docs_created_at ON knowledge_documents(created_at);
CREATE INDEX idx_docs_content_fts ON knowledge_documents USING gin(to_tsvector('english', content));

-- Vector embeddings - For RAG semantic search (commented out until pgvector is available)
-- CREATE TABLE document_embeddings (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
--     chunk_index INTEGER NOT NULL DEFAULT 0,
--     content TEXT NOT NULL,
--     embedding vector(1536), -- OpenAI text-embedding-3-small dimensions
--     extra_metadata JSONB DEFAULT '{}',
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- Vector similarity search indexes (commented out until pgvector is available)
-- CREATE INDEX idx_embeddings_document_id ON document_embeddings(document_id);
-- CREATE INDEX idx_embeddings_chunk_index ON document_embeddings(chunk_index);
-- CREATE INDEX idx_embeddings_vector_cosine ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
-- CREATE INDEX idx_embeddings_vector_l2 ON document_embeddings USING ivfflat (embedding vector_l2_ops);

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
-- PERFORMANCE OPTIMIZATIONS
-- =============================================================================

-- Create composite indexes for optimal query performance
CREATE INDEX idx_responses_project_timestamp ON interview_responses(project_id, timestamp DESC);
CREATE INDEX idx_messages_session_created ON agent_messages(session_id, created_at DESC);

-- Set up text search configuration for better multilingual support
CREATE TEXT SEARCH CONFIGURATION legacy_search (COPY = english);

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE projects IS 'Core interview projects with subject information stored as JSONB';
COMMENT ON TABLE interview_responses IS 'Individual Q&A pairs from interviews';
COMMENT ON TABLE interview_themes IS 'Identified themes and patterns from responses';
COMMENT ON TABLE agent_sessions IS 'Agno agent session management';
COMMENT ON TABLE agent_messages IS 'Conversation messages between users and agents';
COMMENT ON TABLE user_memories IS 'Persistent memories about users/subjects';
COMMENT ON TABLE knowledge_documents IS 'Documents for RAG knowledge base';

COMMENT ON COLUMN projects.subject_info IS 'JSON object containing name, age, relation, background, language';
COMMENT ON COLUMN projects.themes IS 'Legacy theme format for backward compatibility';
COMMENT ON COLUMN projects.enhanced_themes IS 'Enhanced theme format with participant assignments';
COMMENT ON COLUMN projects.participants IS 'Project participants with roles and theme assignments';
COMMENT ON COLUMN projects.seed_questions IS 'Cached generated seed questions';

-- Grant permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO legacy_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO legacy_user;
