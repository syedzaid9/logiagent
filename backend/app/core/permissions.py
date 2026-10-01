from typing import List, Dict, Set

# ==============================================================================
# Granular Permission String Constants (colon & snake_case compatibility)
# ==============================================================================

# User & Access Governance
PERMISSION_USERS_READ = "users:read"
PERMISSION_USERS_CREATE = "users:create"
PERMISSION_USERS_MANAGE = "users:manage"
PERMISSION_USERS_APPROVE = "users:approve"
PERMISSION_USERS_SUSPEND = "users:suspend"
PERMISSION_USERS_DELETE = "users:delete"
PERMISSION_ROLES_MANAGE = "roles:manage"
PERMISSION_ROLES_READ = "roles:read"

# Shipment Management
PERMISSION_SHIPMENTS_CREATE = "shipments:create"
PERMISSION_SHIPMENTS_READ_ALL = "shipments:read_all"
PERMISSION_SHIPMENTS_READ_OWN = "shipments:read_own"
PERMISSION_SHIPMENTS_READ = "shipments:read"
PERMISSION_SHIPMENTS_UPDATE = "shipments:update"
PERMISSION_SHIPMENTS_MANAGE = "shipments:manage"
PERMISSION_SHIPMENTS_CANCEL = "shipments:cancel"
PERMISSION_SHIPMENTS_DELETE = "shipments:delete"

# Fleet & Vehicle Management
PERMISSION_VEHICLES_CREATE = "vehicles:create"
PERMISSION_VEHICLES_READ_ALL = "vehicles:read_all"
PERMISSION_VEHICLES_READ_OWN = "vehicles:read_own"
PERMISSION_VEHICLES_READ = "vehicles:read"
PERMISSION_VEHICLES_UPDATE = "vehicles:update"
PERMISSION_VEHICLES_DELETE = "vehicles:delete"
PERMISSION_VEHICLES_MANAGE = "vehicles:manage"

# Driver Fleet Management
PERMISSION_DRIVERS_CREATE = "drivers:create"
PERMISSION_DRIVERS_READ_ALL = "drivers:read_all"
PERMISSION_DRIVERS_READ_OWN = "drivers:read_own"
PERMISSION_DRIVERS_READ = "drivers:read"
PERMISSION_DRIVERS_UPDATE = "drivers:update"
PERMISSION_DRIVERS_DELETE = "drivers:delete"
PERMISSION_DRIVERS_MANAGE = "drivers:manage"

# Route Planning & Optimization
PERMISSION_ROUTES_CREATE = "routes:create"
PERMISSION_ROUTES_READ_ALL = "routes:read_all"
PERMISSION_ROUTES_READ_OWN = "routes:read_own"
PERMISSION_ROUTES_READ = "routes:read"
PERMISSION_TELEMETRY_READ = "telemetry:read"
PERMISSION_ROUTES_UPDATE = "routes:update"
PERMISSION_ROUTES_CANCEL = "routes:cancel"
PERMISSION_ROUTES_MANAGE = "routes:manage"
PERMISSION_ROUTES_OPTIMIZE = "routes:optimize"

# Analytics & Intelligence
PERMISSION_ANALYTICS_READ = "analytics:read"
PERMISSION_ANALYTICS_READ_ALL = "analytics:read_all"
PERMISSION_ANALYTICS_READ_LIMITED = "analytics:read_limited"
PERMISSION_ANALYTICS_READ_OWN = "analytics:read_own"
PERMISSION_ANALYTICS_EXPORT = "analytics:export"

# Policy, SOPs & Knowledge Documents (RAG)
PERMISSION_DOCUMENTS_READ = "documents:read"
PERMISSION_DOCUMENTS_CREATE = "documents:create"
PERMISSION_DOCUMENTS_MANAGE = "documents:manage"
PERMISSION_DOCUMENTS_REINDEX = "documents:reindex"

# Notification Center
PERMISSION_NOTIFICATIONS_READ = "notifications:read"
PERMISSION_NOTIFICATIONS_READ_ALL = "notifications:read_all"
PERMISSION_NOTIFICATIONS_READ_OWN = "notifications:read_own"
PERMISSION_NOTIFICATIONS_CREATE = "notifications:create"

# AI Assistant & LangGraph Agents
PERMISSION_AI_USE = "ai:use"
PERMISSION_AGENT_FULL = "agent:full_access"
PERMISSION_AGENT_DRIVER = "agent:driver_restricted"

