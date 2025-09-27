-- Legacy Interview App Multi-Environment PostgreSQL Schema
-- Supports CI/Test/Production environments with table prefixes
-- Optimized for Agno session management and RAG capabilities

-- Enable required extensions (same across all environments)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";  -- For future RAG functionality
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- For text search optimization

-- =============================================================================
-- DYNAMIC TABLE CREATION FUNCTION
-- =============================================================================

-- Function to create tables with environment-specific prefixes
CREATE OR REPLACE FUNCTION create_legacy_tables(table_prefix TEXT DEFAULT '')
RETURNS VOID AS $$
DECLARE
    projects_table TEXT := table_prefix || 'projects';
    responses_table TEXT := table_prefix || 'interview_responses';
    themes_table TEXT := table_prefix || 'interview_themes';
    sessions_table TEXT := table_prefix || 'agent_sessions';
    runs_table TEXT := table_prefix || 'agent_runs';
    messages_table TEXT := table_prefix || 'agent_messages';
    memories_table TEXT := table_prefix || 'user_memories';
    summaries_table TEXT := table_prefix || 'session_summaries';
    docs_table TEXT := table_prefix || 'knowledge_documents';
    embeddings_table TEXT := table_prefix || 'document_embeddings';
BEGIN
    -- =============================================================================
    -- CORE PROJECT DATA
    -- =============================================================================
    
    -- Projects table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            subject_name VARCHAR(255) NOT NULL,
            subject_age INTEGER,
            relation VARCHAR(100) NOT NULL,
            background TEXT,
            interview_mode VARCHAR(20) NOT NULL CHECK (interview_mode IN (''self'', ''family'', ''hybrid'')),
            language VARCHAR(10) NOT NULL DEFAULT ''en'',
            status VARCHAR(50) NOT NULL DEFAULT ''created'' CHECK (status IN (''created'', ''seed_questions'', ''themes_identified'', ''deep_dive'', ''completed'')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT ''{}''
        )', projects_table);

    -- Create indexes for projects
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (status)', 'idx_' || table_prefix || 'projects_status', projects_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (created_at)', 'idx_' || table_prefix || 'projects_created_at', projects_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (subject_name)', 'idx_' || table_prefix || 'projects_subject_name', projects_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING gin (metadata)', 'idx_' || table_prefix || 'projects_metadata_gin', projects_table);

    -- Interview responses table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID NOT NULL REFERENCES %I(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            question_type VARCHAR(20) NOT NULL DEFAULT ''seed'' CHECK (question_type IN (''seed'', ''followup'', ''theme'')),
            theme_id UUID,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            followup_questions JSONB DEFAULT ''[]'',
            metadata JSONB DEFAULT ''{}''
        )', responses_table, projects_table);

    -- Create indexes for responses
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (project_id)', 'idx_' || table_prefix || 'responses_project_id', responses_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (timestamp)', 'idx_' || table_prefix || 'responses_timestamp', responses_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (question_type)', 'idx_' || table_prefix || 'responses_question_type', responses_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING gin (to_tsvector(''english'', answer))', 'idx_' || table_prefix || 'responses_answer_fts', responses_table);

    -- Interview themes table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID NOT NULL REFERENCES %I(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            questions JSONB DEFAULT ''[]'',
            suggested_interviewer VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT ''{}''
        )', themes_table, projects_table);

    -- Create indexes for themes
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (project_id)', 'idx_' || table_prefix || 'themes_project_id', themes_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (name)', 'idx_' || table_prefix || 'themes_name', themes_table);

    -- =============================================================================
    -- AGNO SESSION MANAGEMENT
    -- =============================================================================

    -- Agent sessions table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255),
            agent_id VARCHAR(255),
            team_id VARCHAR(255),
            session_type VARCHAR(50) NOT NULL DEFAULT ''agent'',
            session_data JSONB DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (session_id)
        )', sessions_table);

    -- Create indexes for sessions
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (user_id)', 'idx_' || table_prefix || 'sessions_user_id', sessions_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (agent_id)', 'idx_' || table_prefix || 'sessions_agent_id', sessions_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (created_at)', 'idx_' || table_prefix || 'sessions_created_at', sessions_table);

    -- Agent runs table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id VARCHAR(255) NOT NULL REFERENCES %I(session_id) ON DELETE CASCADE,
            agent_id VARCHAR(255),
            team_id VARCHAR(255),
            run_data JSONB NOT NULL DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )', runs_table, sessions_table);

    -- Create indexes for runs
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (session_id)', 'idx_' || table_prefix || 'runs_session_id', runs_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (created_at)', 'idx_' || table_prefix || 'runs_created_at', runs_table);

    -- Agent messages table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id VARCHAR(255) NOT NULL REFERENCES %I(session_id) ON DELETE CASCADE,
            run_id UUID REFERENCES %I(run_id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL CHECK (role IN (''system'', ''user'', ''assistant'', ''function'', ''tool'')),
            content TEXT NOT NULL,
            message_data JSONB DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )', messages_table, sessions_table, runs_table);

    -- Create indexes for messages
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (session_id)', 'idx_' || table_prefix || 'messages_session_id', messages_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (role)', 'idx_' || table_prefix || 'messages_role', messages_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (created_at)', 'idx_' || table_prefix || 'messages_created_at', messages_table);

    -- User memories table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id VARCHAR(255) NOT NULL,
            memory TEXT NOT NULL,
            memory_data JSONB DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )', memories_table);

    -- Create indexes for memories
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (user_id)', 'idx_' || table_prefix || 'memories_user_id', memories_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (created_at)', 'idx_' || table_prefix || 'memories_created_at', memories_table);

    -- Session summaries table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id VARCHAR(255) NOT NULL REFERENCES %I(session_id) ON DELETE CASCADE,
            summary TEXT NOT NULL,
            summary_data JSONB DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )', summaries_table, sessions_table);

    -- Create indexes for summaries
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (session_id)', 'idx_' || table_prefix || 'summaries_session_id', summaries_table);

    -- =============================================================================
    -- RAG AND VECTOR STORAGE
    -- =============================================================================

    -- Knowledge documents table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID REFERENCES %I(id) ON DELETE CASCADE,
            title VARCHAR(500),
            content TEXT NOT NULL,
            source_type VARCHAR(50) NOT NULL DEFAULT ''interview'' CHECK (source_type IN (''interview'', ''document'', ''audio'', ''transcript'')),
            source_url TEXT,
            metadata JSONB DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )', docs_table, projects_table);

    -- Create indexes for documents
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (project_id)', 'idx_' || table_prefix || 'docs_project_id', docs_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (source_type)', 'idx_' || table_prefix || 'docs_source_type', docs_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING gin (to_tsvector(''english'', content))', 'idx_' || table_prefix || 'docs_content_fts', docs_table);

    -- Document embeddings table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_id UUID NOT NULL REFERENCES %I(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB DEFAULT ''{}'' ,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )', embeddings_table, docs_table);

    -- Create indexes for embeddings
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (document_id)', 'idx_' || table_prefix || 'embeddings_document_id', embeddings_table);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (chunk_index)', 'idx_' || table_prefix || 'embeddings_chunk_index', embeddings_table);
    
    -- Vector similarity indexes (if pgvector is available)
    BEGIN
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)', 'idx_' || table_prefix || 'embeddings_vector_cosine', embeddings_table);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING ivfflat (embedding vector_l2_ops) WITH (lists = 100)', 'idx_' || table_prefix || 'embeddings_vector_l2', embeddings_table);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Vector indexes skipped - pgvector may not be available';
    END;

    RAISE NOTICE 'Created tables with prefix: %', table_prefix;
    
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ENVIRONMENT-SPECIFIC TABLE CREATION
-- =============================================================================

