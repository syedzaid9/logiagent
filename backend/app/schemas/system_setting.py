from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class GeneralSettings(BaseModel):
    organization_name: str = Field(default="LogiAgent Global Logistics Inc.", description="Enterprise organization name")
    contact_email: str = Field(default="ops@logiagent.io", description="Primary operations contact email")
    support_phone: str = Field(default="+1 (800) 555-LOGI", description="Operational support telephone number")
    headquarters_address: str = Field(default="100 Logistics Blvd, Suite 400, Chicago, IL 60607", description="HQ address")
    timezone: str = Field(default="America/Chicago (CST)", description="Platform operational timezone")
    date_format: str = Field(default="YYYY-MM-DD", description="Display date format")
    time_format: str = Field(default="24-hour (HH:mm)", description="Display time format (12h/24h)")
    currency: str = Field(default="USD ($)", description="Primary reporting currency")
    distance_unit: str = Field(default="Kilometers (km)", description="Default distance measurement unit")
    weight_unit: str = Field(default="Kilograms (kg)", description="Default cargo weight unit")

class ShipmentSettings(BaseModel):
    auto_assign_driver: bool = Field(default=True, description="Automatically evaluate and suggest optimal driver assignments")
    sla_target_hours: int = Field(default=48, ge=1, le=720, description="Standard SLA transit delivery target in hours")
    critical_delay_threshold_mins: int = Field(default=45, ge=5, le=300, description="Delay duration (minutes) triggering CRITICAL anomaly alert")
    warning_delay_threshold_mins: int = Field(default=20, ge=1, le=180, description="Delay duration (minutes) triggering WARNING alert")
    high_risk_score_threshold: int = Field(default=60, ge=1, le=100, description="ML risk score (0-100) marking shipments as HIGH RISK")
    enable_proof_of_delivery_signature: bool = Field(default=True, description="Enforce digital receiver POD signature for delivery completion")
    auto_calculate_estimated_eta: bool = Field(default=True, description="Recalculate dynamic ETA based on weather and traffic telemetry")
    default_cargo_type: str = Field(default="General Freight", description="Default cargo classification")
    max_cargo_weight_limit_kg: int = Field(default=24000, ge=1000, le=50000, description="Maximum single trailer legal payload weight in kg")

class FleetSettings(BaseModel):
    max_driver_hos_hours: float = Field(default=11.0, ge=1.0, le=16.0, description="Maximum continuous driving hours per DOT HOS regulations")
    min_rest_break_hours: float = Field(default=10.0, ge=4.0, le=24.0, description="Mandatory off-duty rest period between shifts in hours")
    hos_warning_threshold_hours: float = Field(default=2.0, ge=0.5, le=5.0, description="Hours remaining before triggering driver fatigue alerts")
    preventive_maintenance_interval_km: int = Field(default=15000, ge=1000, le=100000, description="Odometer interval for scheduled fleet maintenance inspections")
    maintenance_fuel_threshold_pct: int = Field(default=15, ge=5, le=50, description="Fuel level percentage triggering low fuel depot alerts")
    gps_telemetry_interval_secs: int = Field(default=30, ge=5, le=300, description="Live GPS and OBD-II telemetry broadcast frequency in seconds")
    speed_limit_warning_kmh: int = Field(default=105, ge=60, le=150, description="Highway speed cap triggering carrier safety warnings in km/h")
    enable_hos_violation_alerts: bool = Field(default=True, description="Trigger instant dispatch alerts when driver exceeds duty limits")

class AIRAGSettings(BaseModel):
    vector_similarity_threshold: float = Field(default=0.72, ge=0.4, le=0.99, description="Minimum cosine similarity threshold for RAG semantic chunk retrieval")
    rag_top_k_chunks: int = Field(default=4, ge=1, le=12, description="Maximum number of context chunks passed to LangGraph agent")
    enable_ml_delay_prediction: bool = Field(default=True, description="Enable Random Forest / Gradient Boosting real-time delay probability engine")
    enable_route_optimization_engine: bool = Field(default=True, description="Enable multi-factor Dijkstra & cost optimization algorithms")
    ai_confidence_threshold_pct: int = Field(default=80, ge=50, le=99, description="Confidence threshold percentage required for automated AI actions")
    llm_temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="Model generation temperature (lower = more deterministic)")
    max_tokens_per_interaction: int = Field(default=2048, ge=256, le=8192, description="Maximum LLM tokens per operational query")
    require_human_confirmation_for_dispatch: bool = Field(default=True, description="Enforce human operator sign-off before re-dispatching loads")

class NotificationSettings(BaseModel):
    email_notifications_enabled: bool = Field(default=True, description="Enable automated SMTP/SES email dispatch for high-priority alerts")
    sms_alerts_enabled: bool = Field(default=True, description="Enable Twilio SMS delivery updates to commercial drivers")
    webhook_url: str = Field(default="https://api.logiagent.io/webhooks/exceptions", description="Outbound webhook endpoint for external ERP/TMS systems")
    critical_alert_recipients: str = Field(default="dispatch@logiagent.io, ops-alerts@logiagent.io", description="Comma-separated emails for critical delivery exceptions")
    notify_on_driver_hos_risk: bool = Field(default=True, description="Notify dispatchers when a driver has < 2 hours remaining")
    notify_on_delayed_shipment: bool = Field(default=True, description="Notify dispatchers immediately upon delay threshold breach")
    notify_on_maintenance_due: bool = Field(default=True, description="Notify fleet managers when vehicles approach service intervals")
    digest_frequency: str = Field(default="Real-time", description="Notification batching frequency (Real-time, Hourly, Daily Digest)")

class SecuritySettings(BaseModel):
    session_timeout_minutes: int = Field(default=1440, ge=15, le=10080, description="Bearer JWT access token lifespan in minutes (default: 24h)")
    mfa_enforced_for_admins: bool = Field(default=True, description="Enforce multi-factor authentication for Admin and Logistics Manager roles")
    require_admin_approval_for_new_accounts: bool = Field(default=True, description="Require administrative authorization for self-registered accounts")
    password_min_length: int = Field(default=8, ge=6, le=32, description="Minimum allowed password character length")
    rate_limiting_enabled: bool = Field(default=True, description="Enforce sliding-window IP and token rate limits on API routes")
    jwt_algorithm: str = Field(default="HS256", description="Cryptographic signature algorithm for JSON Web Tokens")
    allowed_cors_origins: str = Field(default="http://localhost:5173, http://127.0.0.1:5173, https://app.logiagent.io", description="Configured CORS origin domains")
    audit_log_retention_days: int = Field(default=90, ge=7, le=365, description="Retention period for security audit logs in days")

class SystemSettingsSchema(BaseModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    shipments: ShipmentSettings = Field(default_factory=ShipmentSettings)
    fleet: FleetSettings = Field(default_factory=FleetSettings)
    ai_rag: AIRAGSettings = Field(default_factory=AIRAGSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

class SystemSettingsResponse(BaseModel):
    settings: SystemSettingsSchema
    last_updated_at: Optional[datetime] = None
    last_updated_by: Optional[str] = None
    environment: str = "production"
    version: str = "1.0.0"

class SystemSettingsUpdateRequest(BaseModel):
    category: Optional[str] = Field(None, description="Optional specific category key to update (e.g. general, shipments, fleet, ai_rag, notifications, security)")
    settings: Dict[str, Any] = Field(..., description="Settings payload dictionary to merge/update")

class SystemSettingsResetRequest(BaseModel):
    category: Optional[str] = Field(None, description="Category to reset to default. If omitted, all categories are reset.")
