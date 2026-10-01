import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import {
  SystemSettingsSchema,
  SystemSettingsResponse,
  GeneralSettings,
  ShipmentSettings,
  FleetSettings,
  AIRAGSettings,
  NotificationSettings,
  SecuritySettings
} from '../../types';
import { PageHeader } from '../common/PageHeader';
import { ConfirmationDialog } from '../common/ConfirmationDialog';
import {
  Settings,
  Building2,
  Package,
  Truck,
  Sparkles,
  Bell,
  ShieldCheck,
  Save,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Globe,
  Clock,
  MapPin,
  Scale,
  Gauge,
  Brain,
  Sliders,
  Radio,
  FileCode,
  Check,
  Info,
  Server,
  KeyRound,
  ShieldAlert
} from 'lucide-react';

interface SystemSettingsViewProps {
  onNavigate?: (tab: string) => void;
}

type TabKey = 'general' | 'shipments' | 'fleet' | 'ai_rag' | 'notifications' | 'security';

export const SystemSettingsView: React.FC<SystemSettingsViewProps> = ({ onNavigate }) => {
  const { role, hasPermission } = useAuth();
  const isAdmin = role === 'Admin' || hasPermission('settings:manage');

  const [activeTab, setActiveTab] = useState<TabKey>('general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Original and working state
  const [originalData, setOriginalData] = useState<SystemSettingsResponse | null>(null);
  const [formData, setFormData] = useState<SystemSettingsSchema>({
    general: {
      organization_name: 'LogiAgent Global Logistics Inc.',
      contact_email: 'ops@logiagent.io',
      support_phone: '+1 (800) 555-LOGI',
      headquarters_address: '100 Logistics Blvd, Suite 400, Chicago, IL 60607',
      timezone: 'America/Chicago (CST)',
      date_format: 'YYYY-MM-DD',
      time_format: '24-hour (HH:mm)',
      currency: 'USD ($)',
      distance_unit: 'Kilometers (km)',
      weight_unit: 'Kilograms (kg)',
    },
    shipments: {
      auto_assign_driver: true,
      sla_target_hours: 48,
      critical_delay_threshold_mins: 45,
      warning_delay_threshold_mins: 20,
      high_risk_score_threshold: 60,
      enable_proof_of_delivery_signature: true,
      auto_calculate_estimated_eta: true,
      default_cargo_type: 'General Freight',
      max_cargo_weight_limit_kg: 24000,
    },
    fleet: {
      max_driver_hos_hours: 11.0,
      min_rest_break_hours: 10.0,
      hos_warning_threshold_hours: 2.0,
      preventive_maintenance_interval_km: 15000,
      maintenance_fuel_threshold_pct: 15,
      gps_telemetry_interval_secs: 30,
      speed_limit_warning_kmh: 105,
      enable_hos_violation_alerts: true,
    },
    ai_rag: {
      vector_similarity_threshold: 0.72,
      rag_top_k_chunks: 4,
      enable_ml_delay_prediction: true,
      enable_route_optimization_engine: true,
      ai_confidence_threshold_pct: 80,
      llm_temperature: 0.2,
      max_tokens_per_interaction: 2048,
      require_human_confirmation_for_dispatch: true,
    },
    notifications: {
      email_notifications_enabled: true,
      sms_alerts_enabled: true,
      webhook_url: 'https://api.logiagent.io/webhooks/exceptions',
      critical_alert_recipients: 'dispatch@logiagent.io, ops-alerts@logiagent.io',
      notify_on_driver_hos_risk: true,
      notify_on_delayed_shipment: true,
      notify_on_maintenance_due: true,
      digest_frequency: 'Real-time',
    },
    security: {
      session_timeout_minutes: 1440,
      mfa_enforced_for_admins: true,
      require_admin_approval_for_new_accounts: true,
      password_min_length: 8,
      rate_limiting_enabled: true,
      jwt_algorithm: 'HS256',
      allowed_cors_origins: 'http://localhost:5173, http://127.0.0.1:5173, https://app.logiagent.io',
      audit_log_retention_days: 90,
    },
  });

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showResetConfirmModal, setShowResetConfirmModal] = useState(false);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await api.getSettings();
      setOriginalData(res);
      setFormData(res.settings);
      setHasUnsavedChanges(false);
    } catch (err: any) {
      console.error('Failed to load system settings:', err);
      setErrorMsg(err.message || 'Unable to retrieve settings from the database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleFieldChange = (category: TabKey, key: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
    setHasUnsavedChanges(true);
  };

  const handleSaveCategory = async () => {
    if (!isAdmin) {
      alert('Only administrators with settings:manage permission can modify system parameters.');
      return;
    }

    try {
      setSaving(true);
      setErrorMsg(null);

      const res = await api.updateSettings({
        category: activeTab,
        settings: formData[activeTab],
      });

      setOriginalData(res);
      setFormData(res.settings);
      setHasUnsavedChanges(false);
      setSuccessToast(`Successfully updated ${getTabTitle(activeTab)} configuration settings.`);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      console.error('Failed to save settings:', err);
      setErrorMsg(err.message || 'Error occurred while persisting settings to database.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAll = async () => {
    if (!isAdmin) {
      alert('Only administrators with settings:manage permission can modify system parameters.');
      return;
    }

    try {
      setSaving(true);
      setErrorMsg(null);

      const res = await api.updateSettings({
        settings: formData,
      });

      setOriginalData(res);
      setFormData(res.settings);
      setHasUnsavedChanges(false);
      setSuccessToast('All platform system settings have been saved and applied.');
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      console.error('Failed to save all settings:', err);
      setErrorMsg(err.message || 'Error occurred while saving settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleResetConfirmed = async () => {
    try {
      setResetting(true);
      setShowResetConfirmModal(false);
      const res = await api.resetSettings(activeTab);
      setOriginalData(res);
      setFormData(res.settings);
      setHasUnsavedChanges(false);
      setSuccessToast(`Reset ${getTabTitle(activeTab)} settings to standard default parameters.`);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      console.error('Failed to reset settings:', err);
      setErrorMsg(err.message || 'Failed to reset settings category.');
    } finally {
      setResetting(false);
    }
  };

  const handleDiscardChanges = () => {
    if (originalData) {
      setFormData(originalData.settings);
      setHasUnsavedChanges(false);
    }
  };

  const getTabTitle = (tab: TabKey) => {
    switch (tab) {
      case 'general':
        return 'General / Operations';
      case 'shipments':
        return 'Shipment & Operations';
      case 'fleet':
        return 'Fleet & Driver';
      case 'ai_rag':
        return 'AI & RAG Intelligence';
      case 'notifications':
        return 'Notifications & Alerts';
      case 'security':
        return 'Security & RBAC';
    }
  };

  const tabs: { id: TabKey; label: string; icon: any; desc: string }[] = [
    {
      id: 'general',
      label: 'General / Operations',
      icon: Building2,
      desc: 'Organization profile, timezones, and units',
    },
    {
      id: 'shipments',
      label: 'Shipment & Operations',
      icon: Package,
      desc: 'SLA benchmarks, delay triggers, and POD',
    },
    {
      id: 'fleet',
      label: 'Fleet & Driver',
      icon: Truck,
      desc: 'DOT HOS limits, maintenance, and GPS telemetry',
    },
    {
      id: 'ai_rag',
      label: 'AI & RAG',
      icon: Brain,
      desc: 'pgvector similarity, token limits, and delay ML',
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: Bell,
      desc: 'Alert webhooks, email/SMS, and digest rules',
    },
    {
      id: 'security',
      label: 'Security & RBAC',
      icon: ShieldCheck,
      desc: 'JWT sessions, CORS origins, and governance',
    },
  ];

  if (loading && !originalData) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-white rounded-xl border border-slate-200" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="h-96 bg-white rounded-xl border border-slate-200" />
          <div className="md:col-span-3 h-96 bg-white rounded-xl border border-slate-200" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-200 pb-16">
      {/* 1. Header Banner */}
      <PageHeader
        title="LogiAgent Enterprise System Settings"
        subtitle="Configure operational thresholds, carrier SLA targets, pgvector similarity limits, and automated notification webhook endpoints."
        icon={Settings}
        badge="ADMIN GOVERNANCE"
        badgeColor="bg-blue-50 text-blue-700 border-blue-200"
        onRefresh={loadSettings}
        isRefreshing={loading}
        actions={
          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 flex items-center gap-1.5 animate-pulse">
                <AlertTriangle className="w-3 h-3 text-amber-600" />
                <span>Unsaved Changes</span>
              </span>
            )}
            <button
              onClick={handleSaveAll}
              disabled={saving || !isAdmin}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
            >
              {saving ? (
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              <span>Save All Settings</span>
            </button>
          </div>
        }
      />

      {/* Toast Messages */}
      {successToast && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-2xs animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successToast}</span>
          </div>
          <button onClick={() => setSuccessToast(null)} className="text-emerald-700 hover:text-emerald-900">
            &times;
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex items-center justify-between shadow-2xs animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-700 hover:text-rose-900">
            &times;
          </button>
        </div>
      )}

      {/* Main Settings Grid: Left Nav + Right Form */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Side Navigation */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white border border-slate-200/90 rounded-xl p-3 shadow-2xs space-y-1">
            <div className="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Configuration Domains
            </div>
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-start gap-3 p-2.5 rounded-lg text-left transition-all cursor-pointer ${
                    isActive
                      ? 'bg-blue-50/80 border border-blue-200 text-blue-700 shadow-2xs'
                      : 'hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent'
                  }`}
                >
                  <div className={`p-1.5 rounded-md mt-0.5 shrink-0 ${
                    isActive ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'
                  }`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <div className={`text-xs font-bold ${isActive ? 'text-blue-900' : 'text-slate-800'}`}>
                      {tab.label}
                    </div>
                    <div className="text-[11px] text-slate-500 truncate mt-0.5">
                      {tab.desc}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Audit Metadata Card */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs space-y-2 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-slate-800 pb-2 border-b border-slate-100">
              <Server className="w-3.5 h-3.5 text-blue-600" />
              <span>Platform Metadata</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>Environment:</span>
              <span className="font-mono font-semibold text-slate-800 uppercase">{originalData?.environment || 'Production'}</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>Version:</span>
              <span className="font-mono text-slate-800">v{originalData?.version || '1.0.0'}</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>Last Modified By:</span>
              <span className="font-medium text-slate-800 truncate max-w-[130px]">{originalData?.last_updated_by || 'Admin'}</span>
            </div>
            {originalData?.last_updated_at && (
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span>Last Updated:</span>
                <span className="font-mono text-slate-600">
                  {new Date(originalData.last_updated_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side Settings Panels */}
        <div className="lg:col-span-3 space-y-6">
          {/* SECTION 1: GENERAL / OPERATIONS */}
          {activeTab === 'general' && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-blue-600" />
                    <span>General & Operational Defaults</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Organization profile, default timezone, measurement units, and platform localization.
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  CORE SETTINGS
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Organization Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.general.organization_name}
                    onChange={(e) => handleFieldChange('general', 'organization_name', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Displayed on bills of lading (BOL), invoices, and reports.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Operations Contact Email <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={formData.general.contact_email}
                    onChange={(e) => handleFieldChange('general', 'contact_email', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Primary address for system-generated escalations.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Operations Support Hotline
                  </label>
                  <input
                    type="text"
                    value={formData.general.support_phone}
                    onChange={(e) => handleFieldChange('general', 'support_phone', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">24/7 central dispatch hotline for drivers on the road.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Headquarters Terminal Address
                  </label>
                  <input
                    type="text"
                    value={formData.general.headquarters_address}
                    onChange={(e) => handleFieldChange('general', 'headquarters_address', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Central staging depot and administrative hub.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Operational Timezone <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={formData.general.timezone}
                    onChange={(e) => handleFieldChange('general', 'timezone', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 cursor-pointer"
                  >
                    <option value="America/Chicago (CST)">America/Chicago (Central Time - UTC-6/UTC-5)</option>
                    <option value="America/New_York (EST)">America/New_York (Eastern Time - UTC-5/UTC-4)</option>
                    <option value="America/Denver (MST)">America/Denver (Mountain Time - UTC-7/UTC-6)</option>
                    <option value="America/Los_Angeles (PST)">America/Los_Angeles (Pacific Time - UTC-8/UTC-7)</option>
                    <option value="UTC">Coordinated Universal Time (UTC)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Display Date Format
                  </label>
                  <select
                    value={formData.general.date_format}
                    onChange={(e) => handleFieldChange('general', 'date_format', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 cursor-pointer"
                  >
                    <option value="YYYY-MM-DD">ISO 8601 (YYYY-MM-DD)</option>
                    <option value="MM/DD/YYYY">US Standard (MM/DD/YYYY)</option>
                    <option value="DD/MM/YYYY">International (DD/MM/YYYY)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Distance Measurement Unit
                  </label>
                  <select
                    value={formData.general.distance_unit}
                    onChange={(e) => handleFieldChange('general', 'distance_unit', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 cursor-pointer"
                  >
                    <option value="Kilometers (km)">Kilometers (km)</option>
                    <option value="Miles (mi)">Miles (mi)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Weight Unit
                  </label>
                  <select
                    value={formData.general.weight_unit}
                    onChange={(e) => handleFieldChange('general', 'weight_unit', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 cursor-pointer"
                  >
                    <option value="Kilograms (kg)">Kilograms (kg)</option>
                    <option value="Pounds (lbs)">Pounds (lbs)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 2: SHIPMENT & OPERATIONS */}
          {activeTab === 'shipments' && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Package className="w-4 h-4 text-blue-600" />
                    <span>Shipment Operations & SLA Targets</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Configure delivery SLA benchmarks, delay triggers, auto-allocation, and delivery verification.
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  SLA POLICIES
                </span>
              </div>

              {/* Toggles & Checkbox Features */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Automatic Driver & Truck Matching Recommendation</div>
                    <div className="text-[11px] text-slate-500">Suggest optimal available carrier truck and HOS-compliant driver upon shipment creation.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.shipments.auto_assign_driver}
                      onChange={(e) => handleFieldChange('shipments', 'auto_assign_driver', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Dynamic Weather & Traffic ETA Recalculation</div>
                    <div className="text-[11px] text-slate-500">Continuously update estimated time of arrival using real-time highway corridor conditions.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.shipments.auto_calculate_estimated_eta}
                      onChange={(e) => handleFieldChange('shipments', 'auto_calculate_estimated_eta', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Mandatory Proof of Delivery (POD) Signature</div>
                    <div className="text-[11px] text-slate-500">Require driver to log receiver sign-off before closing delivery checkpoint.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.shipments.enable_proof_of_delivery_signature}
                      onChange={(e) => handleFieldChange('shipments', 'enable_proof_of_delivery_signature', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              {/* Numerical Thresholds */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Standard Transit SLA Target (Hours)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="720"
                    value={formData.shipments.sla_target_hours}
                    onChange={(e) => handleFieldChange('shipments', 'sla_target_hours', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Benchmark delivery deadline for contract compliance.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Warning Delay Threshold (Minutes)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="180"
                    value={formData.shipments.warning_delay_threshold_mins}
                    onChange={(e) => handleFieldChange('shipments', 'warning_delay_threshold_mins', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Triggers amber warning badge in dashboard.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Critical Delay Exception (Minutes)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="300"
                    value={formData.shipments.critical_delay_threshold_mins}
                    onChange={(e) => handleFieldChange('shipments', 'critical_delay_threshold_mins', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Dispatches urgent notification to managers.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    ML High Risk Score Threshold (0–100)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={formData.shipments.high_risk_score_threshold}
                    onChange={(e) => handleFieldChange('shipments', 'high_risk_score_threshold', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Scores above this generate automated AI alerts.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Max Payload Limit Per Trailer (kg)
                  </label>
                  <input
                    type="number"
                    min="1000"
                    max="50000"
                    step="500"
                    value={formData.shipments.max_cargo_weight_limit_kg}
                    onChange={(e) => handleFieldChange('shipments', 'max_cargo_weight_limit_kg', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">DOT federal gross axle weight enforcement limit.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Default Cargo Classification
                  </label>
                  <input
                    type="text"
                    value={formData.shipments.default_cargo_type}
                    onChange={(e) => handleFieldChange('shipments', 'default_cargo_type', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Initial freight category in creation forms.</p>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: FLEET & DRIVER */}
          {activeTab === 'fleet' && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Truck className="w-4 h-4 text-blue-600" />
                    <span>Fleet & Commercial Driver Governance</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    FMCSA / DOT Hours of Service (HOS), preventive maintenance triggers, and vehicle telemetry.
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                  DOT COMPLIANCE
                </span>
              </div>

              {/* Toggles */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-900 text-xs">Real-Time HOS Violation & Fatigue Alarms</div>
                  <div className="text-[11px] text-slate-500">Automatically broadcast high-priority alerts when a driver approaches or breaches 11-hour limit.</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.fleet.enable_hos_violation_alerts}
                    onChange={(e) => handleFieldChange('fleet', 'enable_hos_violation_alerts', e.target.checked)}
                    disabled={!isAdmin}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* HOS & Maintenance Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Max Continuous Driving HOS (Hours)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="16"
                    value={formData.fleet.max_driver_hos_hours}
                    onChange={(e) => handleFieldChange('fleet', 'max_driver_hos_hours', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">DOT property-carrying legal driving limit (11.0h).</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Mandatory Rest Break Period (Hours)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="4"
                    max="24"
                    value={formData.fleet.min_rest_break_hours}
                    onChange={(e) => handleFieldChange('fleet', 'min_rest_break_hours', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Required off-duty rest hours before dispatch reset.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    HOS Warning Buffer Threshold (Hours)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="5"
                    value={formData.fleet.hos_warning_threshold_hours}
                    onChange={(e) => handleFieldChange('fleet', 'hos_warning_threshold_hours', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Pre-alert time buffer before shift expiration.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Preventive Maintenance Interval (km)
                  </label>
                  <input
                    type="number"
                    step="1000"
                    min="1000"
                    max="100000"
                    value={formData.fleet.preventive_maintenance_interval_km}
                    onChange={(e) => handleFieldChange('fleet', 'preventive_maintenance_interval_km', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Odometer threshold for scheduled vehicle inspections.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Low Fuel Alert Threshold (%)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="50"
                    value={formData.fleet.maintenance_fuel_threshold_pct}
                    onChange={(e) => handleFieldChange('fleet', 'maintenance_fuel_threshold_pct', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Alerts dispatch when truck fuel drops below level.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Highway Speed Cap Warning (km/h)
                  </label>
                  <input
                    type="number"
                    min="60"
                    max="150"
                    value={formData.fleet.speed_limit_warning_kmh}
                    onChange={(e) => handleFieldChange('fleet', 'speed_limit_warning_kmh', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Safety telemetry warning trigger for high speed.</p>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 4: AI & RAG */}
          {activeTab === 'ai_rag' && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-indigo-600" />
                    <span>AI Assistant, Vector Embeddings & RAG Engine</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Supabase pgvector similarity parameters, LangGraph tool calling limits, and ML predictors.
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                  LANGGRAPH & PGVECTOR
                </span>
              </div>

              {/* Toggles */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Machine Learning Delay Probability Predictor</div>
                    <div className="text-[11px] text-slate-500">Run scikit-learn models over weather, cargo weight, and highway traffic bottlenecks.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.ai_rag.enable_ml_delay_prediction}
                      onChange={(e) => handleFieldChange('ai_rag', 'enable_ml_delay_prediction', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Human-in-the-Loop Confirmation for High-Impact Dispatches</div>
                    <div className="text-[11px] text-slate-500">Require operator confirmation modal before executing automated corridor re-routing.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.ai_rag.require_human_confirmation_for_dispatch}
                      onChange={(e) => handleFieldChange('ai_rag', 'require_human_confirmation_for_dispatch', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              {/* Vector & Model Hyperparameters */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Vector Cosine Similarity Threshold (0.40 – 0.99)
                  </label>
                  <input
                    type="number"
                    step="0.02"
                    min="0.4"
                    max="0.99"
                    value={formData.ai_rag.vector_similarity_threshold}
                    onChange={(e) => handleFieldChange('ai_rag', 'vector_similarity_threshold', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">pgvector threshold for relevant SOP policy retrieval (default: 0.72).</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    RAG Context Chunks (Top K)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={formData.ai_rag.rag_top_k_chunks}
                    onChange={(e) => handleFieldChange('ai_rag', 'rag_top_k_chunks', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Number of grounded chunks passed to LangGraph agent.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Model Sampling Temperature (0.0 – 1.0)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.0"
                    max="1.0"
                    value={formData.ai_rag.llm_temperature}
                    onChange={(e) => handleFieldChange('ai_rag', 'llm_temperature', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Lower values yield deterministic operational answers.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Max Output Tokens Limit
                  </label>
                  <input
                    type="number"
                    step="256"
                    min="256"
                    max="8192"
                    value={formData.ai_rag.max_tokens_per_interaction}
                    onChange={(e) => handleFieldChange('ai_rag', 'max_tokens_per_interaction', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Token allocation ceiling per conversation turn.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    AI Automated Action Confidence (%)
                  </label>
                  <input
                    type="number"
                    min="50"
                    max="99"
                    value={formData.ai_rag.ai_confidence_threshold_pct}
                    onChange={(e) => handleFieldChange('ai_rag', 'ai_confidence_threshold_pct', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Confidence score threshold to recommend routing changes.</p>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 5: NOTIFICATIONS */}
          {activeTab === 'notifications' && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Bell className="w-4 h-4 text-blue-600" />
                    <span>Notifications, Webhooks & Alert Routing</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Configure operational exception channels, TMS webhook payloads, and distribution rosters.
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                  REAL-TIME DISPATCH
                </span>
              </div>

              {/* Channels Toggles */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Email Broadcast Notifications</div>
                    <div className="text-[11px] text-slate-500">Send automated incident emails to terminal managers.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.notifications.email_notifications_enabled}
                      onChange={(e) => handleFieldChange('notifications', 'email_notifications_enabled', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">SMS Driver Dispatch Alerts</div>
                    <div className="text-[11px] text-slate-500">Send urgent route modification SMS alerts to drivers.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.notifications.sms_alerts_enabled}
                      onChange={(e) => handleFieldChange('notifications', 'sms_alerts_enabled', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              {/* Endpoints & Email list */}
              <div className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Outbound Enterprise TMS Webhook Endpoint URL
                  </label>
                  <input
                    type="url"
                    value={formData.notifications.webhook_url}
                    onChange={(e) => handleFieldChange('notifications', 'webhook_url', e.target.value)}
                    disabled={!isAdmin}
                    placeholder="https://tms.example.com/api/v1/logistics-events"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">JSON HTTP POST payloads dispatched upon high-severity delivery exceptions.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Critical Alert Distribution List (Comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.notifications.critical_alert_recipients}
                    onChange={(e) => handleFieldChange('notifications', 'critical_alert_recipients', e.target.value)}
                    disabled={!isAdmin}
                    placeholder="dispatch@logiagent.io, ops-director@logiagent.io"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Recipients notified when SLA breach or severe temperature failure occurs.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Alert Digest Aggregation Frequency
                  </label>
                  <select
                    value={formData.notifications.digest_frequency}
                    onChange={(e) => handleFieldChange('notifications', 'digest_frequency', e.target.value)}
                    disabled={!isAdmin}
                    className="w-full max-w-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 cursor-pointer"
                  >
                    <option value="Real-time">Real-time (Immediate stream delivery)</option>
                    <option value="Hourly">Hourly Digest (Batched incidents)</option>
                    <option value="Daily Digest">Daily Morning Operations Digest</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 6: SECURITY & RBAC */}
          {activeTab === 'security' && (
            <div className="bg-white border border-slate-200/90 rounded-xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-purple-600" />
                    <span>Security, Authentication & RBAC Governance</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Session durations, rate-limiting policies, password constraints, and CORS origin controls.
                  </p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                  ENTERPRISE SECURITY
                </span>
              </div>

              {/* Security Toggles */}
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Require Administrator Approval for Self-Registrations</div>
                    <div className="text-[11px] text-slate-500">Newly registered users are placed in 'Pending_Approval' until authorized by Admin or Manager.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.security.require_admin_approval_for_new_accounts}
                      onChange={(e) => handleFieldChange('security', 'require_admin_approval_for_new_accounts', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900 text-xs">Sliding-Window API Rate Limiting</div>
                    <div className="text-[11px] text-slate-500">Protect authentication and AI inference endpoints from excessive requests.</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.security.rate_limiting_enabled}
                      onChange={(e) => handleFieldChange('security', 'rate_limiting_enabled', e.target.checked)}
                      disabled={!isAdmin}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              {/* Security Numerical & String Config */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Bearer JWT Token Lifespan (Minutes)
                  </label>
                  <input
                    type="number"
                    step="60"
                    min="15"
                    max="10080"
                    value={formData.security.session_timeout_minutes}
                    onChange={(e) => handleFieldChange('security', 'session_timeout_minutes', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Default 1440 minutes (24 hours).</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Minimum Password Length
                  </label>
                  <input
                    type="number"
                    min="6"
                    max="32"
                    value={formData.security.password_min_length}
                    onChange={(e) => handleFieldChange('security', 'password_min_length', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Enforced across registration and token activations.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Security Audit Retention (Days)
                  </label>
                  <input
                    type="number"
                    step="30"
                    min="7"
                    max="365"
                    value={formData.security.audit_log_retention_days}
                    onChange={(e) => handleFieldChange('security', 'audit_log_retention_days', Number(e.target.value))}
                    disabled={!isAdmin}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Historical checkpoint log retention window.</p>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1 text-xs">
                  Allowed CORS Origin Domains (Comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.security.allowed_cors_origins}
                  onChange={(e) => handleFieldChange('security', 'allowed_cors_origins', e.target.value)}
                  disabled={!isAdmin}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 focus:bg-white focus:outline-none focus:border-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Authorized frontend origin endpoints permitted to interact with FastAPI server.</p>
              </div>

              {/* Secrets Safety Notice */}
              <div className="p-3.5 rounded-xl bg-blue-50/60 border border-blue-100 flex items-start gap-2.5 text-xs text-slate-700">
                <Lock className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-slate-900">Cryptographic Keys & Database Credentials Protection</span>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Server environment secrets (such as <code className="font-mono text-slate-700">JWT_SECRET</code>, <code className="font-mono text-slate-700">GEMINI_API_KEY</code>, and <code className="font-mono text-slate-700">DATABASE_URL</code>) are securely loaded from environment variables and strictly excluded from client-side payloads.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action Bar */}
          <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowResetConfirmModal(true)}
                disabled={resetting || !isAdmin}
                className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
              >
                <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                <span>Reset {getTabTitle(activeTab)} Defaults</span>
              </button>

              {hasUnsavedChanges && (
                <button
                  type="button"
                  onClick={handleDiscardChanges}
                  className="px-3 py-2 bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                >
                  Discard Changes
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <button
                type="button"
                onClick={handleSaveCategory}
                disabled={saving || !isAdmin}
                className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
              >
                {saving ? (
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                <span>Save {getTabTitle(activeTab)} Settings</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirmModal && (
        <ConfirmationDialog
          isOpen={showResetConfirmModal}
          title={`Reset ${getTabTitle(activeTab)} Settings?`}
          message={`Are you sure you want to reset all parameters in '${getTabTitle(activeTab)}' back to standard enterprise defaults? This action will overwrite any custom configurations in this category.`}
          confirmLabel="Reset to Factory Defaults"
          cancelLabel="Cancel"
          isDangerous={false}
          isLoading={resetting}
          onConfirm={handleResetConfirmed}
          onCancel={() => setShowResetConfirmModal(false)}
        />
      )}
    </div>
  );
};