# Platform Settings
PERMISSION_SETTINGS_MANAGE = "settings:manage"
PERMISSION_SETTINGS_READ = "settings:read"

# ==============================================================================
# Canonical Permission Definitions (For DB Seeding & Documentation)
# ==============================================================================
ALL_SYSTEM_PERMISSIONS = [
    {"name": "user:create", "resource": "user", "action": "create", "description": "Provision or register new user accounts"},
    {"name": "user:read", "resource": "user", "action": "read", "description": "View user account profiles and audit statuses"},
    {"name": "user:update", "resource": "user", "action": "update", "description": "Update user profiles, statuses, and operational links"},
    {"name": "user:delete", "resource": "user", "action": "delete", "description": "Deactivate or remove user accounts"},
    {"name": "user:approve", "resource": "user", "action": "approve", "description": "Authorize pending user accounts according to approval hierarchy"},
    {"name": "user:suspend", "resource": "user", "action": "suspend", "description": "Suspend user account access"},
    {"name": "user:manage", "resource": "user", "action": "manage", "description": "Comprehensive user governance"},
    {"name": "role:read", "resource": "role", "action": "read", "description": "View system roles and permission sets"},
    {"name": "role:manage", "resource": "role", "action": "manage", "description": "Configure roles, approval policies, and permission grants"},
    
    {"name": "shipment:create", "resource": "shipment", "action": "create", "description": "Create new commercial freight shipments"},
    {"name": "shipment:read", "resource": "shipment", "action": "read", "description": "Read freight shipment records"},
    {"name": "shipment:read_all", "resource": "shipment", "action": "read_all", "description": "Read all organization shipments across entire network"},
    {"name": "shipment:read_own", "resource": "shipment", "action": "read_own", "description": "Read only assigned shipments for authenticated driver"},
    {"name": "shipment:update", "resource": "shipment", "action": "update", "description": "Update shipment status, location, or carrier assignment"},
    {"name": "shipment:cancel", "resource": "shipment", "action": "cancel", "description": "Cancel scheduled or active shipments"},
    {"name": "shipment:delete", "resource": "shipment", "action": "delete", "description": "Delete shipment records"},
    {"name": "shipment:manage", "resource": "shipment", "action": "manage", "description": "Full shipment lifecycle management"},
    
    {"name": "route:create", "resource": "route", "action": "create", "description": "Plan new transportation corridors and routes"},
    {"name": "route:read", "resource": "route", "action": "read", "description": "View route waypoints, telemetry, and polylines"},
    {"name": "route:read_all", "resource": "route", "action": "read_all", "description": "View all routes across the logistics network"},
    {"name": "telemetry:read", "resource": "telemetry", "action": "read", "description": "View live GPS telemetry, engine diagnostics, and route corridor tracking"},
    {"name": "route:read_own", "resource": "route", "action": "read_own", "description": "View routes assigned to the authenticated driver"},
    {"name": "route:update", "resource": "route", "action": "update", "description": "Modify route waypoints and scheduled milestones"},
    {"name": "route:cancel", "resource": "route", "action": "cancel", "description": "Cancel scheduled or active routes"},
    {"name": "route:optimize", "resource": "route", "action": "optimize", "description": "Execute AI/ML route and fuel cost optimization algorithms"},
    {"name": "route:manage", "resource": "route", "action": "manage", "description": "Full route corridor management and re-dispatch"},
    
    {"name": "vehicle:create", "resource": "vehicle", "action": "create", "description": "Register new commercial fleet vehicles"},
    {"name": "vehicle:read", "resource": "vehicle", "action": "read", "description": "View vehicle specifications and status"},
    {"name": "vehicle:read_all", "resource": "vehicle", "action": "read_all", "description": "View entire vehicle fleet telemetry and capacity"},
    {"name": "vehicle:read_own", "resource": "vehicle", "action": "read_own", "description": "View only assigned vehicle telemetry for authenticated driver"},
    {"name": "vehicle:update", "resource": "vehicle", "action": "update", "description": "Update vehicle status, maintenance schedule, and driver assignment"},
    {"name": "vehicle:delete", "resource": "vehicle", "action": "delete", "description": "Decommission fleet vehicles"},
    {"name": "vehicle:manage", "resource": "vehicle", "action": "manage", "description": "Full fleet asset and maintenance lifecycle management"},
    
    {"name": "driver:create", "resource": "driver", "action": "create", "description": "Register new commercial drivers and CDL credentials"},
    {"name": "driver:read", "resource": "driver", "action": "read", "description": "View driver operational profiles and HOS metrics"},
    {"name": "driver:read_all", "resource": "driver", "action": "read_all", "description": "View all drivers across regional terminals"},
    {"name": "driver:read_own", "resource": "driver", "action": "read_own", "description": "View authenticated driver's own profile and duty status"},
    {"name": "driver:update", "resource": "driver", "action": "update", "description": "Update driver status, HOS logs, and vehicle pairing"},
    {"name": "driver:delete", "resource": "driver", "action": "delete", "description": "Deactivate driver operational profiles"},
    {"name": "driver:manage", "resource": "driver", "action": "manage", "description": "Full driver roster, HOS compliance, and safety management"},
    
    {"name": "analytics:read", "resource": "analytics", "action": "read", "description": "Access logistics analytics and KPIs"},
    {"name": "analytics:read_all", "resource": "analytics", "action": "read_all", "description": "Full access to executive, financial, and SLA analytics"},
    {"name": "analytics:read_limited", "resource": "analytics", "action": "read_limited", "description": "Operational dispatcher-level KPIs and telemetry"},
    {"name": "analytics:read_own", "resource": "analytics", "action": "read_own", "description": "Driver performance, HOS, and completion metrics"},
    {"name": "analytics:export", "resource": "analytics", "action": "export", "description": "Export analytics and cost reports to CSV"},
    
    {"name": "ai:use", "resource": "ai", "action": "use", "description": "Interact with LogiAgent AI Assistant and LangGraph agents"},
    {"name": "agent:full_access", "resource": "agent", "action": "full_access", "description": "Unrestricted access to all AI agent logistics tools"},
    {"name": "agent:driver_restricted", "resource": "agent", "action": "driver_restricted", "description": "Driver-scoped restricted AI agent tool access"},
    
    {"name": "documents:read", "resource": "documents", "action": "read", "description": "Query policy documents and standard operating procedures (SOPs)"},
    {"name": "documents:create", "resource": "documents", "action": "create", "description": "Upload new SOP policy documents"},
    {"name": "documents:manage", "resource": "documents", "action": "manage", "description": "Upload, index, and re-vectorize policy documents"},
    {"name": "documents:reindex", "resource": "documents", "action": "reindex", "description": "Trigger full RAG vector store re-indexing"},
    
    {"name": "notifications:read", "resource": "notifications", "action": "read", "description": "View notification alerts"},
    {"name": "notifications:read_all", "resource": "notifications", "action": "read_all", "description": "View all operational and system notifications"},
    {"name": "notifications:read_own", "resource": "notifications", "action": "read_own", "description": "View only assigned notifications"},
    {"name": "notifications:create", "resource": "notifications", "action": "create", "description": "Dispatch operational and driver notifications"},
    
    {"name": "settings:read", "resource": "settings", "action": "read", "description": "View system configuration settings"},
    {"name": "settings:manage", "resource": "settings", "action": "manage", "description": "Configure system-wide parameters and integrations"},
]

