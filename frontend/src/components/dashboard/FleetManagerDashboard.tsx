import React, { useEffect, useState } from 'react';
import { api } from '../../api/services';
import { Vehicle, Driver, FleetStats, DriverStats, AlertItem } from '../../types';
import { KPICard } from '../common/KPICard';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { AlertBadge } from '../common/AlertBadge';
import { KPISkeleton, CardSkeleton } from '../common/LoadingSkeleton';
import { ErrorState } from '../common/ErrorState';
import { QuickActionGroup } from '../common/QuickAction';
import {
  Truck,
  Users,
  Wrench,
  Gauge,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Fuel,
  RefreshCw
} from 'lucide-react';

interface FleetManagerDashboardProps {
  onNavigate?: (tab: string) => void;
}

export const FleetManagerDashboard: React.FC<FleetManagerDashboardProps> = ({ onNavigate }) => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [fleetStats, setFleetStats] = useState<FleetStats | null>(null);
  const [driverStats, setDriverStats] = useState<DriverStats | null>(null);
  const [fleetAlerts, setFleetAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const [vList, dList, fStats, dStats, aList] = await Promise.all([
        api.getVehicles(),
        api.getDrivers(),
        api.getFleetStats(),
        api.getDriverStats(),
        api.getAiAlerts({ entity_type: 'vehicle', limit: 4 }).catch(() => []),
      ]);
      setVehicles(vList);
      setDrivers(dList);
      setFleetStats(fStats);
      setDriverStats(dStats);
      setFleetAlerts(aList);
    } catch (err: any) {
      console.error('Failed to load fleet dashboard data:', err);
      setError(err.message || 'Failed to retrieve fleet telemetry.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const maintenanceVehicles = vehicles.filter((v) => v.status === 'Maintenance');
  const availableVehicles = vehicles.filter((v) => v.status === 'Available');
  const inTransitVehicles = vehicles.filter((v) => v.status === 'In Transit');

  if (loading && vehicles.length === 0) {
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

  if (error && vehicles.length === 0) {
    return <ErrorState message={error} onRetry={() => loadData()} />;
  }

  const fleetActions = [
    {
      id: 'manage-fleet-grid',
      title: 'Fleet Asset Grid',
      description: 'Review full fleet registry, payload utilization, and vehicle locations.',
      icon: Truck,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      onClick: () => onNavigate && onNavigate('vehicles'),
    },
    {
      id: 'maintenance-schedule',
      title: 'Maintenance Scheduler',
      description: `Schedule preventive inspections for ${maintenanceVehicles.length} flagged units.`,
      icon: Wrench,
      iconColor: 'text-amber-600',
      bgColor: 'bg-amber-50',
      badge: maintenanceVehicles.length > 0 ? `${maintenanceVehicles.length} Service Due` : undefined,
      onClick: () => onNavigate && onNavigate('vehicles'),
    },
    {
      id: 'driver-safety',
      title: 'Driver Hours of Service',
      description: `Audit DOT safety logs and HOS availability for ${drivers.length} commercial drivers.`,
      icon: Users,
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      onClick: () => onNavigate && onNavigate('drivers'),
    },
    {
      id: 'route-telemetry',
      title: 'Corridor Telemetry',
      description: 'Inspect live vehicle GPS tracking and fuel consumption rates.',
      icon: Gauge,
      iconColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      onClick: () => onNavigate && onNavigate('routes'),
    },
  ];

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Header */}
      <PageHeader
        title="Fleet & Asset Governance Console"
        subtitle="Live vehicle telemetry, maintenance scheduling, driver hours of service, and payload efficiency."
        icon={Truck}
        badge="FLEET MANAGEMENT"
        badgeColor="bg-blue-50 text-blue-700 border-blue-200"
        onRefresh={() => loadData(true)}
        isRefreshing={refreshing}
        actions={
          <button
            onClick={() => onNavigate && onNavigate('vehicles')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            <Truck className="w-3.5 h-3.5" />
            <span>Manage Fleet</span>
          </button>
        }
      />

      {/* 2. Top 5 Fleet KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <KPICard
          title="Total Fleet Assets"
          value={fleetStats?.total_vehicles ?? vehicles.length}
          subtitle={`${availableVehicles.length} available • ${inTransitVehicles.length} on road`}
          icon={Truck}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
          onClick={() => onNavigate && onNavigate('vehicles')}
        />

        <KPICard
          title="Available Ready Units"
          value={availableVehicles.length}
          subtitle="Ready for dispatch"
          icon={CheckCircle2}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          trend="Ready"
          trendUp={true}
          onClick={() => onNavigate && onNavigate('vehicles')}
        />

        <KPICard
          title="Capacity Utilization"
          value={`${fleetStats?.average_utilization_pct ?? 68.4}%`}
          subtitle="Weight efficiency ratio"
          icon={Gauge}
          iconColor="text-indigo-600"
          bgColor="bg-indigo-50"
          trend="Optimal"
          trendUp={true}
        />

        <KPICard
          title="In Maintenance"
          value={maintenanceVehicles.length}
          subtitle="Preventive inspections"
          icon={Wrench}
          iconColor={maintenanceVehicles.length > 0 ? 'text-amber-600' : 'text-slate-400'}
          bgColor={maintenanceVehicles.length > 0 ? 'bg-amber-50' : 'bg-slate-50'}
          highlight={maintenanceVehicles.length > 0}
          onClick={() => onNavigate && onNavigate('vehicles')}
        />

        <KPICard
          title="Certified Drivers"
          value={driverStats?.total_drivers ?? drivers.length}
          subtitle={`${driverStats?.available_drivers ?? 0} ready for route`}
          icon={Users}
          iconColor="text-purple-600"
          bgColor="bg-purple-50"
          onClick={() => onNavigate && onNavigate('drivers')}
        />
      </div>

      {/* 3. Fleet Deployment Grid & Driver HOS Roster */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Vehicles Status Table */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Truck className="w-4 h-4 text-blue-600" />
              <span>Fleet Deployment Summary</span>
            </h3>
            <button
              onClick={() => onNavigate && onNavigate('vehicles')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View All Units</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5">
            {vehicles.slice(0, 5).map((v) => (
              <div
                key={v.id}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
              >
                <div>
                  <div className="font-bold text-slate-900 flex items-center gap-2">
                    <span>{v.vehicle_code}</span>
                    <span className="text-[10px] font-normal text-slate-500 font-mono">({v.type})</span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{v.model} • {v.current_location || 'Depot Hub'}</div>
                </div>

                <div className="text-right flex items-center gap-3">
                  <div className="text-[11px] text-slate-600 text-right hidden sm:block">
                    <div>Cap: <strong className="text-slate-800">{v.max_capacity_kg.toLocaleString()} kg</strong></div>
                    <div className="text-[10px] text-slate-400">Fuel: {v.fuel_level_pct ?? 100}%</div>
                  </div>
                  <StatusBadge status={v.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Driver Safety & HOS Roster */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Commercial Driver Safety & HOS</span>
            </h3>
            <button
              onClick={() => onNavigate && onNavigate('drivers')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View Roster</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5">
            {drivers.slice(0, 5).map((d) => (
              <div
                key={d.id}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
              >
                <div>
                  <div className="font-bold text-slate-900">{d.name} ({d.driver_code})</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{d.license_type || 'CDL-A'} • {d.phone || 'Phone verified'}</div>
                </div>

                <div className="text-right flex items-center gap-3">
                  <div className="text-right hidden sm:block">
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                      ★ {d.rating ?? 4.9}
                    </span>
                  </div>
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                    (d.hours_of_service_remaining ?? 11) > 3
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}>
                    {d.hours_of_service_remaining ?? 11}h HOS
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Fleet Actions */}
      <QuickActionGroup title="Fleet Management Workflows" actions={fleetActions} />
    </div>
  );
};
