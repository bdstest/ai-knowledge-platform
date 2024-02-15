-- Initialize AI Knowledge Platform Database
-- PostgreSQL initialization script

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database user (if not exists)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'demouser') THEN
      CREATE ROLE demouser LOGIN PASSWORD 'demopass123';
   END IF;
END
$do$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE knowledge_db TO demouser;
GRANT ALL ON SCHEMA public TO demouser;

-- Knowledge Documents table
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    document_type VARCHAR(50),
    tags VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    severity VARCHAR(20) DEFAULT 'medium',
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(100),
    resolution_time INTEGER, -- minutes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Search metrics table
CREATE TABLE IF NOT EXISTS search_metrics (
    id SERIAL PRIMARY KEY,
    query VARCHAR(255),
    response_time_ms FLOAT,
    results_count INTEGER,
    user_agent VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_documents(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_search_timestamp ON search_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);

-- Insert sample knowledge documents
INSERT INTO knowledge_documents (title, content, category, document_type, tags) VALUES
('Network Troubleshooting Guide', 'Network connectivity issues can be resolved by checking physical connections, verifying IP configuration, testing DNS resolution, and examining firewall rules. Common tools include ping, traceroute, nslookup, and netstat.', 'Network', 'procedure', 'network,troubleshooting,connectivity'),
('Database Connection Timeout Resolution', 'Database connection timeouts typically occur due to connection pool exhaustion, long-running queries, or network latency. Increase connection timeout values, optimize queries, and monitor connection pool usage.', 'Database', 'troubleshooting', 'database,timeout,performance'),
('Email Server Configuration', 'Email server setup requires configuring SMTP, IMAP/POP3 settings, setting up DNS MX records, implementing security protocols like SPF, DKIM, and DMARC, and configuring anti-spam measures.', 'Email', 'configuration', 'email,smtp,configuration'),
('Security Incident Response Playbook', 'Security incident response involves immediate containment, evidence preservation, threat analysis, communication to stakeholders, remediation steps, and post-incident review. Follow the incident severity matrix for escalation.', 'Security', 'playbook', 'security,incident,response'),
('Backup and Recovery Procedures', 'Implement 3-2-1 backup strategy: 3 copies of data, 2 different media types, 1 offsite backup. Test backup integrity regularly, document recovery procedures, and maintain recovery time objectives (RTO) and recovery point objectives (RPO).', 'Backup', 'procedure', 'backup,recovery,disaster')
ON CONFLICT DO NOTHING;

-- Insert sample incidents
INSERT INTO incidents (incident_id, title, description, category, severity, resolution_time) VALUES
('INC-2024-001', 'Email server outage', 'Users unable to send or receive emails', 'Email Infrastructure', 'high', 45),
('INC-2024-002', 'Database connection timeout', 'Application showing database connection timeout errors', 'Database', 'medium', 22),
('INC-2024-003', 'Website loading slowly', 'Website pages taking more than 10 seconds to load', 'Performance', 'medium', 67),
('INC-2024-004', 'Network connectivity issues', 'Intermittent network connectivity problems affecting multiple users', 'Network', 'high', 89),
('INC-2024-005', 'Login authentication failure', 'Users cannot log in with correct credentials', 'Authentication', 'critical', 34)
ON CONFLICT DO NOTHING;

-- Insert sample search metrics
INSERT INTO search_metrics (query, response_time_ms, results_count) VALUES
('network troubleshooting', 245.5, 8),
('database timeout', 187.2, 5),
('email configuration', 298.7, 12),
('security incident', 156.8, 15),
('backup procedures', 203.4, 7)
ON CONFLICT DO NOTHING;

-- Insert sample system metrics
INSERT INTO system_metrics (metric_name, metric_value) VALUES
('search_total_count', 1247),
('incidents_total_count', 156),
('avg_response_time_ms', 245.2),
('system_uptime_percent', 99.97),
('knowledge_coverage_percent', 89.0)
ON CONFLICT DO NOTHING;

-- Grant permissions on tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO demouser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO demouser;