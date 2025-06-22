-- =============================================================================
-- SYNTHIA STYLE DATABASE INITIALIZATION SCRIPT
-- =============================================================================
-- Initial database setup for PostgreSQL

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('USER', 'PREMIUM', 'ADMIN', 'SUPER_ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE analysis_type AS ENUM ('FACIAL', 'CHROMATIC');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE face_shape AS ENUM ('OVALADO', 'REDONDO', 'CUADRADO', 'RECTANGULAR', 'CORAZÓN', 'DIAMANTE', 'TRIANGULAR', 'UNKNOWN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE color_season AS ENUM ('INVIERNO', 'PRIMAVERA', 'VERANO', 'OTOÑO', 'UNKNOWN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE skin_undertone AS ENUM ('FRIO', 'CALIDO', 'NEUTRO', 'UNKNOWN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create performance optimization indexes (will be created after Prisma migration)
-- These are additional indexes for better performance

-- Function for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Performance monitoring view
CREATE OR REPLACE VIEW performance_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Database health check function
CREATE OR REPLACE FUNCTION db_health_check()
RETURNS TABLE (
    metric_name TEXT,
    metric_value TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'database_size'::TEXT,
        pg_size_pretty(pg_database_size(current_database()))::TEXT,
        CASE 
            WHEN pg_database_size(current_database()) < 1073741824 THEN 'OK'
            WHEN pg_database_size(current_database()) < 5368709120 THEN 'WARNING'
            ELSE 'CRITICAL'
        END::TEXT
    UNION ALL
    SELECT 
        'active_connections'::TEXT,
        count(*)::TEXT,
        CASE 
            WHEN count(*) < 50 THEN 'OK'
            WHEN count(*) < 100 THEN 'WARNING'
            ELSE 'CRITICAL'
        END::TEXT
    FROM pg_stat_activity 
    WHERE state = 'active'
    UNION ALL
    SELECT 
        'database_version'::TEXT,
        version()::TEXT,
        'INFO'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Create backup user with limited permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'backup_user') THEN
        CREATE ROLE backup_user WITH LOGIN PASSWORD 'backup_password_change_in_production';
        GRANT CONNECT ON DATABASE synthia_style_db TO backup_user;
        GRANT USAGE ON SCHEMA public TO backup_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;
    END IF;
END
$$;

-- Create monitoring user with read-only access
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'monitoring_user') THEN
        CREATE ROLE monitoring_user WITH LOGIN PASSWORD 'monitoring_password_change_in_production';
        GRANT CONNECT ON DATABASE synthia_style_db TO monitoring_user;
        GRANT USAGE ON SCHEMA public TO monitoring_user;
        GRANT USAGE ON SCHEMA information_schema TO monitoring_user;
        GRANT USAGE ON SCHEMA pg_catalog TO monitoring_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO monitoring_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO monitoring_user;
    END IF;
END
$$;

-- Performance tuning settings (adjust based on available memory)
-- These will be overridden by postgresql.conf in production

-- Commented out as these should be set in postgresql.conf
-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';
-- ALTER SYSTEM SET maintenance_work_mem = '64MB';
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9;
-- ALTER SYSTEM SET wal_buffers = '16MB';
-- ALTER SYSTEM SET default_statistics_target = 100;
-- ALTER SYSTEM SET random_page_cost = 1.1;
-- ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
-- SELECT pg_reload_conf();

-- Log successful initialization
INSERT INTO pg_stat_statements_reset();

-- Create initial admin user (will be handled by application)
-- This is just a placeholder for reference

COMMENT ON DATABASE synthia_style_db IS 'Synthia Style - AI Style Analysis Platform Database';

-- Grant necessary permissions to main user
GRANT ALL PRIVILEGES ON DATABASE synthia_style_db TO synthia_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO synthia_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO synthia_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO synthia_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO synthia_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO synthia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO synthia_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO synthia_user;

-- Log the initialization
\echo 'Synthia Style database initialization completed successfully!'
