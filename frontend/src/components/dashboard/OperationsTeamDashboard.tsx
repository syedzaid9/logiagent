import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../../api/services';
import { AnalyticsDashboard, Shipment, AlertItem } from '../../types';
import { KPICard } from '../common/KPICard';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { AlertBadge } from '../common/AlertBadge';
import { KPISkeleton, CardSkeleton } from '../common/LoadingSkeleton';
import { ErrorState } from '../common/ErrorState';
import { QuickActionGroup } from '../common/QuickAction';
import {
  Activity,
  AlertTriangle,
  ClipboardList,
  CheckCircle2,
  Package,
  Truck,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Clock,
  RefreshCw,
  Layers
} from 'lucide-react';

interface OperationsTeamDashboardProps {
  onNavigate: (tab: string) => void;
  onViewRoute?: (code: string) => void;
}

export const OperationsTeamDashboard: React.FC<OperationsTeamDashboardProps> = ({
  onNavigate,
  onViewRoute,
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const [analyticsData, shipmentsData, alertsData] = await Promise.all([
        api.getAnalytics(),
        api.getShipments(),
        api.getAiAlerts({ status: 'active', limit: 6 }).catch(() => []),
      ]);
      setAnalytics(analyticsData);
      setShipments(shipmentsData);
      setAlerts(alertsData);
    } catch (err: any) {
      console.error('Failed to load operations team data:', err);
      setError(err.message || 'Failed to retrieve operational exceptions telemetry.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAcknowledgeAlert = async (id: number) => {
    try {
      await api.acknowledgeAiAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'acknowledged' } : a)));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const delayedShipments = shipments.filter((s) => s.status === 'Delayed' || s.delay_minutes > 0);
  const activeShipments = shipments.filter((s) => ['In Transit', 'Picked Up', 'Assigned'].includes(s.status));

  if (loading && !analytics) {
    return (
      <div className="space-y-5">
        <div className="h-20 bg-white rounded-xl border border-slate-200 animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <KPISkeleton />
          <KPISkeleton />
          <KPISkeleton />
          <KPISkeleton />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return <ErrorState message={error} onRetry={() => loadData()} />;
  }

  const kpis = analytics!.kpis;

  const opsTasks = [
    { id: '1', title: 'Verify Staging Clearance for SHP-1004', priority: 'HIGH', entity: 'SHP-1004', status: 'Pending Review' },
    { id: '2', title: 'Carrier Contact Confirmation (Failed Delivery Policy SOP-LOG-02)', priority: 'HIGH', entity: 'SHP-1008', status: 'In Progress' },
    { id: '3', title: 'Midwest Highway Weather Re-Routing Check', priority: 'MEDIUM', entity: 'RTE-1003', status: 'Pending' },
    { id: '4', title: 'Volvo VNL 860 Reefer Preventive Temperature Check', priority: 'MEDIUM', entity: 'TRK-102', status: 'Scheduled' },
  ];

  const opsActions = [
    {
      id: 'resolve-delayed',
      title: 'Delayed Freight Exceptions',
      description: `Investigate ${delayedShipments.length} shipments currently exceeding SLA delivery deadlines.`,
      icon: AlertTriangle,
      iconColor: 'text-rose-600',
      bgColor: 'bg-rose-50',
      badge: delayedShipments.length > 0 ? `${delayedShipments.length} Delayed` : undefined,
      onClick: () => onNavigate('shipments'),
    },
    {
      id: 'active-routes',
      title: 'Corridor Optimization',
      description: 'Review highway bottlenecks and calculate alternative bypass corridors.',
      icon: Activity,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      onClick: () => onNavigate('routes'),
    },
    {
      id: 'policy-sop',
      title: 'SOP & Policy Explorer',
      description: 'Check standard operating procedures for failed deliveries, breakdowns, and hazmat.',
      icon: ClipboardList,
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      onClick: () => onNavigate('documents'),
    },
    {
      id: 'ai-assistant',
      title: 'AI Operations Assistant',
      description: 'Query natural-language root-cause explanations and mitigation recommendations.',
      icon: Sparkles,
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      onClick: () => onNavigate('chat'),
    },
  ];

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Header */}
      <PageHeader
        title="Operations & Exception Management Workspace"
        subtitle="Active cargo exceptions, bottleneck resolution, operational shift task tracking, and priority alerts."
        icon={Activity}
        badge="OPERATIONS TEAM"
        badgeColor="bg-blue-50 text-blue-700 border-blue-200"
        onRefresh={() => loadData(true)}
        isRefreshing={refreshing}
        actions={
          <button
            onClick={() => onNavigate('chat')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Operations</span>
          </button>
        }
      />

      {/* 2. Top 4 Operational KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <KPICard
          title="Open Operational Tasks"
          value={opsTasks.length}
          subtitle="Assigned to current shift"
          icon={ClipboardList}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
        />

        <KPICard
          title="Active Delayed Shipments"
          value={delayedShipments.length}
          subtitle="Exceeding schedule"
          icon={AlertTriangle}
          iconColor={delayedShipments.length > 0 ? 'text-rose-600' : 'text-slate-400'}
          bgColor={delayedShipments.length > 0 ? 'bg-rose-50' : 'bg-slate-50'}
          highlight={delayedShipments.length > 0}
          onClick={() => onNavigate('shipments')}
        />

        <KPICard
          title="Active Transit Corridors"
          value={activeShipments.length}
          subtitle="En route network"
          icon={Truck}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          onClick={() => onNavigate('routes')}
        />

        <KPICard
          title="Critical Alerts"
          value={alerts.length}
          subtitle="Requires operator sign-off"
          icon={ShieldAlert}
          iconColor={alerts.length > 0 ? 'text-amber-600' : 'text-slate-400'}
          bgColor={alerts.length > 0 ? 'bg-amber-50' : 'bg-slate-50'}
          onClick={() => onNavigate('notifications')}
        />
      </div>

      {/* 3. Operational Tasks & Priority Alerts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Shift Tasks Table */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ClipboardList className="w-4 h-4 text-blue-600" />
              <span>Shift Exception & Action Tasks</span>
            </h3>
            <span className="text-xs font-semibold text-slate-500">{opsTasks.length} Tasks</span>
          </div>

          <div className="space-y-2.5">
            {opsTasks.map((task) => (
              <div
                key={task.id}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
              >
                <div>
                  <div className="font-bold text-slate-900">{task.title}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Entity: <strong className="text-slate-700">{task.entity}</strong> • {task.status}</div>
                </div>

                <div className="text-right">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    task.priority === 'HIGH' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-blue-50 text-blue-700 border-blue-200'
                  }`}>
                    {task.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Operational Alerts */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Actionable Exception Alerts</span>
            </h3>
            <button
              onClick={() => onNavigate('notifications')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5">
            {alerts.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No active operational alerts.
              </div>
            ) : (
              alerts.map((a) => (
                <div
                  key={a.id}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <AlertBadge severity={a.severity} />
                      <span className="font-bold text-slate-900">{a.title}</span>
                    </div>
                    <p className="text-[11px] text-slate-600">{a.message}</p>
                    {a.recommended_action && (
                      <div className="text-[10px] text-amber-800 font-medium bg-amber-50 px-2 py-0.5 rounded border border-amber-100 inline-block mt-0.5">
                        Action: {a.recommended_action}
                      </div>
                    )}
                  </div>

                  {a.status === 'active' && (
                    <button
                      onClick={() => handleAcknowledgeAlert(a.id)}
                      className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer shrink-0"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 4. Operations Quick Actions */}
      <QuickActionGroup title="Exception Resolution Workflows" actions={opsActions} />
    </div>
  );
};
