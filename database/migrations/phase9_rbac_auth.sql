-- ==============================================================================
-- LogiAgent Phase 9: Authentication & RBAC Database Migration
-- PostgreSQL / Supabase Migration with Row-Level Security (RLS) & Idempotent Seeding
-- ==============================================================================

-- 1. ROLES TABLE
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. ROLE_PERMISSIONS MAPPING TABLE
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- 4. USERS / PROFILES TABLE ENHANCEMENTS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Driver',
    role_id INTEGER REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    account_status VARCHAR(50) DEFAULT 'Active',
    approval_status VARCHAR(50) DEFAULT 'Approved',
    driver_id INTEGER REFERENCES drivers(id),
    invited_by_id INTEGER REFERENCES users(id),
    approved_by_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    activation_token VARCHAR(255),
    activation_expires_at TIMESTAMP WITH TIME ZONE,
    auth_user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alter users table if already exists
DO $$ 
BEGIN 
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INTEGER REFERENCES roles(id); EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS account_status VARCHAR(50) DEFAULT 'Active'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'Approved'; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS driver_id INTEGER REFERENCES drivers(id); EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS invited_by_id INTEGER REFERENCES users(id); EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_by_id INTEGER REFERENCES users(id); EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS activation_token VARCHAR(255); EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS activation_expires_at TIMESTAMP WITH TIME ZONE; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_user_id VARCHAR(255); EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(); EXCEPTION WHEN OTHERS THEN NULL; END;
END $$;

-- 5. APPROVAL POLICIES TABLE
CREATE TABLE IF NOT EXISTS approval_policies (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    requires_approval BOOLEAN DEFAULT TRUE,
    allowed_approver_roles TEXT DEFAULT '["Admin"]',
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- Idempotent Role Seeding
-- ==============================================================================
INSERT INTO roles (name, description) VALUES
    ('Admin', 'Full system governance, security policies, user management, and operational oversight.')
    ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description) VALUES
    ('Logistics Manager', 'Operations management, fleet scheduling, shipment dispatch, approvals, analytics, and AI tools.')
    ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description) VALUES
    ('Dispatcher', 'Active shipment scheduling, driver/vehicle assignments, corridor optimization, and live monitoring.')
    ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description) VALUES
    ('Fleet Manager', 'Vehicle maintenance, asset lifecycle, driver roster governance, capacity, and compliance.')
    ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description) VALUES
    ('Driver', 'Commercial freight operator with access strictly scoped to assigned shipments, vehicle, and route.')
    ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description) VALUES
    ('Analyst', 'Read-only access to logistics business intelligence, delay metrics, SLA trends, and cost modeling.')
    ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description) VALUES
    ('Operations Team', 'Terminal operations personnel with read and operational update capabilities.')
    ON CONFLICT (name) DO NOTHING;

-- ==============================================================================
-- Idempotent Permissions Seeding
-- ==============================================================================
INSERT INTO permissions (name, resource, action, description) VALUES
    ('user:create', 'user', 'create', 'Provision or register new user accounts'),
    ('user:read', 'user', 'read', 'View user account profiles and audit statuses'),
    ('user:update', 'user', 'update', 'Update user profiles, statuses, and operational links'),
    ('user:delete', 'user', 'delete', 'Deactivate or remove user accounts'),
    ('user:approve', 'user', 'approve', 'Authorize pending user accounts according to approval hierarchy'),
    ('role:manage', 'role', 'manage', 'Configure roles, approval policies, and permission grants'),
    
    ('shipment:create', 'shipment', 'create', 'Create new commercial freight shipments'),
    ('shipment:read', 'shipment', 'read', 'Read freight shipment records'),
    ('shipment:read_all', 'shipment', 'read_all', 'Read all organization shipments across entire network'),
    ('shipment:read_own', 'shipment', 'read_own', 'Read only assigned shipments for authenticated driver'),
    ('shipment:update', 'shipment', 'update', 'Update shipment status, location, or carrier assignment'),
    ('shipment:delete', 'shipment', 'delete', 'Cancel or delete shipment records'),
    
    ('route:create', 'route', 'create', 'Plan new transportation corridors and routes'),
    ('route:read', 'route', 'read', 'View route waypoints, telemetry, and polylines'),
    ('route:read_all', 'route', 'read_all', 'View all routes across the logistics network'),
    ('route:read_own', 'route', 'read_own', 'View routes assigned to the authenticated driver'),
    ('route:update', 'route', 'update', 'Modify route waypoints and scheduled milestones'),
    ('route:cancel', 'route', 'cancel', 'Cancel scheduled or active routes'),
    ('route:optimize', 'route', 'optimize', 'Execute AI/ML route and fuel cost optimization algorithms'),
    
    ('vehicle:create', 'vehicle', 'create', 'Register new commercial fleet vehicles'),
    ('vehicle:read', 'vehicle', 'read', 'View vehicle specifications and status'),
    ('vehicle:read_all', 'vehicle', 'read_all', 'View entire vehicle fleet telemetry and capacity'),
    ('vehicle:read_own', 'vehicle', 'read_own', 'View only assigned vehicle telemetry for authenticated driver'),
    ('vehicle:update', 'vehicle', 'update', 'Update vehicle status, maintenance schedule, and driver assignment'),
    ('vehicle:delete', 'vehicle', 'delete', 'Decommission fleet vehicles'),
    
    ('driver:create', 'driver', 'create', 'Register new commercial drivers and CDL credentials'),
    ('driver:read', 'driver', 'read', 'View driver operational profiles and HOS metrics'),
    ('driver:read_all', 'driver', 'read_all', 'View all drivers across regional terminals'),
    ('driver:read_own', 'driver', 'read_own', 'View authenticated driver profile and duty status'),
    ('driver:update', 'driver', 'update', 'Update driver status, HOS logs, and vehicle pairing'),
    ('driver:delete', 'driver', 'delete', 'Deactivate driver operational profiles'),
    
    ('analytics:read', 'analytics', 'read', 'Access logistics analytics and KPIs'),
    ('analytics:read_all', 'analytics', 'read_all', 'Full access to executive, financial, and SLA analytics'),
    ('analytics:read_limited', 'analytics', 'read_limited', 'Operational dispatcher-level KPIs and telemetry'),
    ('analytics:read_own', 'analytics', 'read_own', 'Driver performance, HOS, and completion metrics'),
    ('analytics:export', 'analytics', 'export', 'Export analytics and cost reports to CSV'),
    
    ('ai:use', 'ai', 'use', 'Interact with LogiAgent AI Assistant and LangGraph agents'),
    ('documents:read', 'documents', 'read', 'Query policy documents and standard operating procedures (SOPs)'),
    ('documents:manage', 'documents', 'manage', 'Upload, index, and re-vectorize policy documents'),
    ('notifications:read', 'notifications', 'read', 'View notification alerts'),
    ('settings:manage', 'settings', 'manage', 'Configure system-wide parameters and integrations')
