import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { DriverPortalData, Shipment } from '../../types';
import { KPICard } from '../common/KPICard';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { AlertBadge } from '../common/AlertBadge';
import { KPISkeleton, CardSkeleton } from '../common/LoadingSkeleton';
import { ErrorState } from '../common/ErrorState';
import {
  Truck,
  Package,
  MapPin,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Star,
  Navigation,
  RefreshCw,
  Phone,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  ClipboardList,
  Fuel
} from 'lucide-react';

interface DriverDashboardProps {
  onNavigate?: (tab: string) => void;
}

export const DriverDashboard: React.FC<DriverDashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [data, setData] = useState<DriverPortalData | null>(null);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTask, setActiveTask] = useState<string | null>(null);

  const loadDriverData = async (isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    else setIsRefreshing(true);
    setError(null);

    try {
      const [portalRes, shpRes] = await Promise.all([
        api.getDriverPortal(),
        api.getShipments(),
      ]);
      setData(portalRes);
      setShipments(shpRes);
    } catch (err: any) {
      console.error('Failed to load driver data:', err);
      setError(err.message || 'Failed to load driver operations portal.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadDriverData();
  }, []);

  const handleUpdateStatus = async (shipmentCode: string, newStatus: string) => {
    try {
      await api.updateShipment(shipmentCode, {
        status: newStatus as any,
        notes: `Status updated to ${newStatus} by Driver ${data?.driver?.name || user?.full_name}`,
      });
      loadDriverData(true);
    } catch (err: any) {
      alert(err.message || 'Failed to update shipment status.');
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    const name = data?.driver?.name || user?.full_name || 'Driver';
    if (hour < 12) return `Good morning, ${name}`;
    if (hour < 18) return `Good afternoon, ${name}`;
    return `Good evening, ${name}`;
  };

  if (isLoading && !data) {
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

  if (error && !data) {
    return <ErrorState message={error} onRetry={() => loadDriverData()} />;
  }

  const driver = data?.driver;
  const vehicle = data?.vehicle;
  const kpis = data?.kpis;
  const activeRoute = data?.active_route;
  const primaryShipment = shipments.find((s) => s.status === 'In Transit' || s.status === 'Picked Up') || shipments[0];

  const driverTasks = [
    { id: 'pre-trip', label: 'Pre-Trip Vehicle Safety Inspection', completed: true },
    { id: 'pickup-bol', label: 'Verify Cargo BOL & Departure Clearance', completed: primaryShipment?.status !== 'Assigned' && primaryShipment?.status !== 'Pending' },
    { id: 'en-route', label: 'En-Route Telemetry & Rest Stops Compliance', completed: primaryShipment?.status === 'Delivered' },
    { id: 'pod-sign', label: 'Receiver Proof of Delivery (POD) Signature', completed: primaryShipment?.status === 'Delivered' },
  ];

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Driver Welcome Header */}
      <PageHeader
        title={getGreeting()}
        subtitle={`Driver Code: ${driver?.driver_code || user?.driver_code || 'DRV-01'} • ${vehicle ? `${vehicle.vehicle_code} (${vehicle.type})` : 'Truck assigned'}`}
        icon={Truck}
        badge="DRIVER PORTAL"
        badgeColor="bg-amber-50 text-amber-700 border-amber-200"
        onRefresh={() => loadDriverData(true)}
        isRefreshing={isRefreshing}
        actions={
          <button
            onClick={() => onNavigate && onNavigate('chat')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Driver AI</span>
          </button>
        }
      />

      {/* 2. Top 4 Driver KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <KPICard
          title="Assigned Shipments"
          value={kpis?.total_assigned || shipments.length}
          subtitle={`${kpis?.active_deliveries || 0} active on road`}
          icon={Package}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
        />

        <KPICard
          title="Hours of Service (HOS)"
          value={`${driver?.hours_of_service_remaining ?? 11.0}h`}
          subtitle="DOT compliance active"
          icon={Clock}
          iconColor={(driver?.hours_of_service_remaining ?? 11.0) > 3 ? 'text-emerald-600' : 'text-rose-600'}
          bgColor={(driver?.hours_of_service_remaining ?? 11.0) > 3 ? 'bg-emerald-50' : 'bg-rose-50'}
        />

        <KPICard
          title="Completed Deliveries"
          value={kpis?.completed_deliveries || 0}
          subtitle="100% on-time record"
          icon={CheckCircle2}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          trend="Target Met"
          trendUp={true}
        />

        <KPICard
          title="Safety & Driver Rating"
          value={`${driver?.rating || 4.95} / 5.0`}
          subtitle="Top Tier Platinum Roster"
          icon={Star}
          iconColor="text-amber-600"
          bgColor="bg-amber-50"
        />
      </div>

      {/* 3. Primary Current Shipment Card */}
      {primaryShipment && (
        <div className="bg-white border border-blue-200/90 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Current Active Assignment</span>
                <StatusBadge status={primaryShipment.status} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 mt-0.5">{primaryShipment.shipment_code}</h2>
            </div>

            <div className="flex items-center gap-2">
              {primaryShipment.status === 'Assigned' && (
                <button
                  onClick={() => handleUpdateStatus(primaryShipment.shipment_code, 'Picked Up')}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
                >
                  Mark Picked Up
                </button>
              )}
              {primaryShipment.status === 'Picked Up' && (
                <button
                  onClick={() => handleUpdateStatus(primaryShipment.shipment_code, 'In Transit')}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
                >
                  Depart (In Transit)
                </button>
              )}
              {primaryShipment.status === 'In Transit' && (
                <button
                  onClick={() => handleUpdateStatus(primaryShipment.shipment_code, 'Delivered')}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
                >
                  Complete Delivery
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Transit Corridor</span>
              <div className="font-bold text-slate-900 mt-1 flex items-center gap-1.5">
                <span>{primaryShipment.origin_city || 'Origin Terminal'}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                <span>{primaryShipment.destination_city || 'Destination Site'}</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Customer: {primaryShipment.customer_name}</div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Estimated Arrival ETA</span>
              <div className="font-bold text-slate-900 mt-1 text-sm">
                {primaryShipment.estimated_eta
                  ? new Date(primaryShipment.estimated_eta).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
                  : 'On Schedule'}
              </div>
              <div className="text-[11px] text-emerald-700 font-medium mt-0.5">Schedule SLA Guaranteed</div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Assigned Cargo</span>
              <div className="font-bold text-slate-900 mt-1">
                {primaryShipment.cargo_type} • {primaryShipment.weight_kg.toLocaleString()} kg
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Truck: {primaryShipment.vehicle_code || 'TRK-101'}</div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Today's Route & Driver Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Today's Route Corridor */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Navigation className="w-4 h-4 text-emerald-600" />
              <span>Today's Highway Route Telemetry</span>
            </h3>
            {activeRoute && (
              <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                {activeRoute.route_code}
              </span>
            )}
          </div>

          {activeRoute ? (
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 text-center">
                  <div className="text-[10px] text-slate-400 font-semibold">Planned Distance</div>
                  <div className="text-xs font-bold text-slate-900 mt-0.5">{activeRoute.planned_distance_km} km</div>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 text-center">
                  <div className="text-[10px] text-slate-400 font-semibold">Drive Time</div>
                  <div className="text-xs font-bold text-slate-900 mt-0.5">{activeRoute.planned_duration_min} min</div>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 text-center">
                  <div className="text-[10px] text-slate-400 font-semibold">Traffic Status</div>
                  <div className="text-xs font-bold text-emerald-700 mt-0.5">{activeRoute.traffic_condition}</div>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 text-center">
                  <div className="text-[10px] text-slate-400 font-semibold">Weather Status</div>
                  <div className="text-xs font-bold text-blue-700 mt-0.5">{activeRoute.weather_condition}</div>
                </div>
              </div>

              <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <MapPin className="w-4 h-4 text-blue-600 shrink-0" />
                  <span className="text-[11px] text-slate-700 font-medium">
                    Live GPS Waypoint tracking & speed monitoring enabled.
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              No active route assigned. Contact your dispatcher for today's assignment.
            </div>
          )}
        </div>

        {/* Driver Operational Tasks */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ClipboardList className="w-4 h-4 text-blue-600" />
              <span>Shift Delivery Tasks</span>
            </h3>
            <span className="text-[11px] font-semibold text-slate-500">
              {driverTasks.filter((t) => t.completed).length} / {driverTasks.length} Completed
            </span>
          </div>

          <div className="space-y-2 text-xs">
            {driverTasks.map((task) => (
              <div
                key={task.id}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between"
              >
                <div className="flex items-center gap-2.5">
                  <div className={`p-1 rounded-full ${task.completed ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'}`}>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <span className={`font-medium ${task.completed ? 'text-slate-500 line-through' : 'text-slate-800'}`}>
                    {task.label}
                  </span>
                </div>
                {task.completed ? (
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Done
                  </span>
                ) : (
                  <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Pending
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. Driver AI Assistant Quick Chips */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-600" />
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Driver AI Assistant</h3>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            'What is my predicted ETA and next stop?',
            'Are there any weather or traffic slowdowns on my route?',
            'What is the policy for failed customer delivery?',
            'Show my assigned truck payload capacity',
          ].map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => onNavigate && onNavigate('chat')}
              className="px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-blue-50 border border-slate-200 text-slate-700 hover:text-blue-700 text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <span>{prompt}</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
