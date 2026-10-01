import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { AnalyticsDashboard, OperationalInsightItem } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  AlertTriangle, 
  Truck, 
  Clock, 
  ShieldCheck, 
  RefreshCw,
  Download,
  Calendar,
  Layers,
  MapPin,
  Users,
  Activity,
  CheckCircle2,
  Info,
  AlertOctagon,
  Flame
} from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const { user, role } = useAuth();
  const [dashboard, setDashboard] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<string>('30d');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [activeSection, setActiveSection] = useState<'overview' | 'delays' | 'fleet' | 'routes' | 'costs' | 'insights' | 'customers'>('overview');

  const loadData = async (range: string = timeRange, status: string = statusFilter) => {
    try {
      setLoading(true);
      const data = await api.getAnalytics({
        time_range: range,
        status: status !== 'All' ? status : undefined
      });
      setDashboard(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(timeRange, statusFilter);
  }, [timeRange, statusFilter]);

  const handleExportCSV = () => {
    const token = localStorage.getItem('logiagent_token');
    const url = `http://127.0.0.1:8000/api/v1/analytics/export?time_range=${timeRange}`;
    window.open(url, '_blank');
  };

  if (loading && !dashboard) {
    return (
      <div className="p-16 text-center text-slate-600 font-mono text-xs flex items-center justify-center gap-2 bg-white rounded-2xl border border-slate-200 shadow-card">
        <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
        <span>Computing real-time PostgreSQL operational aggregations & bottlenecks...</span>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="p-12 text-center text-rose-800 bg-rose-50 rounded-2xl border border-rose-200 shadow-card">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-rose-600" />
        <p className="text-sm font-semibold">Unable to load analytics data.</p>
        <button onClick={() => loadData()} className="mt-3 px-4 py-1.5 text-xs bg-rose-600 hover:bg-rose-700 rounded-lg text-white font-semibold shadow-2xs cursor-pointer">Retry</button>
      </div>
    );
  }

  const { kpis, delay_root_causes, delay_duration_distribution, cost_breakdown, vehicle_utilization, corridor_efficiency, customer_analytics, operational_insights, trend_and_forecast_assessment, status_distribution } = dashboard;
  const costColors = ['#2563EB', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'];
  const statusColors: Record<string, string> = {
    'In Transit': '#2563EB',
    'Delivered': '#10B981',
    'Delayed': '#DC2626',
    'Pending': '#D97706',
    'Assigned': '#6366F1',
    'Picked Up': '#0284C7',
    'Cancelled': '#64748B'
  };

  const getSeverityBadge = (sev: OperationalInsightItem['severity']) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'HIGH':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'MEDIUM':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header & Filter Bar */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 shadow-card flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-600">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>Logistics Intelligence & Advanced Analytics</span>
                <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 text-[10px] font-mono border border-blue-200 font-semibold">
                  {role || 'Operations'} Scope
                </span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Real database performance telemetry, delay root-cause Pareto analysis, fleet capacity modeling, and operational bottleneck detection.
              </p>
            </div>
          </div>
        </div>

        {/* Date Range & Controls */}
        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
          {/* Time Range Pills */}
          <div className="flex items-center p-1 rounded-xl bg-slate-100 border border-slate-200">
            {[
              { id: 'today', label: 'Today' },
              { id: 'yesterday', label: 'Yesterday' },
              { id: '7d', label: '7D' },
              { id: '30d', label: '30D' },
              { id: '90d', label: '90D' }
            ].map(pill => (
              <button
                key={pill.id}
                onClick={() => setTimeRange(pill.id)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  timeRange === pill.id 
                    ? 'bg-white text-slate-900 shadow-xs' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {pill.label}
              </button>
            ))}
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 cursor-pointer shadow-2xs"
          >
            <option value="All">All Statuses</option>
            <option value="In Transit">In Transit</option>
            <option value="Delivered">Delivered</option>
            <option value="Delayed">Delayed</option>
            <option value="Pending">Pending</option>
            <option value="Assigned">Assigned</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={() => loadData(timeRange, statusFilter)}
            disabled={loading}
            className="p-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 transition-all disabled:opacity-50 cursor-pointer shadow-2xs"
            title="Refresh Real-Time Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>

          {/* Export CSV */}
          <button
            onClick={handleExportCSV}
            className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <Download className="w-3.5 h-3.5 text-emerald-600" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200 text-xs font-semibold">
        {[
          { id: 'overview', label: 'Executive Overview', icon: Layers },
          { id: 'delays', label: 'Delays & Root Causes', icon: AlertTriangle },
          { id: 'fleet', label: 'Fleet & Capacity', icon: Truck },
          { id: 'routes', label: 'Corridor Efficiency', icon: MapPin },
          ...(role !== 'Driver' && role !== 'Dispatcher' ? [{ id: 'costs', label: 'Cost Intelligence', icon: DollarSign }] : []),
          { id: 'insights', label: `Bottlenecks (${operational_insights?.length || 0})`, icon: AlertOctagon },
          ...(role !== 'Driver' ? [{ id: 'customers', label: 'Customer Volume', icon: Users }] : [])
        ].map((tab: any) => {
          const IconComp = tab.icon;
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id)}
              className={`px-3.5 py-2 rounded-xl flex items-center gap-2 whitespace-nowrap transition-all cursor-pointer ${
                isActive 
                  ? 'bg-blue-50 text-blue-700 border border-blue-200 font-bold' 
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <IconComp className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Section 1: Executive KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* Total Shipments */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Total Volume</span>
            <Layers className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 font-mono">{kpis.total_shipments}</div>
          <div className="mt-1 text-[11px] text-slate-500 flex items-center gap-1">
            <span className="text-emerald-700 font-semibold">{kpis.delivered_shipments} Deliv</span> · 
            <span className="text-blue-700 font-semibold">{kpis.in_transit_shipments} Active</span>
          </div>
        </div>

        {/* On-Time Delivery % */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>On-Time SLA</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-700 font-mono">
            {kpis.on_time_delivery_rate_pct}%
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Target SLA: <span className="text-slate-700 font-semibold">95.0%</span>
          </div>
        </div>

        {/* Delayed Volume */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Transit Delays</span>
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-700 font-mono">{kpis.delayed_shipments}</div>
          <div className="mt-1 text-[11px] text-slate-500">
            Avg: <span className="text-rose-700 font-semibold">+{kpis.average_delay_minutes || 0}m</span>
          </div>
        </div>

        {/* Fleet Utilization */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Fleet Utilization</span>
            <Truck className="w-3.5 h-3.5 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 font-mono">{kpis.fleet_utilization_pct}%</div>
          <div className="mt-1 text-[11px] text-slate-500">
            <span className="text-emerald-700 font-semibold">{kpis.available_vehicles} Ready</span> / {kpis.total_vehicles} Units
          </div>
        </div>

        {/* Avg Delivery Duration */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Avg Lead Time</span>
            <Clock className="w-3.5 h-3.5 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 font-mono">
            {kpis.average_delivery_hours || 0}h
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            ETA Remaining: <span className="text-indigo-700 font-semibold">{kpis.average_eta_hours}h</span>
          </div>
        </div>

        {/* Total Spend */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Network Spend</span>
            <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-700 font-mono truncate">
            ${kpis.total_transportation_cost.toLocaleString()}
          </div>
          <div className="mt-1 text-[11px] text-slate-500 truncate">
            Avg/km: <span className="text-slate-700 font-semibold">${kpis.average_cost_per_km || 0}/km</span>
          </div>
        </div>
      </div>

      {/* TAB 1: EXECUTIVE OVERVIEW */}
      {activeSection === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Status Breakdown Bar Chart */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-600" />
                  <span>Shipment Status Distribution</span>
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Live operational lifecycle volume across all network corridors</p>
              </div>
              <span className="text-xs font-mono text-slate-600 font-semibold">{kpis.total_shipments} Shipments Total</span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={status_distribution} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                  <XAxis dataKey="status" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#CBD5E1',
                      borderRadius: '8px',
                      color: '#0F172A',
                      fontSize: '12px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {status_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={statusColors[entry.status] || '#2563EB'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quick SLA & Risk Status Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Operational Health Status</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Real-time compliance vs target SLAs</p>
            </div>

            <div className="space-y-3 my-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <span className="text-xs text-slate-600">On-Time Performance</span>
                <span className={`text-xs font-mono font-bold ${kpis.on_time_delivery_rate_pct >= 90 ? 'text-emerald-700' : 'text-amber-700'}`}>
                  {kpis.on_time_delivery_rate_pct}%
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <span className="text-xs text-slate-600">At-Risk Cargo Monitor</span>
                <span className={`text-xs font-mono font-bold ${kpis.at_risk_shipments > 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
                  {kpis.at_risk_shipments} At-Risk
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <span className="text-xs text-slate-600">Today Expected Deliveries</span>
                <span className="text-xs font-mono font-bold text-blue-700">{kpis.today_deliveries_count} Units</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <span className="text-xs text-slate-600">Driver Compliance (Avg Rating)</span>
                <span className="text-xs font-mono font-bold text-emerald-700">{kpis.driver_average_rating || 4.8} / 5.0</span>
              </div>
            </div>

            {/* Historical Trend Note */}
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-[11px] text-blue-800 flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <span>{trend_and_forecast_assessment?.historical_trend?.summary || 'Historical baseline synchronized with live Supabase database.'}</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DELAYS & ROOT CAUSES */}
      {activeSection === 'delays' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Real Delay Root Cause Pareto */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600" />
                  <span>Delay Root Cause Pareto Analysis</span>
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Aggregated from PostgreSQL shipment audit history</p>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 text-xs font-mono font-semibold border border-rose-200">
                {delay_root_causes.length} Root Causes
              </span>
            </div>

            {delay_root_causes.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={delay_root_causes} layout="vertical" margin={{ top: 5, right: 20, left: 30, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                    <XAxis type="number" stroke="#64748B" fontSize={10} tickLine={false} />
                    <YAxis dataKey="reason" type="category" stroke="#64748B" fontSize={9} width={130} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderColor: '#CBD5E1',
                        borderRadius: '8px',
                        color: '#0F172A',
                        fontSize: '12px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                      }}
                    />
                    <Bar dataKey="count" fill="#DC2626" radius={[0, 6, 6, 0]} name="Incidents Logged" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">No transit delays recorded for this time range.</div>
            )}
          </div>

          {/* Delay Duration Distribution */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-600" />
                  <span>Delay Duration Distribution</span>
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Severity distribution across operational delay brackets</p>
              </div>
              <span className="text-xs font-mono text-amber-700 font-semibold">Max: +{kpis.max_delay_minutes || 0}m</span>
            </div>

            {delay_duration_distribution ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={delay_duration_distribution} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                    <XAxis dataKey="bracket" stroke="#64748B" fontSize={10} tickLine={false} />
                    <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderColor: '#CBD5E1',
                        borderRadius: '8px',
                        color: '#0F172A',
                        fontSize: '12px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                      }}
                    />
                    <Bar dataKey="count" fill="#D97706" radius={[6, 6, 0, 0]} name="Shipments Affected" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* TAB 3: FLEET & CAPACITY */}
      {activeSection === 'fleet' && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Truck className="w-4 h-4 text-blue-600" />
                <span>Fleet Capacity & Payload Load Modeling by Vehicle Type</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Actual payload weights vs maximum GVWR thresholds</p>
            </div>
            <span className="text-xs font-mono text-blue-700 font-semibold">{kpis.total_vehicles} Vehicles Monitored</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            {vehicle_utilization.map((v, i) => (
              <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 truncate">{v.vehicle_type}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                    {v.active_count} / {v.total_count} Active
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-500 font-medium">Avg Load:</span>
                    <span className="text-slate-900 font-mono font-bold">{v.average_load_pct}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        v.average_load_pct >= 70 ? 'bg-emerald-600' : v.average_load_pct >= 40 ? 'bg-blue-600' : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(100, v.average_load_pct)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: CORRIDOR EFFICIENCY */}
      {activeSection === 'routes' && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-600" />
                <span>Corridor Efficiency & Network Route Performance</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Authoritative canonical highway distances, travel durations, and cost per km</p>
            </div>
            <span className="text-xs font-mono text-slate-600">{corridor_efficiency?.length || 0} Corridors Active</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 font-mono text-[11px] uppercase border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Route Code</th>
                  <th className="py-2.5 px-3">Transit Corridor</th>
                  <th className="py-2.5 px-3">Planned Dist</th>
                  <th className="py-2.5 px-3">Est Duration</th>
                  <th className="py-2.5 px-3">Traffic / Weather</th>
                  <th className="py-2.5 px-3">Estimated Cost</th>
                  <th className="py-2.5 px-3">Cost / KM</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {corridor_efficiency && corridor_efficiency.length > 0 ? (
                  corridor_efficiency.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-50/80 transition-all">
                      <td className="py-2.5 px-3 font-mono font-bold text-blue-700">{r.route_code}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900 max-w-xs truncate">{r.corridor}</td>
                      <td className="py-2.5 px-3 font-mono">{r.distance_km} km</td>
                      <td className="py-2.5 px-3 font-mono">{Math.floor(r.duration_min / 60)}h {r.duration_min % 60}m</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-[10px] text-slate-700 font-medium">{r.traffic} / {r.weather}</span>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-700">${r.cost_usd.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-600">${r.cost_per_km}/km</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="text-center py-6 text-slate-500">No active corridors found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: COST MODELING */}
      {activeSection === 'costs' && role !== 'Driver' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Pie Chart */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span>Transportation Cost Breakdown</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Category spend allocation</p>
            </div>

            <div className="h-56 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={cost_breakdown}
                    cx="50%"
                    cy="50%"
                    outerRadius={75}
                    innerRadius={45}
                    paddingAngle={4}
                    dataKey="amount"
                  >
                    {cost_breakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={costColors[index % costColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#CBD5E1',
                      borderRadius: '8px',
                      color: '#0F172A',
                      fontSize: '12px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
              {cost_breakdown.map((c, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: costColors[i] }}></span>
                    <span className="text-slate-600">{c.category}:</span>
                  </div>
                  <span className="text-slate-900 font-mono font-bold">${c.amount.toLocaleString()} ({c.percentage}%)</span>
                </div>
              ))}
            </div>
          </div>

          {/* Financial KPI Summary */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-5">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                <span>Financial Efficiency Modeling</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Total network expenditure vs unit economics</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-xs text-slate-500 font-medium">Total Spend</span>
                <div className="text-xl font-mono font-bold text-emerald-700 mt-1">${kpis.total_transportation_cost.toLocaleString()}</div>
                <span className="text-[10px] text-slate-400">Live PostgreSQL sum</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-xs text-slate-500 font-medium">Avg Cost / Shipment</span>
                <div className="text-xl font-mono font-bold text-slate-900 mt-1">${kpis.average_cost_per_shipment || 0}</div>
                <span className="text-[10px] text-slate-400">Per unit delivered</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-xs text-slate-500 font-medium">Avg Cost / KM</span>
                <div className="text-xl font-mono font-bold text-blue-700 mt-1">${kpis.average_cost_per_km || 0}/km</div>
                <span className="text-[10px] text-slate-400">Highway efficiency</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-xs text-slate-800 space-y-1">
              <div className="font-bold text-blue-900">Cost Optimization Guidance:</div>
              <p className="text-slate-600">
                Driver labor and fuel represent the largest operational expenditures. Increasing payload capacity utilization on flatbed and dry van corridors can reduce average cost/km by up to 12.5%.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: OPERATIONAL BOTTLENECK INSIGHTS */}
      {activeSection === 'insights' && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 text-amber-600" />
                <span>Deterministic Operational Bottlenecks & Intelligence Findings</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Automated rule-based detection operating directly over Supabase records</p>
            </div>
            <span className="text-xs font-mono text-slate-600 font-medium">{operational_insights?.length || 0} Findings Active</span>
          </div>

          <div className="space-y-3 pt-2">
            {operational_insights && operational_insights.length > 0 ? (
              operational_insights.map((ins, i) => (
                <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getSeverityBadge(ins.severity)}`}>
                        {ins.severity}
                      </span>
                      <span className="text-xs font-bold text-slate-900">{ins.title}</span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">Rule ID: {ins.id}</span>
                  </div>

                  <p className="text-xs text-slate-700">{ins.explanation}</p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-600 pt-1 border-t border-slate-200">
                    <div>
                      <span className="text-slate-500">Metric Value:</span>{' '}
                      <strong className="text-slate-900 font-mono">{ins.metric_value}</strong> (Threshold: {ins.threshold})
                    </div>
                    {ins.related_records && ins.related_records.length > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="text-slate-500">Affected Entities:</span>{' '}
                        <span className="text-blue-700 font-mono font-semibold">{ins.related_records.join(', ')}</span>
                      </div>
                    )}
                  </div>

                  <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-[11px] text-blue-900 flex items-start gap-1.5">
                    <Flame className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
                    <span><strong>Action Recommended:</strong> {ins.recommended_action}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">No active operational bottlenecks detected.</div>
            )}
          </div>
        </div>
      )}

      {/* TAB 7: CUSTOMER ANALYTICS */}
      {activeSection === 'customers' && role !== 'Driver' && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-600" />
                <span>Customer Shipment Volume & Fulfillment Performance</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Volume, delivered count, and SLA performance by customer account</p>
            </div>
            <span className="text-xs font-mono text-slate-600">{customer_analytics?.length || 0} Accounts</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 font-mono text-[11px] uppercase border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Customer</th>
                  <th className="py-2.5 px-3">Tier</th>
                  <th className="py-2.5 px-3">Total Shipments</th>
                  <th className="py-2.5 px-3">Delivered</th>
                  <th className="py-2.5 px-3">Delayed</th>
                  <th className="py-2.5 px-3">On-Time %</th>
                  <th className="py-2.5 px-3">Total Spend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {customer_analytics && customer_analytics.length > 0 ? (
                  customer_analytics.map((c, i) => (
                    <tr key={i} className="hover:bg-slate-50/80 transition-all">
                      <td className="py-2.5 px-3 font-medium text-slate-900">
                        <div className="font-bold">{c.company_name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{c.customer_code} · {c.name}</div>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {c.tier}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{c.total_shipments}</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-700 font-semibold">{c.delivered_count}</td>
                      <td className="py-2.5 px-3 font-mono text-rose-700 font-semibold">{c.delayed_count}</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{c.on_time_rate_pct}%</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-700">${c.total_spend_usd.toLocaleString()}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="text-center py-6 text-slate-500">No customer records available.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