ON CONFLICT (name) DO NOTHING;

-- ==============================================================================
-- Idempotent Approval Policies Seeding
-- ==============================================================================
INSERT INTO approval_policies (role_name, requires_approval, allowed_approver_roles, description) VALUES
    ('Driver', TRUE, '["Admin", "Logistics Manager", "Fleet Manager"]', 'Commercial driver accounts require manager or admin approval before activation.'),
    ('Dispatcher', TRUE, '["Admin", "Logistics Manager"]', 'Dispatcher accounts require logistics management approval.'),
    ('Fleet Manager', TRUE, '["Admin", "Logistics Manager"]', 'Fleet management accounts require director or admin approval.'),
    ('Logistics Manager', TRUE, '["Admin"]', 'Management accounts require administrator authorization.'),
    ('Analyst', FALSE, '["Admin", "Logistics Manager"]', 'Analytics accounts can be auto-approved or approved by managers.'),
    ('Admin', TRUE, '["Admin"]', 'Administrator accounts require primary admin approval.')
ON CONFLICT (role_name) DO NOTHING;

-- ==============================================================================
-- Supabase Row Level Security (RLS) Policies
-- ==============================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE drivers ENABLE ROW LEVEL SECURITY;

-- 1. Users RLS Policies
DROP POLICY IF EXISTS "Users can read own profile or admins read all" ON users;
CREATE POLICY "Users can read own profile or admins read all" ON users
    FOR SELECT
    USING (
        auth.uid()::text = auth_user_id 
        OR (SELECT role FROM users WHERE auth_user_id = auth.uid()::text) IN ('Admin', 'Logistics Manager')
    );

-- 2. Shipments RLS Policies
DROP POLICY IF EXISTS "Drivers see assigned shipments, managers see all" ON shipments;
CREATE POLICY "Drivers see assigned shipments, managers see all" ON shipments
    FOR SELECT
    USING (
        (SELECT role FROM users WHERE auth_user_id = auth.uid()::text) IN ('Admin', 'Logistics Manager', 'Dispatcher', 'Operations Team', 'Analyst')
        OR (
            (SELECT role FROM users WHERE auth_user_id = auth.uid()::text) = 'Driver'
            AND driver_id = (SELECT driver_id FROM users WHERE auth_user_id = auth.uid()::text)
        )
    );

-- 3. Drivers RLS Policies
DROP POLICY IF EXISTS "Drivers see own profile, managers see all" ON drivers;
CREATE POLICY "Drivers see own profile, managers see all" ON drivers
    FOR SELECT
    USING (
        (SELECT role FROM users WHERE auth_user_id = auth.uid()::text) IN ('Admin', 'Logistics Manager', 'Dispatcher', 'Fleet Manager', 'Operations Team', 'Analyst')
        OR (
            (SELECT role FROM users WHERE auth_user_id = auth.uid()::text) = 'Driver'
            AND id = (SELECT driver_id FROM users WHERE auth_user_id = auth.uid()::text)
        )
    );