# Standard Role Definitions
STANDARD_ROLES = [
    {
        "name": "Admin",
        "description": "Full system governance, security policies, user management, and operational oversight."
    },
    {
        "name": "Logistics Manager",
        "description": "Operations management, fleet scheduling, shipment dispatch, approvals, analytics, and AI tools."
    },
    {
        "name": "Dispatcher",
        "description": "Active shipment scheduling, driver/vehicle assignments, corridor optimization, and live monitoring."
    },
    {
        "name": "Fleet Manager",
        "description": "Vehicle maintenance, asset lifecycle, driver roster governance, capacity, and compliance."
    },
    {
        "name": "Driver",
        "description": "Commercial freight operator with access strictly scoped to assigned shipments, vehicle, and route."
    },
    {
        "name": "Analyst",
        "description": "Read-only access to logistics business intelligence, delay metrics, SLA trends, and cost modeling."
    },
    {
        "name": "Operations Team",
        "description": "Terminal operations personnel with read and operational update capabilities."
    }
]

# ==============================================================================
# Role-Permission Mapping Matrix (Database & Runtime Enforcement)
# ==============================================================================
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "Admin": {
        PERMISSION_USERS_READ,
        PERMISSION_USERS_CREATE,
        PERMISSION_USERS_MANAGE,
        PERMISSION_USERS_APPROVE,
        PERMISSION_USERS_SUSPEND,
        PERMISSION_USERS_DELETE,
        PERMISSION_ROLES_MANAGE,
        PERMISSION_ROLES_READ,
        PERMISSION_SHIPMENTS_CREATE,
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_ALL,
        PERMISSION_SHIPMENTS_READ_OWN,
        PERMISSION_SHIPMENTS_UPDATE,
        PERMISSION_SHIPMENTS_MANAGE,
        PERMISSION_SHIPMENTS_CANCEL,
        PERMISSION_SHIPMENTS_DELETE,
        PERMISSION_VEHICLES_CREATE,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_ALL,
        PERMISSION_VEHICLES_READ_OWN,
        PERMISSION_VEHICLES_UPDATE,
        PERMISSION_VEHICLES_DELETE,
        PERMISSION_VEHICLES_MANAGE,
        PERMISSION_DRIVERS_CREATE,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_ALL,
        PERMISSION_DRIVERS_READ_OWN,
        PERMISSION_DRIVERS_UPDATE,
        PERMISSION_DRIVERS_DELETE,
        PERMISSION_DRIVERS_MANAGE,
        PERMISSION_ROUTES_CREATE,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_ALL,
        PERMISSION_ROUTES_READ_OWN,
        PERMISSION_TELEMETRY_READ,
        PERMISSION_ROUTES_UPDATE,
        PERMISSION_ROUTES_CANCEL,
        PERMISSION_ROUTES_MANAGE,
        PERMISSION_ROUTES_OPTIMIZE,
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_ALL,
        PERMISSION_ANALYTICS_EXPORT,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_DOCUMENTS_CREATE,
        PERMISSION_DOCUMENTS_MANAGE,
        PERMISSION_DOCUMENTS_REINDEX,
        PERMISSION_NOTIFICATIONS_READ,
        PERMISSION_NOTIFICATIONS_READ_ALL,
        PERMISSION_NOTIFICATIONS_CREATE,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_FULL,
        PERMISSION_SETTINGS_MANAGE,
        PERMISSION_SETTINGS_READ,
    },
    "Logistics Manager": {
        PERMISSION_USERS_READ,
        PERMISSION_USERS_CREATE,
        PERMISSION_USERS_MANAGE,
        PERMISSION_USERS_APPROVE,
        PERMISSION_ROLES_READ,
        PERMISSION_SHIPMENTS_CREATE,
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_ALL,
        PERMISSION_SHIPMENTS_READ_OWN,
        PERMISSION_SHIPMENTS_UPDATE,
        PERMISSION_SHIPMENTS_MANAGE,
        PERMISSION_SHIPMENTS_CANCEL,
        PERMISSION_VEHICLES_CREATE,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_ALL,
        PERMISSION_VEHICLES_UPDATE,
        PERMISSION_VEHICLES_MANAGE,
        PERMISSION_DRIVERS_CREATE,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_ALL,
        PERMISSION_DRIVERS_UPDATE,
        PERMISSION_DRIVERS_MANAGE,
        PERMISSION_ROUTES_CREATE,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_ALL,
        PERMISSION_TELEMETRY_READ,
        PERMISSION_ROUTES_UPDATE,
        PERMISSION_ROUTES_CANCEL,
        PERMISSION_ROUTES_MANAGE,
        PERMISSION_ROUTES_OPTIMIZE,
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_ALL,
        PERMISSION_ANALYTICS_EXPORT,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_DOCUMENTS_CREATE,
        PERMISSION_DOCUMENTS_MANAGE,
        PERMISSION_NOTIFICATIONS_READ,
        PERMISSION_NOTIFICATIONS_READ_ALL,
        PERMISSION_NOTIFICATIONS_CREATE,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_FULL,
    },
    "Dispatcher": {
        PERMISSION_SHIPMENTS_CREATE,
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_ALL,
        PERMISSION_SHIPMENTS_READ_OWN,
        PERMISSION_SHIPMENTS_UPDATE,
        PERMISSION_SHIPMENTS_MANAGE,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_ALL,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_ALL,
        PERMISSION_ROUTES_CREATE,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_ALL,
        PERMISSION_TELEMETRY_READ,
        PERMISSION_ROUTES_UPDATE,
        PERMISSION_ROUTES_MANAGE,
        PERMISSION_ROUTES_OPTIMIZE,
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_LIMITED,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_NOTIFICATIONS_READ,
        PERMISSION_NOTIFICATIONS_READ_ALL,
        PERMISSION_NOTIFICATIONS_CREATE,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_FULL,
    },
    "Fleet Manager": {
        PERMISSION_VEHICLES_CREATE,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_ALL,
        PERMISSION_VEHICLES_UPDATE,
        PERMISSION_VEHICLES_DELETE,
        PERMISSION_VEHICLES_MANAGE,
        PERMISSION_DRIVERS_CREATE,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_ALL,
        PERMISSION_DRIVERS_UPDATE,
        PERMISSION_DRIVERS_DELETE,
        PERMISSION_DRIVERS_MANAGE,
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_ALL,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_ALL,
        PERMISSION_TELEMETRY_READ,
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_ALL,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_NOTIFICATIONS_READ,
        PERMISSION_NOTIFICATIONS_READ_ALL,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_FULL,
    },
    "Driver": {
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_OWN,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_OWN,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_OWN,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_OWN,
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_OWN,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_NOTIFICATIONS_READ,
        PERMISSION_NOTIFICATIONS_READ_OWN,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_DRIVER,
    },
    "Analyst": {
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_ALL,
        PERMISSION_ANALYTICS_EXPORT,
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_ALL,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_ALL,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_ALL,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_ALL,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_FULL,
    },
    "Operations Team": {
        PERMISSION_SHIPMENTS_READ,
        PERMISSION_SHIPMENTS_READ_ALL,
        PERMISSION_VEHICLES_READ,
        PERMISSION_VEHICLES_READ_ALL,
        PERMISSION_DRIVERS_READ,
        PERMISSION_DRIVERS_READ_ALL,
        PERMISSION_ROUTES_READ,
        PERMISSION_ROUTES_READ_ALL,
        PERMISSION_ANALYTICS_READ,
        PERMISSION_ANALYTICS_READ_ALL,
        PERMISSION_DOCUMENTS_READ,
        PERMISSION_NOTIFICATIONS_READ,
        PERMISSION_NOTIFICATIONS_READ_ALL,
        PERMISSION_AI_USE,
        PERMISSION_AGENT_FULL,
    }
}

