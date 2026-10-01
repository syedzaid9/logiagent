import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../../api/services';
import { Vehicle, FleetStats } from '../../types';
import { CreateVehicleModal } from './CreateVehicleModal';
import { EditVehicleModal } from './EditVehicleModal';
import { VehicleDetailModal } from './VehicleDetailModal';
import { 
  Truck, 
  Fuel, 
  User, 
  MapPin, 
  Activity, 
  Filter, 
  RefreshCw,
  Zap,
  Gauge,
  Plus,
  CheckCircle2,
  XCircle,
  Search,
  Scale,
  Package,
  ShieldAlert,
  ArrowUpRight,
  SlidersHorizontal,
  Edit3
} from 'lucide-react';

interface VehicleGridProps {
  onViewShipment?: (shipmentCode: string) => void;
  onAskAI?: (prompt: string) => void;
}

export const VehicleGrid: React.FC<VehicleGridProps> = ({
  onViewShipment,
  onAskAI,
}) => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [fleetStats, setFleetStats] = useState<FleetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [availableOnly, setAvailableOnly] = useState(false);

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const statuses = ['All', 'Available', 'In Transit', 'Assigned', 'Maintenance', 'Deactivated'];
  const types = ['All', 'Semi-Truck (Dry Van)', 'Reefer (Refrigerated)', 'Flatbed', 'Box Truck', 'Sprinter Van'];

  const loadVehicles = async () => {
    try {
      setLoading(true);
      const [vehiclesData, statsData] = await Promise.all([
        api.getVehicles({
          status: statusFilter === 'All' ? undefined : statusFilter,
          vehicle_type: typeFilter === 'All' ? undefined : typeFilter,
          search: searchQuery.trim() || undefined,
        }),
        api.getFleetStats().catch(() => null),
      ]);
      setVehicles(vehiclesData || []);
      if (statsData) setFleetStats(statsData);
    } catch (err) {
      console.error('Error loading fleet vehicles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVehicles();
  }, [statusFilter, typeFilter]);

  // Client-side filtering for fast instant search feedback
  const filteredVehicles = useMemo(() => {
    return vehicles.filter((v) => {
      // Available only filter
      if (availableOnly && v.status !== 'Available') return false;

      // Search filter
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        v.vehicle_code.toLowerCase().includes(q) ||
        v.model.toLowerCase().includes(q) ||
        v.type.toLowerCase().includes(q) ||
        v.current_location.toLowerCase().includes(q) ||
        (v.driver_name && v.driver_name.toLowerCase().includes(q)) ||
        (v.active_shipment_code && v.active_shipment_code.toLowerCase().includes(q))
      );
    });
  }, [vehicles, searchQuery, availableOnly]);

  // Dynamic calculated KPI metrics
  const totalCount = vehicles.length;
  const availableCount = vehicles.filter((v) => v.status === 'Available').length;
  const inTransitCount = vehicles.filter((v) => v.status === 'In Transit' || v.status === 'Assigned').length;
  const maintenanceCount = vehicles.filter((v) => v.status === 'Maintenance').length;
  const totalCap = vehicles.reduce((sum, v) => sum + (v.max_capacity_kg || 0), 0);
  const totalLoad = vehicles.reduce((sum, v) => sum + (v.current_load_kg || 0), 0);
  const avgUtilization = totalCap > 0 ? Math.round((totalLoad / totalCap) * 100) : 0;

  const handleCreateSuccess = (newVehicle: Vehicle) => {
    setVehicles((prev) => [newVehicle, ...prev]);
    setToastMessage(`Vehicle ${newVehicle.vehicle_code} successfully registered and persisted to Supabase!`);
    setTimeout(() => setToastMessage(null), 5000);
    api.getFleetStats().then(setFleetStats).catch(() => null);
  };

  const handleUpdateSuccess = (updatedVehicle: Vehicle) => {
    setVehicles((prev) =>
      prev.map((v) => (v.vehicle_code === updatedVehicle.vehicle_code ? updatedVehicle : v))
    );
    if (selectedVehicle?.vehicle_code === updatedVehicle.vehicle_code) {
      setSelectedVehicle(updatedVehicle);
    }
    setToastMessage(`Vehicle ${updatedVehicle.vehicle_code} updated successfully!`);
    setTimeout(() => setToastMessage(null), 5000);
    api.getFleetStats().then(setFleetStats).catch(() => null);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Available':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'In Transit':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Assigned':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'Maintenance':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'Deactivated':
        return 'bg-slate-100 text-slate-600 border-slate-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-card animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-600 hover:text-emerald-900 cursor-pointer">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-600">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>Fleet & Commercial Vehicle Management</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {totalCount} commercial transport vehicles with dynamic payload telematics & active dispatch tracking.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadVehicles}
            className="px-3 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 hover:text-slate-900 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Fleet</span>
          </button>

          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Vehicle</span>
          </button>
        </div>
      </div>

      {/* Dynamic Fleet KPI Telemetry Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        {/* Total Fleet */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-1">
            <span>Total Fleet</span>
            <Truck className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">{fleetStats?.total_vehicles ?? totalCount}</div>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Registered Commercial Units</span>
        </div>

        {/* Available Units */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-1">
            <span>Available</span>
            <Zap className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-700 font-mono">
            {fleetStats?.available_vehicles ?? availableCount}
          </div>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Ready for Cargo Dispatch</span>
        </div>

        {/* In Transit / Active */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-1">
            <span>Active Dispatched</span>
            <Activity className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-blue-700 font-mono">
            {(fleetStats?.in_transit_vehicles ?? inTransitCount) + (fleetStats?.assigned_vehicles ?? 0)}
          </div>
          <span className="text-[10px] text-slate-400 mt-0.5 block">In Transit or Assigned</span>
        </div>

        {/* Maintenance */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-1">
            <span>Maintenance</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-700 font-mono">
            {fleetStats?.maintenance_vehicles ?? maintenanceCount}
          </div>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Service / Inspection</span>
        </div>

        {/* Fleet Utilization */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-1">
            <span>Payload Utilization</span>
            <Gauge className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-indigo-700 font-mono">
            {fleetStats?.average_utilization_pct ?? avgUtilization}%
          </div>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Network Payload Capacity</span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card space-y-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Live Search Input */}
          <div className="relative w-full md:w-80">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search code, model, driver, shipment..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 placeholder-slate-400 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-medium shadow-2xs"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-700 text-xs cursor-pointer"
              >
                ✕
              </button>
            )}
          </div>

          {/* Quick Toggle: Available Only */}
          <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
            <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-slate-700 font-medium">
              <input
                type="checkbox"
                checked={availableOnly}
                onChange={(e) => setAvailableOnly(e.target.checked)}
                className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
              />
              <span>Available Capacity Only</span>
            </label>

            <span className="text-xs font-mono text-slate-500">
              Showing <strong className="text-slate-900">{filteredVehicles.length}</strong> of {vehicles.length}
            </span>
          </div>
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] text-slate-400 uppercase font-bold mr-1">Status:</span>
            {statuses.map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  statusFilter === st
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Type Filters */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] text-slate-400 uppercase font-bold mr-1">Class:</span>
            {types.map((tp) => (
              <button
                key={tp}
                onClick={() => setTypeFilter(tp)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all cursor-pointer ${
                  typeFilter === tp
                    ? 'bg-indigo-600 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
                }`}
              >
                {tp.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Vehicle Cards Grid */}
      {loading ? (
        <div className="p-16 text-center text-slate-500 font-mono text-xs flex items-center justify-center gap-2 bg-white rounded-2xl border border-slate-200 shadow-card">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Querying Supabase vehicle fleet records...</span>
        </div>
      ) : filteredVehicles.length === 0 ? (
        <div className="p-16 text-center text-slate-500 text-xs bg-white rounded-2xl border border-slate-200 shadow-card space-y-2">
          <Truck className="w-8 h-8 mx-auto text-slate-400" />
          <p className="font-semibold text-slate-800 text-sm">No vehicles match the selected criteria</p>
          <p className="text-slate-500">Try adjusting your search terms or status/class filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVehicles.map((v) => {
            const usedPct = v.utilization_pct || 0;
            const freeCap = Math.max(0, v.max_capacity_kg - v.current_load_kg);

            return (
              <div
                key={v.id}
                className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 transition-all shadow-card hover:shadow-md space-y-4 group flex flex-col justify-between"
              >
                <div className="space-y-3.5">
                  {/* Card Header */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-bold text-slate-900 font-mono">{v.vehicle_code}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(v.status)}`}>
                          {v.status}
                        </span>
                      </div>
                      <span className="text-xs text-blue-600 font-semibold">{v.type}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => setEditingVehicle(v)}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 border border-slate-200 transition-colors cursor-pointer"
                        title="Edit Vehicle"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedVehicle(v)}
                        className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-600 hover:text-blue-800 border border-blue-200 transition-colors cursor-pointer"
                        title="View Operational Details"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Make & Model */}
                  <div className="text-xs text-slate-500 font-mono">
                    {v.model} • Odometer: {v.mileage_km?.toLocaleString()} km
                  </div>

                  {/* Capacity Progress Meter */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Load Capacity:</span>
                      <strong className="text-slate-900 font-mono">
                        {v.current_load_kg.toLocaleString()} / {v.max_capacity_kg.toLocaleString()} kg
                      </strong>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                      <div
                        className={`h-full transition-all rounded-full ${
                          usedPct > 90 ? 'bg-rose-500' : usedPct > 60 ? 'bg-blue-600' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, usedPct)}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>Available: <strong className="text-emerald-700 font-mono">{freeCap.toLocaleString()} kg</strong></span>
                      <span className="font-mono text-slate-600 font-medium">{usedPct}% used</span>
                    </div>
                  </div>

                  {/* Active Shipment Tag (if assigned) */}
                  {v.active_shipment_code && (
                    <div className="p-2 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 text-blue-800 truncate">
                        <Package className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                        <span className="font-mono font-bold truncate">Active: {v.active_shipment_code}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-semibold shrink-0">
                        {v.active_shipment_status || 'In Transit'}
                      </span>
                    </div>
                  )}

                  {/* Info Pills */}
                  <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Fuel className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>Fuel: <strong className="text-slate-900 font-mono">{v.fuel_level_pct}%</strong></span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600 truncate">
                      <User className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                      <span className="truncate">Driver: <strong className="text-slate-900 truncate">{v.driver_name || 'Unassigned'}</strong></span>
                    </div>
                  </div>

                  {/* Location Hub */}
                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2 text-[11px] text-slate-700">
                    <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="truncate font-medium">{v.current_location}</span>
                  </div>
                </div>

                {/* Inspect Action Footer */}
                <button
                  type="button"
                  onClick={() => setSelectedVehicle(v)}
                  className="w-full mt-3 py-2 rounded-xl bg-slate-50 hover:bg-blue-50 hover:text-blue-700 text-slate-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all border border-slate-200 hover:border-blue-300 cursor-pointer shadow-2xs"
                >
                  <span>Inspect Vehicle Telemetry</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Vehicle Modal */}
      {isCreateModalOpen && (
        <CreateVehicleModal
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleCreateSuccess}
          existingCodes={vehicles.map((v) => v.vehicle_code)}
        />
      )}

      {/* Edit Vehicle Modal */}
      {editingVehicle && (
        <EditVehicleModal
          vehicle={editingVehicle}
          onClose={() => setEditingVehicle(null)}
          onSuccess={handleUpdateSuccess}
        />
      )}

      {/* Detailed Vehicle Modal */}
      {selectedVehicle && (
        <VehicleDetailModal
          vehicle={selectedVehicle}
          onClose={() => setSelectedVehicle(null)}
          onUpdate={handleUpdateSuccess}
          onViewShipment={onViewShipment}
          onAskAI={onAskAI}
        />
      )}
    </div>
  );
};
