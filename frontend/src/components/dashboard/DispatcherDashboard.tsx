import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { Shipment, Vehicle, Driver, RouteItem, AlertItem } from '../../types';
import { KPICard } from '../common/KPICard';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { AlertBadge } from '../common/AlertBadge';
import { KPISkeleton, CardSkeleton } from '../common/LoadingSkeleton';
import { EmptyState } from '../common/EmptyState';
import { ErrorState } from '../common/ErrorState';
import { QuickActionGroup } from '../common/QuickAction';
import {
  Radio,
  Truck,
  Package,
  Route,
  AlertTriangle,
  Clock,
  MapPin,
  Users,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Navigation,
  Send,
  RefreshCw
} from 'lucide-react';

interface DispatcherDashboardProps {
  onNavigate?: (tab: string) => void;
  onViewRoute?: (code: string) => void;
}

export const DispatcherDashboard: React.FC<DispatcherDashboardProps> = ({
  onNavigate,
  onViewRoute,
}) => {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    else setIsRefreshing(true);
    setError(null);

    try {
      const [sRes, vRes, dRes, aRes] = await Promise.all([
        api.getShipments(),
        api.getVehicles(),
        api.getDrivers(),
        api.getAiAlerts({ status: 'active', limit: 4 }).catch(() => []),
      ]);
      setShipments(sRes);
      setVehicles(vRes);
      setDrivers(dRes);
      setAlerts(aRes);
    } catch (err: any) {
      console.error('Failed to load dispatcher data:', err);
      setError(err.message || 'Failed to connect to dispatch telemetry.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const activeShipments = shipments.filter((s) => ['In Transit', 'Picked Up', 'Assigned'].includes(s.status));
  const pendingDispatch = shipments.filter((s) => ['Pending', 'Created'].includes(s.status));
  const delayedShipments = shipments.filter((s) => s.status === 'Delayed' || s.delay_minutes > 0);
  const availableVehicles = vehicles.filter((v) => v.status === 'Available');
  const availableDrivers = drivers.filter((d) => (d.status || '').toLowerCase() === 'available');

  if (isLoading && shipments.length === 0) {
    return (
      <div className="space-y-5">
        <div className="h-20 bg-white rounded-xl border border-slate-200 animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <KPISkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error && shipments.length === 0) {
    return <ErrorState message={error} onRetry={() => loadData()} />;
  }

  const dispatchActions = [
    {
      id: 'quick-assign',
      title: 'Assign Pending Cargo',
      description: `Dispatch ${pendingDispatch.length} waiting shipments to ready trucks.`,
      icon: Package,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      badge: pendingDispatch.length > 0 ? `${pendingDispatch.length} Pending` : undefined,
      onClick: () => onNavigate && onNavigate('shipments'),
    },
    {
      id: 'optimize-routes',
      title: 'Optimize Corridors',
      description: 'Calculate fastest highway corridors and toll-free bypasses.',
      icon: Route,
      iconColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      onClick: () => onNavigate && onNavigate('routes'),
    },
    {
      id: 'driver-roster',
      title: 'Driver Duty Roster',
      description: `Review ${availableDrivers.length} certified drivers ready for dispatch.`,
      icon: Users,
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      onClick: () => onNavigate && onNavigate('drivers'),
    },
    {
      id: 'ai-dispatch',
      title: 'AI Dispatch Assistant',
      description: 'Ask AI for optimal truck allocation and real-time delay mitigations.',
      icon: Sparkles,
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      onClick: () => onNavigate && onNavigate('chat'),
    },
  ];

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Header */}
      <PageHeader
        title="Live Dispatch Operations Console"
        subtitle="Real-time freight assignment, fleet capacity allocation, live corridor tracking, and delay mitigation."
        icon={Radio}
        badge="DISPATCH CONTROL"
        badgeColor="bg-emerald-50 text-emerald-700 border-emerald-200"
        onRefresh={() => loadData(true)}
        isRefreshing={isRefreshing}
        actions={
          <button
            onClick={() => onNavigate && onNavigate('chat')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Dispatcher</span>
          </button>
        }
      />

      {/* 2. Top 5 Dispatch KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <KPICard
          title="Active In-Transit"
          value={activeShipments.length}
          subtitle="Currently on road"
          icon={Truck}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
          trend="GPS Tracking"
          trendUp={true}
          onClick={() => onNavigate && onNavigate('shipments')}
        />

        <KPICard
          title="Pending Dispatch"
          value={pendingDispatch.length}
          subtitle="Awaiting allocation"
          icon={Clock}
          iconColor={pendingDispatch.length > 0 ? 'text-amber-600' : 'text-slate-400'}
          bgColor={pendingDispatch.length > 0 ? 'bg-amber-50' : 'bg-slate-50'}
          highlight={pendingDispatch.length > 0}
          onClick={() => onNavigate && onNavigate('shipments')}
        />

        <KPICard
          title="Available Trucks"
          value={availableVehicles.length}
          subtitle={`Of ${vehicles.length} total units`}
          icon={CheckCircle2}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          trend="Ready"
          trendUp={true}
          onClick={() => onNavigate && onNavigate('vehicles')}
        />

        <KPICard
          title="Available Drivers"
          value={availableDrivers.length}
          subtitle="HOS compliant ready"
          icon={Users}
          iconColor="text-purple-600"
          bgColor="bg-purple-50"
          onClick={() => onNavigate && onNavigate('drivers')}
        />

        <KPICard
          title="Critical Delays"
          value={delayedShipments.length}
          subtitle="Exceeding schedule"
          icon={AlertTriangle}
          iconColor={delayedShipments.length > 0 ? 'text-rose-600' : 'text-slate-400'}
          bgColor={delayedShipments.length > 0 ? 'bg-rose-50' : 'bg-slate-50'}
          highlight={delayedShipments.length > 0}
          onClick={() => onNavigate && onNavigate('shipments')}
        />
      </div>

      {/* 3. Dispatch Queue Table (Compact Operational View) */}
      <div className="bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-2xs space-y-0">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-600" />
              <span>Priority Dispatch Queue</span>
            </h3>
            <p className="text-[11px] text-slate-500">
              Active cargo assignments, assigned vehicle/driver pairings, and live status.
            </p>
          </div>

          <button
            onClick={() => onNavigate && onNavigate('shipments')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
          >
            <span>View All Shipments</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50/80 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Shipment</th>
                <th className="py-3 px-4">Corridor</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Vehicle</th>
                <th className="py-3 px-4">Driver</th>
                <th className="py-3 px-4">ETA</th>
                <th className="py-3 px-4 text-right">Dispatch Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {shipments.slice(0, 6).map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-bold text-slate-900">{s.shipment_code}</div>
                    <div className="text-[10px] text-slate-400">{s.customer_name}</div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-medium text-slate-800 flex items-center gap-1">
                      <span>{s.origin_city || 'Origin'}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <span>{s.destination_city || 'Destination'}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="py-3 px-4 font-mono font-medium text-slate-800">
                    {s.vehicle_code || <span className="text-slate-400 italic">Unassigned</span>}
                  </td>
                  <td className="py-3 px-4 text-slate-800">
                    {s.driver_name || <span className="text-slate-400 italic">Unassigned</span>}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                    {s.estimated_eta
                      ? new Date(s.estimated_eta).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : 'Scheduled'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {onViewRoute && (
                        <button
                          onClick={() => onViewRoute(s.shipment_code)}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer"
                        >
                          Track Route
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Ready Vehicles & Ready Drivers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Available Vehicles for Scheduling */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Truck className="w-4 h-4 text-emerald-600" />
              <span>Available Fleet Vehicles ({availableVehicles.length})</span>
            </h3>
            <button
              onClick={() => onNavigate && onNavigate('vehicles')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View Fleet</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {availableVehicles.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">All fleet trucks are currently assigned or in transit.</p>
            ) : (
              availableVehicles.slice(0, 5).map((v) => (
                <div
                  key={v.id}
                  className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
                >
                  <div>
                    <div className="font-bold text-slate-900">{v.vehicle_code}</div>
                    <div className="text-[11px] text-slate-500">{v.model} ({v.type})</div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Available
                    </span>
                    <div className="text-[10px] text-slate-400 mt-0.5">Cap: {v.max_capacity_kg.toLocaleString()} kg</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Ready Drivers Roster */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-600" />
              <span>Ready Commercial Drivers ({availableDrivers.length})</span>
            </h3>
            <button
              onClick={() => onNavigate && onNavigate('drivers')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View Roster</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {availableDrivers.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No drivers currently on standby roster.</p>
            ) : (
              availableDrivers.slice(0, 5).map((d) => (
                <div
                  key={d.id}
                  className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
                >
                  <div>
                    <div className="font-bold text-slate-900">{d.name} ({d.driver_code})</div>
                    <div className="text-[11px] text-slate-500">{d.license_type || 'CDL-A'} • {d.phone || 'Phone verified'}</div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                      {d.hours_of_service_remaining ?? 11}h HOS
                    </span>
                    <div className="text-[10px] text-slate-400 mt-0.5">Rating: {d.rating ?? 4.9} ★</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 5. Dispatch Quick Actions */}
      <QuickActionGroup title="Dispatch Workflows" actions={dispatchActions} />
    </div>
  );
};