# Add aliasing (e.g. singular "shipment:read" maps to "shipments:read", "user:manage" maps to "users:manage", etc.)
def _normalize_perm_key(p: str) -> str:
    cleaned = p.strip().lower()
    # Normalize resource singular to plural for uniform evaluation
    replacements = [
        ("user:", "users:"),
        ("shipment:", "shipments:"),
        ("route:", "routes:"),
        ("vehicle:", "vehicles:"),
        ("driver:", "drivers:"),
        ("notification:", "notifications:"),
        ("document:", "documents:"),
        ("setting:", "settings:"),
    ]
    for old, new in replacements:
        if cleaned.startswith(old):
            return new + cleaned[len(old):]
    return cleaned

def get_role_permissions(role: str) -> List[str]:
    norm_role = role.strip()
    if norm_role == "Operations Manager":
        norm_role = "Logistics Manager"
    perms = ROLE_PERMISSIONS.get(norm_role, set())
    # Return both original and singular alias forms for robust frontend compatibility
    result_set = set(perms)
    for p in perms:
        if ":" in p:
            res, act = p.split(":", 1)
            if res.endswith("s"):
                result_set.add(f"{res[:-1]}:{act}")
    return sorted(list(result_set))

def has_permission(role: str, permission: str) -> bool:
    if not role:
        return False
    norm_role = role.strip()
    if norm_role == "Admin":
        return True
    if norm_role == "Operations Manager":
        norm_role = "Logistics Manager"

    user_perms = ROLE_PERMISSIONS.get(norm_role, set())
    normalized_target = _normalize_perm_key(permission)
    
    # Telemetry and route telemetry read equivalence
    if normalized_target in ["telemetry:read", "routes:telemetry:read", "route_telemetry:read"]:
        if any(p in user_perms for p in [PERMISSION_TELEMETRY_READ, PERMISSION_ROUTES_READ, PERMISSION_ROUTES_READ_ALL]):
            return True

    for p in user_perms:
        if _normalize_perm_key(p) == normalized_target:
            return True
        # Check wildcard e.g., shipments:manage grants shipments:read, shipments:update
        if ":" in p:
            res, act = p.split(":", 1)
            if act == "manage" and normalized_target.startswith(res + ":"):
                return True
    return False

def get_all_roles() -> List[Dict[str, str]]:
    return STANDARD_ROLES

def get_all_permissions() -> List[Dict[str, str]]:
    return ALL_SYSTEM_PERMISSIONS
