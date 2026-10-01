import { apiRequest } from './client';
import {
  Shipment,
  Vehicle,
  Driver,
  DriverStats,
  RouteData,
  RouteItem,
  RouteStats,
  RouteOptimizeResult,
  AnalyticsDashboard,
  NotificationItem,
  AgentChatResponse,
  AgentCapabilitiesResponse,
  User,
  AlertItem,
  OperationalSummaryResponse,
  ShipmentRiskResponse,
  AIRecommendationItem,
  SystemSettingsResponse,
} from '../types';


export const api = {
  // Auth
  login: async (email: string, password: string) => {
    return apiRequest<{ access_token: string; token_type: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  register: async (data: { email: string; password: string; full_name: string; role?: string }) => {
    return apiRequest<{ access_token: string; token_type: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  getMe: async () => {
    return apiRequest<User>('/auth/me');
  },
  logout: async () => {
    return apiRequest<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  },
  getInvitation: async (token: string) => {
    return apiRequest<any>(`/auth/invitation/${encodeURIComponent(token)}`);
  },
  acceptInvitation: async (token: string, data: { full_name?: string; password: string }) => {
    return apiRequest<any>(`/auth/accept-invitation?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // User & Account Management (RBAC & Approvals)
  getUsers: async (params?: { role?: string; status?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.role) query.append('role', params.role);
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    return apiRequest<User[]>(`/users?${query.toString()}`);
  },
  provisionUser: async (data: { email: string; full_name: string; role: string; driver_id?: number; require_approval?: boolean }) => {
    return apiRequest<{ message: string; user: User; activation_token?: string; invitation_url?: string }>('/users/provision', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  approveUser: async (id: number, notes?: string) => {
    return apiRequest<{ message: string; user: User }>(`/users/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  },
  rejectUser: async (id: number, rejection_reason: string) => {
    return apiRequest<{ message: string; user: User }>(`/users/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejection_reason }),
    });
  },
  suspendUser: async (id: number, reason?: string) => {
    return apiRequest<{ message: string; user: User }>(`/users/${id}/suspend`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },
  activateUser: async (id: number) => {
    return apiRequest<{ message: string; user: User }>(`/users/${id}/activate`, {
      method: 'POST',
    });
  },
  getApprovalPolicies: async () => {
    return apiRequest<any[]>('/users/policies');
  },
  getRoles: async () => {
    return apiRequest<any[]>('/users/roles');
  },
  getPermissions: async () => {
    return apiRequest<any[]>('/users/permissions');
  },

  // Driver Portal Scoped Data
  getDriverPortal: async () => {
    return apiRequest<any>('/analytics/driver-portal');
  },

  // Shipments
  getShipments: async (params?: { status?: string; search?: string; delayed_only?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    if (params?.delayed_only) query.append('delayed_only', 'true');
    return apiRequest<Shipment[]>(`/shipments?${query.toString()}`);
  },
  getShipment: async (code: string) => {
    return apiRequest<Shipment>(`/shipments/${encodeURIComponent(code)}`);
  },
  createShipment: async (data: any) => {
    return apiRequest<Shipment>('/shipments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateShipment: async (code: string, data: Partial<Shipment> & { notes?: string }) => {
    return apiRequest<Shipment>(`/shipments/${encodeURIComponent(code)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  cancelShipment: async (code: string) => {
    return apiRequest<{ success: boolean; message: string; shipment: Shipment }>(`/shipments/${encodeURIComponent(code)}`, {
      method: 'DELETE',
    });
  },
  getCustomers: async () => {
    return apiRequest<any[]>('/shipments/meta/customers');
  },

  // Vehicles
  getVehicles: async (params?: { status?: string; vehicle_type?: string; search?: string; min_capacity_kg?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.vehicle_type) query.append('vehicle_type', params.vehicle_type);
    if (params?.search) query.append('search', params.search);
    if (params?.min_capacity_kg) query.append('min_capacity_kg', params.min_capacity_kg.toString());
    return apiRequest<Vehicle[]>(`/vehicles?${query.toString()}`);
  },
  getVehicle: async (code: string) => {
    return apiRequest<Vehicle>(`/vehicles/${encodeURIComponent(code)}`);
  },
  getFleetStats: async () => {
    return apiRequest<any>('/vehicles/stats');
  },
  createVehicle: async (data: any) => {
    return apiRequest<Vehicle>('/vehicles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateVehicle: async (code: string, data: Partial<Vehicle>) => {
    return apiRequest<Vehicle>(`/vehicles/${encodeURIComponent(code)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  deactivateVehicle: async (code: string) => {
    return apiRequest<{ success: boolean; message: string; vehicle: Vehicle }>(`/vehicles/${encodeURIComponent(code)}`, {
      method: 'DELETE',
    });
  },

  // Drivers
  getDrivers: async (params?: { status?: string; license_type?: string; min_hos?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.license_type) query.append('license_type', params.license_type);
    if (params?.min_hos) query.append('min_hos', params.min_hos.toString());
    if (params?.search) query.append('search', params.search);
    return apiRequest<Driver[]>(`/drivers?${query.toString()}`);
  },
  getDriver: async (code: string) => {
    return apiRequest<Driver>(`/drivers/${encodeURIComponent(code)}`);
  },
  getDriverStats: async () => {
    return apiRequest<DriverStats>('/drivers/stats');
  },
  createDriver: async (data: any) => {
    return apiRequest<Driver>('/drivers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateDriver: async (code: string, data: Partial<Driver>) => {
    return apiRequest<Driver>(`/drivers/${encodeURIComponent(code)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  deactivateDriver: async (code: string) => {
    return apiRequest<{ success: boolean; message: string; driver: Driver }>(`/drivers/${encodeURIComponent(code)}`, {
      method: 'DELETE',
    });
  },

  // Routes
  getRoutes: async (params?: { status?: string; vehicle_id?: number; driver_id?: number; shipment_id?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.vehicle_id) query.append('vehicle_id', params.vehicle_id.toString());
    if (params?.driver_id) query.append('driver_id', params.driver_id.toString());
    if (params?.shipment_id) query.append('shipment_id', params.shipment_id.toString());
    if (params?.search) query.append('search', params.search);
    return apiRequest<RouteItem[]>(`/routes?${query.toString()}`);
  },
  getRoute: async (code: string) => {
    return apiRequest<RouteItem>(`/routes/${encodeURIComponent(code)}`);
  },
  getRouteStats: async () => {
    return apiRequest<RouteStats>('/routes/stats');
  },
  createRoute: async (data: any) => {
    return apiRequest<RouteItem>('/routes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateRoute: async (code: string, data: any) => {
    return apiRequest<RouteItem>(`/routes/${encodeURIComponent(code)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  deactivateRoute: async (code: string) => {
    return apiRequest<{ success: boolean; message: string; route: RouteItem }>(`/routes/${encodeURIComponent(code)}`, {
      method: 'DELETE',
    });
  },
  optimizeRoute: async (data: { route_code?: string; shipment_code?: string; origin_id?: number; destination_id?: number; priority?: string; persist?: boolean }) => {
    return apiRequest<RouteOptimizeResult>('/routes/optimize', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  getRouteForShipment: async (shipmentCode: string) => {
    return apiRequest<RouteData>(`/routes/shipment/${encodeURIComponent(shipmentCode)}`);
  },
  calculateRoute: async (originId: number, destinationId: number, priority = 'fastest') => {
    return apiRequest<RouteData>('/routes/calculate', {
      method: 'POST',
      body: JSON.stringify({ origin_id: originId, destination_id: destinationId, priority }),
    });
  },
  getLocations: async () => {
    return apiRequest<any[]>('/routes/locations');
  },

  // Analytics
  getAnalytics: async (params?: {
    time_range?: string;
    start_date?: string;
    end_date?: string;
    status?: string;
    vehicle_id?: number;
    driver_id?: number;
    customer_id?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.time_range) query.append('time_range', params.time_range);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.status) query.append('status', params.status);
    if (params?.vehicle_id) query.append('vehicle_id', params.vehicle_id.toString());
    if (params?.driver_id) query.append('driver_id', params.driver_id.toString());
    if (params?.customer_id) query.append('customer_id', params.customer_id.toString());
    return apiRequest<AnalyticsDashboard>(`/analytics/dashboard?${query.toString()}`);
  },
  getAnalyticsInsights: async () => {
    return apiRequest<{ insights: any[]; total_insights: number }>('/analytics/insights');
  },

  // Notifications
  getNotifications: async () => {
    return apiRequest<NotificationItem[]>('/notifications');
  },
  markNotificationAsRead: async (id: number) => {
    return apiRequest<NotificationItem>(`/notifications/${id}/read`, {
      method: 'PUT',
    });
  },

  // RAG
  queryRAG: async (query: string) => {
    return apiRequest<any>('/rag/query', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: 4 }),
    });
  },
  getRAGDocuments: async () => {
    return apiRequest<any[]>('/rag/documents');
  },

  // AI Agent
  getAgentCapabilities: async () => {
    return apiRequest<AgentCapabilitiesResponse>('/agent/capabilities');
  },
  chatWithAgent: async (message: string, role = 'Logistics Manager', conversationId?: string) => {
    return apiRequest<AgentChatResponse>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, user_role: role, conversation_id: conversationId }),
    });
  },

  // Logistics Intelligence & AI Operations (Phase 11)
  getAiAlerts: async (params?: { status?: string; severity?: string; entity_type?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.severity) query.append('severity', params.severity);
    if (params?.entity_type) query.append('entity_type', params.entity_type);
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.offset) query.append('offset', params.offset.toString());
    return apiRequest<AlertItem[]>(`/ai/alerts?${query.toString()}`);
  },
  triggerAnomalyScan: async () => {
    return apiRequest<any>('/ai/alerts/scan', {
      method: 'POST',
    });
  },
  acknowledgeAiAlert: async (alertId: number, notes?: string) => {
    return apiRequest<AlertItem>(`/ai/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  },
  resolveAiAlert: async (alertId: number, resolution_summary?: string) => {
    return apiRequest<AlertItem>(`/ai/alerts/${alertId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_summary }),
    });
  },
  getOperationalSummary: async () => {
    return apiRequest<OperationalSummaryResponse>('/ai/operations/summary');
  },
  getShipmentRisk: async (shipmentCode: string) => {
    return apiRequest<ShipmentRiskResponse>(`/ai/shipments/${encodeURIComponent(shipmentCode)}/risk`);
  },
  getRouteAnalysis: async (routeCode: string) => {
    return apiRequest<any>(`/ai/routes/${encodeURIComponent(routeCode)}/analysis`);
  },
  getAiRecommendations: async (limit = 10) => {
    return apiRequest<AIRecommendationItem[]>(`/ai/recommendations?limit=${limit}`);
  },

  // System Settings & Operations Configuration
  getSettings: async () => {
    return apiRequest<SystemSettingsResponse>('/settings');
  },
  updateSettings: async (data: { category?: string; settings: Record<string, any> }) => {
    return apiRequest<SystemSettingsResponse>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  resetSettings: async (category?: string) => {
    return apiRequest<SystemSettingsResponse>('/settings/reset', {
      method: 'POST',
      body: JSON.stringify(category ? { category } : {}),
    });
  },
};