-- Create CI environment tables
SELECT create_legacy_tables('ci_');

-- Create Test environment tables  
SELECT create_legacy_tables('test_');

-- Create Production environment tables (no prefix)
SELECT create_legacy_tables('');

-- Create Development environment tables
SELECT create_legacy_tables('dev_');

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to get environment info
CREATE OR REPLACE FUNCTION get_environment_info(env_prefix TEXT DEFAULT '')
RETURNS TABLE(
    environment TEXT,
    table_count INTEGER,
    tables TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN env_prefix = 'ci_' THEN 'CI'
            WHEN env_prefix = 'test_' THEN 'TEST'
            WHEN env_prefix = 'dev_' THEN 'DEVELOPMENT'
            WHEN env_prefix = '' THEN 'PRODUCTION'
            ELSE 'UNKNOWN'
        END as environment,
        COUNT(*)::INTEGER as table_count,
        array_agg(tablename::TEXT) as tables
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename LIKE env_prefix || '%'
    AND tablename NOT LIKE '%_pkey'
    GROUP BY env_prefix;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up environment tables
CREATE OR REPLACE FUNCTION cleanup_environment_tables(env_prefix TEXT)
RETURNS VOID AS $$
DECLARE
    table_record RECORD;
BEGIN
    FOR table_record IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE env_prefix || '%'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_record.tablename);
    END LOOP;
    
    RAISE NOTICE 'Cleaned up tables with prefix: %', env_prefix;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON FUNCTION create_legacy_tables IS 'Creates all Legacy Interview App tables with specified prefix for environment isolation';
COMMENT ON FUNCTION get_environment_info IS 'Returns information about tables in each environment';
COMMENT ON FUNCTION cleanup_environment_tables IS 'Removes all tables for a specific environment prefix';

-- =============================================================================
-- INITIAL SETUP VERIFICATION
-- =============================================================================

-- Verify all environments have been created
DO $$
DECLARE
    env_record RECORD;
BEGIN
    FOR env_record IN 
        SELECT * FROM get_environment_info('ci_')
        UNION ALL
        SELECT * FROM get_environment_info('test_')
        UNION ALL
        SELECT * FROM get_environment_info('')
        UNION ALL
        SELECT * FROM get_environment_info('dev_')
    LOOP
        RAISE NOTICE 'Environment: % - Tables: %', env_record.environment, env_record.table_count;
    END LOOP;
END;
$$;
