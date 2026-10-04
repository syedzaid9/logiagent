export type UserRole = 'Admin' | 'Logistics Manager' | 'Dispatcher' | 'Fleet Manager' | 'Driver' | 'Analyst' | 'Operations Team';
export type AccountStatus = 'Active' | 'Suspended' | 'Deactivated' | 'Pending_Activation';
export type ApprovalStatus = 'Pending_Approval' | 'Approved' | 'Rejected';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  account_status?: AccountStatus;
  approval_status?: ApprovalStatus;
  has_usable_password?: boolean;
  has_activation_token?: boolean;
  driver_id?: number;
  driver_code?: string;
  driver_name?: string;
  driver_phone?: string;
  assigned_vehicle_id?: number;
  assigned_vehicle_code?: string;
  permissions?: string[];
  created_at: string;
  updated_at?: string;
}

export interface RoleInfo {
  id?: number;
  name: string;
  description?: string;
  permissions: string[];
}

export interface PermissionInfo {
  id?: number;
  name: string;
  resource: string;
  action: string;
  description?: string;
}

export interface ApprovalPolicy {
  id: number;
  role: UserRole;
  requires_approval: boolean;
  approver_role: UserRole;
  auto_provision: boolean;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserProvisionPayload {
  email: string;
  full_name: string;
  role: UserRole;
  driver_id?: number;
  require_approval?: boolean;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export interface UserApprovalAction {
  approved: boolean;
  rejection_reason?: string;
  notes?: string;
}

export interface InvitationDetails {
  token: string;
  email: string;
  full_name: string;
  role: UserRole;
  approval_status: ApprovalStatus;
  expires_at: string;
}

export interface DriverPortalData {
  driver: {
    id: number;
    driver_code: string;
    name: string;
    email: string;
    phone: string;
    license_number: string;
    license_type: string;
    status: string;
    rating: number;
    hours_of_service_remaining: number;
  };
  vehicle: {
    id: number;
    vehicle_code: string;
    model: string;
    type: string;
    status: string;
    license_plate: string;
    current_location: string;
    current_load_kg: number;
    max_capacity_kg: number;
    utilization_pct: number;
  } | null;
  kpis: {
    total_assigned: number;
    active_deliveries: number;
    completed_deliveries: number;
    hours_of_service_remaining: number;
    performance_rating: number;
  };
  active_shipments: Array<{
    id: number;
    shipment_code: string;
    status: string;
    cargo_type: string;
    weight_kg: number;
    origin_hub: string;
    estimated_eta: string;
    delay_minutes: number;
    delay_risk_level: string;
  }>;
  active_route: {
    route_code: string;
    planned_distance_km: number;
    planned_duration_min: number;
    traffic_condition: string;
    weather_condition: string;
  } | null;
}

export type ShipmentStatus = 'Pending' | 'Assigned' | 'Picked Up' | 'In Transit' | 'Delayed' | 'Delivered' | 'Failed' | 'Cancelled';

export interface Customer {
  id: number;
  customer_code: string;
  name: string;
  company_name: string;
  email: string;
  tier: string;
}

export interface LocationItem {
  id: number;
  location_code: string;
  name: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  hub_type: string;
}

export interface ShipmentHistory {
  id: number;
  shipment_id: number;
  status: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  notes?: string;
  timestamp: string;
}

export interface Shipment {
  id: number;
  shipment_code: string;
  order_id?: number;
  customer_id: number;
  customer_name?: string;
  origin_id: number;
  origin_name?: string;
  origin_city?: string;
  origin_state?: string;
  destination_id: number;
  destination_name?: string;
  destination_city?: string;
  destination_state?: string;
  vehicle_id?: number;
  vehicle_code?: string;
  driver_id?: number;
  driver_name?: string;
  status: ShipmentStatus;
  cargo_type: string;
  weight_kg: number;
  volume_m3?: number;
  temperature_controlled?: boolean;
  target_temp_celsius?: number;
  current_latitude?: number;
  current_longitude?: number;
  current_location_name?: string;
  pickup_time?: string;
  expected_delivery: string;
  actual_delivery?: string;
  estimated_eta?: string;
  delay_minutes: number;
  delay_reason?: string;
  delay_risk_score: number;
  delay_risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  special_instructions?: string;
  cost_total_usd?: number;
  cost_breakdown?: Record<string, any>;
  history?: ShipmentHistory[];
  created_at: string;
  updated_at: string;
}

export interface Vehicle {
  id: number;
  vehicle_code: string;
  model: string;
  type: string;
  max_capacity_kg: number;
  current_load_kg: number;
  max_volume_m3: number;
  current_volume_m3: number;
  status: 'Available' | 'Assigned' | 'In Transit' | 'Maintenance' | 'Deactivated';
  current_location: string;
  latitude: number;
  longitude: number;
  fuel_level_pct: number;
  fuel_type: string;
  mileage_km: number;
  driver_id?: number;
  driver_name?: string;
  driver_code?: string;
  driver_phone?: string;
  active_shipment_code?: string;
  active_shipment_id?: number;
  active_shipment_status?: string;
  active_shipment_weight_kg?: number;
  origin_hub?: string;
  destination_hub?: string;
  available_capacity_kg?: number;
  available_volume_m3?: number;
  utilization_pct: number;
  updated_at: string;
}

export interface FleetStats {
  total_vehicles: number;
  available_vehicles: number;
  assigned_vehicles: number;
  in_transit_vehicles: number;
  maintenance_vehicles: number;
  average_utilization_pct: number;
  total_fleet_capacity_kg: number;
  total_fleet_load_kg: number;
}

export interface DriverStats {
  total_drivers: number;
  available_drivers: number;
  assigned_drivers: number;
  on_duty_drivers: number;
  off_duty_drivers: number;
  rest_drivers: number;
  deactivated_drivers: number;
  average_hos_remaining: number;
  average_rating: number;
  drivers_with_active_shipments: number;
}

export interface Driver {
  id: number;
  driver_code: string;
  name: string;
  email: string;
  phone: string;
  license_number: string;
  license_type: string;
  status: 'Available' | 'Assigned' | 'On Duty' | 'Off Duty' | 'Rest' | 'Deactivated';
  rating: number;
  hours_of_service_remaining: number;
  current_vehicle_id?: number;
  assigned_vehicle_code?: string;
  assigned_vehicle_model?: string;
  assigned_vehicle_type?: string;
  assigned_vehicle_location?: string;
  active_shipment_code?: string;
  active_shipment_id?: number;
  active_shipment_status?: string;
  active_shipment_origin?: string;
  active_shipment_destination?: string;
  active_shipment_weight_kg?: number;
  completed_deliveries_count?: number;
  active_deliveries_count?: number;
  hos_compliance_status?: string;
  created_at: string;
}

export interface Waypoint {
  name: string;
  location: string;
  lat: number;
  lng: number;
  type: string;
}

export interface RouteDetail {
  corridor: string;
  distance_km: number;
  duration_minutes: number;
  duration_formatted: string;
  traffic_condition: string;
  weather_condition: string;
  estimated_cost_usd: number;
  cost_per_km: number;
}

export interface RouteItem {
  id: number;
  route_code: string;
  shipment_id?: number;
  shipment_code?: string;
  customer_name?: string;
  origin_id: number;
  origin_name?: string;
  origin_city?: string;
  origin_state?: string;
  origin_latitude?: number;
  origin_longitude?: number;
  destination_id: number;
  destination_name?: string;
  destination_city?: string;
  destination_state?: string;
  destination_latitude?: number;
  destination_longitude?: number;
  vehicle_id?: number;
  vehicle_code?: string;
  vehicle_type?: string;
  driver_id?: number;
  driver_name?: string;
  driver_code?: string;
  planned_distance_km: number;
  planned_duration_min: number;
  actual_duration_min?: number;
  traffic_condition: string;
  weather_condition: string;
  status: 'Planned' | 'Assigned' | 'In Transit' | 'Delayed' | 'Completed' | 'Cancelled';
  cost_total_usd?: number;
  eta_timestamp?: string;
  route_efficiency_pct?: number;
  waypoints?: Waypoint[];
  polyline?: [number, number][];
  created_at?: string;
  updated_at?: string;
}

export interface RouteStats {
  total_routes: number;
  active_routes: number;
  planned_routes: number;
  completed_routes: number;
  delayed_routes: number;
  average_distance_km: number;
  average_duration_min: number;
  average_efficiency_pct: number;
}

export interface RouteOptimizeCandidate {
  corridor: string;
  distance_km: number;
  duration_minutes: number;
  duration_formatted: string;
  traffic_condition: string;
  weather_condition?: string;
  estimated_cost_usd: number;
  cost_per_km?: number;
}

export interface RouteOptimizeResult {
  success: boolean;
  route_code?: string;
  shipment_code?: string;
  origin: string;
  destination: string;
  recommended_priority: string;
  recommended_route: RouteOptimizeCandidate;
  alternative_routes: RouteOptimizeCandidate[];
  stops: Waypoint[];
  polyline_coordinates: [number, number][];
  recommendation_summary: string;
  persisted_route?: RouteItem;
}

export interface RouteData {
  success: boolean;
  shipment_code?: string;
  origin: string;
  destination: string;
  recommended_priority: string;
  recommended_route: RouteDetail;
  alternative_routes?: any[];
  stops: Waypoint[];
  polyline_coordinates: [number, number][];
  recommendation_summary: string;
}

export interface KPISummary {
  total_shipments: number;
  in_transit_shipments: number;
  delivered_shipments: number;
  delayed_shipments: number;
  cancelled_shipments?: number;
  pending_shipments?: number;
  at_risk_shipments: number;
  on_time_delivery_rate_pct: number;
  average_delivery_hours?: number;
  average_delay_minutes?: number;
  max_delay_minutes?: number;
  today_deliveries_count: number;
  average_eta_hours: number;
  total_vehicles: number;
  active_vehicles: number;
  available_vehicles: number;
  fleet_utilization_pct: number;
  total_drivers?: number;
  active_drivers?: number;
  available_drivers?: number;
  driver_average_rating?: number;
  driver_average_hos_remaining?: number;
  total_routes?: number;
  active_routes?: number;
  completed_routes?: number;
  average_route_distance_km?: number;
  average_route_duration_min?: number;
  total_transportation_cost: number;
  total_cost?: number;
  average_cost_per_shipment?: number;
  average_cost_per_km?: number;
}

export interface OperationalInsightItem {
  id: string;
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'INFO' | 'LOW';
  title: string;
  explanation: string;
  metric_name: string;
  metric_value: number;
  threshold: number;
  related_records: string[];
  recommended_action: string;
  generated_at: string;
}

export interface CorridorEfficiencyItem {
  route_code: string;
  corridor: string;
  distance_km: number;
  duration_min: number;
  traffic: string;
  weather: string;
  cost_usd: number;
  cost_per_km: number;
  status: string;
}

export interface CustomerAnalyticsItem {
  customer_id: number;
  customer_code: string;
  name: string;
  company_name: string;
  tier: string;
  total_shipments: number;
  delivered_count: number;
  delayed_count: number;
  on_time_rate_pct: number;
  total_spend_usd: number;
}

export interface AnalyticsDashboard {
  time_range?: string;
  start_date?: string;
  end_date?: string;
  user_role?: string;
  kpis: KPISummary;
  status_distribution: { status: string; count: number; percentage: number }[];
  vehicle_utilization: { vehicle_type: string; total_count: number; active_count: number; average_load_pct: number }[];
  delay_root_causes: { reason: string; count: number; percentage: number }[];
  delay_duration_distribution?: { bracket: string; count: number }[];
  cost_breakdown: { category: string; amount: number; percentage: number }[];
  corridor_efficiency?: CorridorEfficiencyItem[];
  customer_analytics?: CustomerAnalyticsItem[];
  operational_insights?: OperationalInsightItem[];
  trend_and_forecast_assessment?: {
    forecasting_status: string;
    is_available: boolean;
    distinct_historical_days: number;
    sample_size: number;
    message: string;
    historical_trend?: {
      direction: string;
      percentage_change: number;
      summary: string;
    };
  };
  demand_forecast?: { date: string; day_name: string; predicted_shipments: number; lower_bound: number; upper_bound: number; expected_fleet_required: number }[];
  recent_activity: { id: number; shipment_id: number; status: string; location: string; notes: string; time_ago: string; timestamp?: string }[];
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: 'delay' | 'eta_change' | 'route_deviation' | 'delivery_failure' | 'critical_event';
  channel: string;
  recipient: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'unread' | 'read' | 'sent';
  shipment_id?: number;
  created_at: string;
}

export interface RAGSource {
  title: string;
  document_code: string;
  category: string;
  snippet: string;
}

export interface ToolCallDetail {
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output: any;
  success: boolean;
}

export interface AgentChatResponse {
  conversation_id: string;
  user_query: string;
  response: string;
  actions_performed: string[];
  tools_used: string[];
  tool_calls: ToolCallDetail[];
  structured_data?: Record<string, any>;
  sources: RAGSource[];
  latency_ms: number;
}

export interface SuggestedPrompt {
  label: string;
  query: string;
  category: string;
}

export interface AgentCapabilitiesResponse {
  role: string;
  user_name: string;
  user_email: string;
  permissions: string[];
  allowed_tools: string[];
  allowed_document_categories: string[];
  operational_scope: Record<string, any>;
  suggested_prompts: SuggestedPrompt[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  actions_performed?: string[];
  tools_used?: string[];
  tool_calls?: ToolCallDetail[];
  structured_data?: Record<string, any>;
  sources?: RAGSource[];
  latency_ms?: number;
  isError?: boolean;
  queryForRetry?: string;
  timestamp: string;
}

export interface AlertItem {
  id: number;
  alert_code: string;
  alert_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  entity_type: string;
  entity_id: string;
  title: string;
  message: string;
  evidence?: string;
  recommended_action?: string;
  status: 'active' | 'acknowledged' | 'resolved' | string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface AIRecommendationItem {
  id: string;
  priority: string;
  category: string;
  entity_type: string;
  entity_code: string;
  problem: string;
  evidence: string[];
  recommended_action: string;
  requires_human_confirmation: boolean;
  action_type: string;
  action_payload: Record<string, any>;
  expected_effect: string;
}

export interface OperationalSummaryResponse {
  total_active_shipments: number;
  high_risk_shipments_count: number;
  active_alerts_count: number;
  critical_alerts_count: number;
  fleet_utilization_pct: number;
  risk_distribution: Record<string, number>;
  top_recommendations: AIRecommendationItem[];
}

export interface ShipmentRiskResponse {
  shipment_id?: number;
  shipment_code: string;
  prediction_status: string;
  status?: string;
  origin?: string;
  destination?: string;
  risk_level: string;
  risk_score: number;
  delay_probability: number;
  predicted_delay_minutes: number;
  predicted_eta?: string;
  formatted_eta?: string;
  deadline_eta?: string;
  is_deadline_at_risk: boolean;
  traffic_condition?: string;
  weather_condition?: string;
  driver_name?: string;
  vehicle_code?: string;
  risk_factors: { factor: string; impact: string; detail: string }[];
  recommended_actions?: { priority: string; action: string; requires_confirmation: boolean }[];
  error?: string;
}

export interface GeneralSettings {
  organization_name: string;
  contact_email: string;
  support_phone: string;
  headquarters_address: string;
  timezone: string;
  date_format: string;
  time_format: string;
  currency: string;
  distance_unit: string;
  weight_unit: string;
}

export interface ShipmentSettings {
  auto_assign_driver: boolean;
  sla_target_hours: number;
  critical_delay_threshold_mins: number;
  warning_delay_threshold_mins: number;
  high_risk_score_threshold: number;
  enable_proof_of_delivery_signature: boolean;
  auto_calculate_estimated_eta: boolean;
  default_cargo_type: string;
  max_cargo_weight_limit_kg: number;
}

export interface FleetSettings {
  max_driver_hos_hours: number;
  min_rest_break_hours: number;
  hos_warning_threshold_hours: number;
  preventive_maintenance_interval_km: number;
  maintenance_fuel_threshold_pct: number;
  gps_telemetry_interval_secs: number;
  speed_limit_warning_kmh: number;
  enable_hos_violation_alerts: boolean;
}

export interface AIRAGSettings {
  vector_similarity_threshold: number;
  rag_top_k_chunks: number;
  enable_ml_delay_prediction: boolean;
  enable_route_optimization_engine: boolean;
  ai_confidence_threshold_pct: number;
  llm_temperature: number;
  max_tokens_per_interaction: number;
  require_human_confirmation_for_dispatch: boolean;
}

export interface NotificationSettings {
  email_notifications_enabled: boolean;
  sms_alerts_enabled: boolean;
  webhook_url: string;
  critical_alert_recipients: string;
  notify_on_driver_hos_risk: boolean;
  notify_on_delayed_shipment: boolean;
  notify_on_maintenance_due: boolean;
  digest_frequency: string;
}

export interface SecuritySettings {
  session_timeout_minutes: number;
  mfa_enforced_for_admins: boolean;
  require_admin_approval_for_new_accounts: boolean;
  password_min_length: number;
  rate_limiting_enabled: boolean;
  jwt_algorithm: string;
  allowed_cors_origins: string;
  audit_log_retention_days: number;
}

export interface SystemSettingsSchema {
  general: GeneralSettings;
  shipments: ShipmentSettings;
  fleet: FleetSettings;
  ai_rag: AIRAGSettings;
  notifications: NotificationSettings;
  security: SecuritySettings;
}

export interface SystemSettingsResponse {
  settings: SystemSettingsSchema;
  last_updated_at?: string;
  last_updated_by?: string;
  environment: string;
  version: string;
}


