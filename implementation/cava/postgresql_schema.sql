-- 🏛️ CAVA PostgreSQL Schema
-- Constitutional compliance: Uses separate schema to maintain MODULE INDEPENDENCE
-- Works with existing AWS RDS PostgreSQL instance

-- Create CAVA schema
CREATE SCHEMA IF NOT EXISTS cava;

-- Set search path
SET search_path TO cava, public;

-- CAVA conversation sessions table
CREATE TABLE IF NOT EXISTS cava.conversation_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    farmer_id INTEGER REFERENCES public.farmers(id),
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    conversation_type VARCHAR(50), -- 'registration', 'farming', 'mixed'
    total_messages INTEGER DEFAULT 0,
    registration_completed BOOLEAN DEFAULT FALSE,
    llm_tokens_used INTEGER DEFAULT 0,
    constitutional_compliance_score DECIMAL(5,2) DEFAULT 100.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CAVA intelligence log (Amendment #15 compliance)
CREATE TABLE IF NOT EXISTS cava.intelligence_log (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES cava.conversation_sessions(session_id),
    message_timestamp TIMESTAMP DEFAULT NOW(),
    message_type VARCHAR(50), -- 'user', 'ava', 'system'
    raw_message TEXT,
    llm_analysis JSONB, -- LLM decision making process
    database_queries JSONB, -- Generated queries for each database
    response_synthesis JSONB, -- How response was constructed
    performance_metrics JSONB, -- Response times, query efficiency
    error_log JSONB, -- Any errors encountered
    created_at TIMESTAMP DEFAULT NOW()
);

-- CAVA graph sync table (tracks Neo4j data)
CREATE TABLE IF NOT EXISTS cava.graph_sync (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50), -- 'farmer', 'field', 'crop', 'application'
    entity_id VARCHAR(255),
    neo4j_id VARCHAR(255),
    sync_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'synced', 'failed'
    last_sync TIMESTAMP,
    sync_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CAVA performance metrics
CREATE TABLE IF NOT EXISTS cava.performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE DEFAULT CURRENT_DATE,
    metric_hour INTEGER DEFAULT EXTRACT(HOUR FROM NOW()),
    total_conversations INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(10,2),
    neo4j_query_count INTEGER DEFAULT 0,
    redis_hit_rate DECIMAL(5,2),
    llm_success_rate DECIMAL(5,2),
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_farmer_id ON cava.conversation_sessions(farmer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON cava.conversation_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_session_id ON cava.intelligence_log(session_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_timestamp ON cava.intelligence_log(message_timestamp);
CREATE INDEX IF NOT EXISTS idx_graph_sync_entity ON cava.graph_sync(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date_hour ON cava.performance_metrics(metric_date, metric_hour);

-- Function to update conversation metrics
CREATE OR REPLACE FUNCTION cava.update_conversation_metrics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cava.conversation_sessions
    SET 
        total_messages = total_messages + 1,
        updated_at = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update metrics
CREATE TRIGGER update_conversation_metrics_trigger
AFTER INSERT ON cava.intelligence_log
FOR EACH ROW
EXECUTE FUNCTION cava.update_conversation_metrics();

-- Grant permissions (adjust as needed)
-- GRANT USAGE ON SCHEMA cava TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cava TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cava TO your_app_user;

-- Constitutional compliance comment
COMMENT ON SCHEMA cava IS '🏛️ CAVA: Conversation Architecture for AVA OLO - Amendment #15 compliant, LLM-first intelligence';
COMMENT ON TABLE cava.conversation_sessions IS 'Tracks all farmer conversations with constitutional compliance';
COMMENT ON TABLE cava.intelligence_log IS 'Complete audit trail of LLM decisions (TRANSPARENCY principle)';
COMMENT ON TABLE cava.graph_sync IS 'Synchronization tracking between PostgreSQL and Neo4j';
COMMENT ON TABLE cava.performance_metrics IS 'Performance monitoring for PRODUCTION-READY principle';