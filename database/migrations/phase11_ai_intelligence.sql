-- ==============================================================================
-- LOGIAGENT PHASE 11: ADVANCED AI & LOGISTICS INTELLIGENCE MIGRATION
-- Creates alerts table with deduplication and fast lookup indexes
-- Compatible with PostgreSQL (Supabase) and SQLite
-- ==============================================================================

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_code VARCHAR(50) NOT NULL UNIQUE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    evidence TEXT,
    recommended_action TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance & Deduplication Indexes
CREATE INDEX IF NOT EXISTS ix_alerts_alert_code ON alerts(alert_code);
CREATE INDEX IF NOT EXISTS ix_alerts_alert_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS ix_alerts_entity_type ON alerts(entity_type);
CREATE INDEX IF NOT EXISTS ix_alerts_entity_id ON alerts(entity_id);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS ix_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS ix_alerts_updated_at ON alerts(updated_at);
CREATE INDEX IF NOT EXISTS ix_alerts_dedup ON alerts(alert_type, entity_type, entity_id, status);
CREATE INDEX IF NOT EXISTS ix_alerts_created_severity ON alerts(created_at, severity);
