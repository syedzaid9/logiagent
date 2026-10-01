import React, { useState } from 'react';
import { Shipment, ShipmentStatus } from '../../types';
import { 
  Package, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  Truck, 
  Clock, 
  XCircle, 
  ExternalLink,
  ChevronRight,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

interface DashboardShipmentTableProps {
  shipments: Shipment[];
  loading: boolean;
  onViewRoute?: (code: string) => void;
  onNavigateToShipments?: () => void;
}

export const DashboardShipmentTable: React.FC<DashboardShipmentTableProps> = ({
  shipments,
  loading,
  onViewRoute,
  onNavigateToShipments,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filterTabs = [
    { label: 'All', value: 'ALL' },
    { label: 'In Transit', value: 'In Transit' },
    { label: 'Delayed', value: 'Delayed' },
    { label: 'Delivered', value: 'Delivered' },
    { label: 'Pending', value: 'Pending' },
  ];

  const filteredShipments = shipments.filter((s) => {
    const matchesSearch =
      s.shipment_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.customer_name && s.customer_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (s.origin_city && s.origin_city.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (s.destination_city && s.destination_city.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (s.driver_name && s.driver_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (s.vehicle_code && s.vehicle_code.toLowerCase().includes(searchTerm.toLowerCase()));

    if (statusFilter === 'ALL') return matchesSearch;
    if (statusFilter === 'Delayed') {
      return matchesSearch && (s.status === 'Delayed' || s.delay_minutes > 0);
    }
    return matchesSearch && s.status.toLowerCase() === statusFilter.toLowerCase();
  });

  const getStatusBadge = (status: ShipmentStatus, delayMinutes: number) => {
    if (status === 'Delayed' || delayMinutes > 0) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
          <span>Delayed {delayMinutes > 0 ? `(+${delayMinutes}m)` : ''}</span>
        </span>
      );
    }
    switch (status) {
      case 'Delivered':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
            <span>Delivered</span>
          </span>
        );
      case 'In Transit':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <Truck className="w-3 h-3 text-blue-600 shrink-0" />
            <span>In Transit</span>
          </span>
        );
      case 'Picked Up':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
            <Truck className="w-3 h-3 text-indigo-600 shrink-0" />
            <span>Picked Up</span>
          </span>
        );
      case 'Assigned':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <Clock className="w-3 h-3 text-slate-500 shrink-0" />
            <span>Assigned</span>
          </span>
        );
      case 'Pending':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <Clock className="w-3 h-3 text-slate-400 shrink-0" />
            <span>Pending</span>
          </span>
        );
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600 shrink-0" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs p-5 space-y-4">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-slate-900">
              Shipment Overview
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded-full font-medium bg-slate-100 text-slate-600">
              {filteredShipments.length} Active
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time corridor tracking, carrier assignments, and ETA updates.
          </p>
        </div>

        {/* Filter Tabs and Search */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Segmented Filter */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg">
            {filterTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setStatusFilter(tab.value)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  statusFilter === tab.value
                    ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter shipments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 pr-3 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-blue-500 w-44 sm:w-52 transition-all"
            />
          </div>
        </div>
      </div>

      {/* Shipment Table */}
      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-2">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-500">Loading shipment data...</span>
        </div>
      ) : filteredShipments.length === 0 ? (
        <div className="py-10 text-center bg-slate-50/50 rounded-lg border border-dashed border-slate-200">
          <Package className="w-7 h-7 text-slate-400 mx-auto mb-1.5 opacity-60" />
          <p className="text-xs font-semibold text-slate-700">No shipments found</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Try resetting the status filter or search term.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold text-[11px]">
                <th className="py-2.5 px-3">Shipment ID</th>
                <th className="py-2.5 px-3">Customer</th>
                <th className="py-2.5 px-3">Corridor</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Cargo / Weight</th>
                <th className="py-2.5 px-3">ETA</th>
                <th className="py-2.5 px-3">Driver</th>
                <th className="py-2.5 px-3">Vehicle</th>
                <th className="py-2.5 px-3 text-right">Route</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredShipments.slice(0, 10).map((s) => (
                <tr
                  key={s.id}
                  className="hover:bg-slate-50/80 transition-colors"
                >
                  {/* Shipment Code */}
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-semibold text-slate-900">
                        {s.shipment_code}
                      </span>
                      {s.delay_risk_score >= 50 && (
                        <span title={`Delay Risk: ${s.delay_risk_score}/100`}>
                          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Customer */}
                  <td className="py-2.5 px-3">
                    <span className="font-medium text-slate-800 truncate block max-w-[130px]">
                      {s.customer_name || '—'}
                    </span>
                  </td>

                  {/* Corridor */}
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-1 text-slate-700">
                      <span>{s.origin_city || 'Origin'}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>{s.destination_city || 'Dest'}</span>
                    </div>
                  </td>

                  {/* Status Badge */}
                  <td className="py-2.5 px-3">
                    {getStatusBadge(s.status, s.delay_minutes)}
                  </td>

                  {/* Cargo */}
                  <td className="py-2.5 px-3">
                    <div className="text-slate-700">
                      <span>{s.cargo_type}</span>
                      <span className="text-slate-400 ml-1 font-mono text-[10px]">
                        ({s.weight_kg.toLocaleString()} kg)
                      </span>
                    </div>
                  </td>

                  {/* ETA */}
                  <td className="py-2.5 px-3">
                    <div className="text-slate-700 font-mono text-[11px]">
                      {s.estimated_eta
                        ? new Date(s.estimated_eta).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })
                        : s.expected_delivery
                        ? new Date(s.expected_delivery).toLocaleDateString()
                        : 'Scheduled'}
                    </div>
                    {s.delay_reason && (
                      <span className="text-[10px] text-amber-700 truncate block max-w-[130px]" title={s.delay_reason}>
                        {s.delay_reason}
                      </span>
                    )}
                  </td>

                  {/* Driver */}
                  <td className="py-2.5 px-3 text-slate-700">
                    {s.driver_name || <span className="text-slate-400 italic">Unassigned</span>}
                  </td>

                  {/* Vehicle */}
                  <td className="py-2.5 px-3 text-slate-700 font-mono text-[11px]">
                    {s.vehicle_code ? (
                      <span className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-700 font-medium">
                        {s.vehicle_code}
                      </span>
                    ) : (
                      <span className="text-slate-400 italic">Unassigned</span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="py-2.5 px-3 text-right">
                    {onViewRoute && (
                      <button
                        onClick={() => onViewRoute(s.shipment_code)}
                        className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        title="View route details"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Table Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
        <span>
          Showing top {Math.min(10, filteredShipments.length)} of {filteredShipments.length} matching shipments
        </span>
        {onNavigateToShipments && (
          <button
            onClick={onNavigateToShipments}
            className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 transition-colors"
          >
            <span>View All Shipments</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
