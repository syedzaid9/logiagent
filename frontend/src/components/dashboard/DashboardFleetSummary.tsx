import React from 'react';
import { Truck, CheckCircle2, Navigation, Wrench, ArrowUpRight } from 'lucide-react';

interface FleetUtilizationData {
  vehicle_type: string;
  total_count: number;
  active_count: number;
  average_load_pct: number;
}

interface DashboardFleetSummaryProps {
  totalVehicles: number;
  availableVehicles: number;
  activeVehicles: number;
  fleetUtilizationPct: number;
  utilizationByType: FleetUtilizationData[];
  onNavigateToFleet?: () => void;
}

export const DashboardFleetSummary: React.FC<DashboardFleetSummaryProps> = ({
  totalVehicles,
  availableVehicles,
  activeVehicles,
  fleetUtilizationPct,
  utilizationByType,
  onNavigateToFleet,
}) => {
  const maintenanceCount = Math.max(0, totalVehicles - availableVehicles - activeVehicles);

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Fleet Readiness
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Carrier vehicle allocation and payload utilization.
          </p>
        </div>

        {onNavigateToFleet && (
          <button
            onClick={onNavigateToFleet}
            className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 transition-colors"
          >
            <span>View Fleet</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Fleet Status Summary Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Total Vehicles */}
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
          <span className="text-[11px] font-medium text-slate-500 block">Total Fleet</span>
          <p className="text-xl font-bold text-slate-900 mt-0.5">{totalVehicles}</p>
          <span className="text-[10px] text-slate-400">units</span>
        </div>

        {/* Available */}
        <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-200/80">
          <span className="text-[11px] font-medium text-emerald-800 block">Available</span>
          <p className="text-xl font-bold text-emerald-800 mt-0.5">{availableVehicles}</p>
          <span className="text-[10px] text-emerald-600">ready to dispatch</span>
        </div>

        {/* In Transit */}
        <div className="p-3 rounded-lg bg-blue-50/50 border border-blue-200/80">
          <span className="text-[11px] font-medium text-blue-800 block">In Transit</span>
          <p className="text-xl font-bold text-blue-800 mt-0.5">{activeVehicles}</p>
          <span className="text-[10px] text-blue-600">en route</span>
        </div>

        {/* Maintenance */}
        <div className="p-3 rounded-lg bg-amber-50/50 border border-amber-200/80">
          <span className="text-[11px] font-medium text-amber-800 block">Maintenance</span>
          <p className="text-xl font-bold text-amber-800 mt-0.5">{maintenanceCount}</p>
          <span className="text-[10px] text-amber-600">in service</span>
        </div>
      </div>

      {/* Fleet Utilization Progress Bars by Type */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-700">Capacity by Vehicle Class</span>
          <span className="text-slate-900 font-bold font-mono">{fleetUtilizationPct}% Average</span>
        </div>

        <div className="space-y-2">
          {utilizationByType.map((item, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">
                  {item.vehicle_type}
                  <span className="text-slate-400 ml-1.5 font-normal">
                    ({item.active_count}/{item.total_count} active)
                  </span>
                </span>
                <span className="font-mono font-semibold text-slate-800 text-[11px]">
                  {item.average_load_pct}%
                </span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${Math.min(100, Math.max(4, item.average_load_pct))}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
