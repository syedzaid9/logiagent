import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { Driver, Vehicle } from '../../types';
import { EditVehicleModal } from './EditVehicleModal';
import {
  X,
  Truck,
  Fuel,
  User,
  MapPin,
  Scale,
  Box,
  Gauge,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Edit3,
  Ban,
  Navigation,
  Package,
  Bot,
  ArrowRight,
  ShieldCheck,
  Save
} from 'lucide-react';

interface VehicleDetailModalProps {
  vehicle: Vehicle;
  onClose: () => void;
  onUpdate: (updated: Vehicle) => void;
  onViewShipment?: (shipmentCode: string) => void;
  onAskAI?: (prompt: string) => void;
}

export const VehicleDetailModal: React.FC<VehicleDetailModalProps> = ({
  vehicle: initialVehicle,
  onClose,
  onUpdate,
  onViewShipment,
  onAskAI,
}) => {
  const [vehicle, setVehicle] = useState<Vehicle>(initialVehicle);
  const [loading, setLoading] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  
  // Quick status update state
  const [newStatus, setNewStatus] = useState(initialVehicle.status);
  const [locationName, setLocationName] = useState(initialVehicle.current_location);
  const [selectedDriverId, setSelectedDriverId] = useState<number | ''>(initialVehicle.driver_id || '');
  const [fuelLevel, setFuelLevel] = useState<number>(initialVehicle.fuel_level_pct);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [updating, setUpdating] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const statuses = ['Available', 'Assigned', 'In Transit', 'Maintenance', 'Deactivated'];

  const fetchFullDetails = async () => {
    try {
      setLoading(true);
      const full = await api.getVehicle(initialVehicle.vehicle_code);
      setVehicle(full);
      setNewStatus(full.status);
      setLocationName(full.current_location);
      setSelectedDriverId(full.driver_id || '');
      setFuelLevel(full.fuel_level_pct);
    } catch (err) {
      console.error('Failed to load full vehicle details:', err);
      setVehicle(initialVehicle);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFullDetails();
    api.getDrivers().then(setDrivers).catch(() => []);
  }, [initialVehicle.vehicle_code]);

  const handleQuickSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setUpdating(true);
      setErrorMsg(null);
      setActionSuccessMsg(null);

      const payload: Partial<Vehicle> = {
        status: newStatus as any,
        current_location: locationName.trim() || undefined,
        driver_id: selectedDriverId === '' ? undefined : Number(selectedDriverId),
        fuel_level_pct: Number(fuelLevel),
      };

      const updated = await api.updateVehicle(vehicle.vehicle_code, payload);
      setVehicle(updated);
      onUpdate(updated);
      setActionSuccessMsg(`Vehicle ${updated.vehicle_code} updated successfully and persisted to Supabase!`);
      setTimeout(() => setActionSuccessMsg(null), 4000);
    } catch (err: any) {
      console.error('Failed to update vehicle:', err);
      setErrorMsg(err.message || 'Failed to update vehicle. Please try again.');
    } finally {
      setUpdating(false);
    }
  };

  const handleDeactivate = async () => {
    if (!window.confirm(`Are you sure you want to deactivate vehicle ${vehicle.vehicle_code}? This will release any driver assignments and flag the vehicle as inactive.`)) {
      return;
    }

    try {
      setUpdating(true);
      setErrorMsg(null);
      const res = await api.deactivateVehicle(vehicle.vehicle_code);
      setVehicle(res.vehicle);
      onUpdate(res.vehicle);
      setActionSuccessMsg(`Vehicle ${vehicle.vehicle_code} deactivated.`);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err: any) {
      console.error('Failed to deactivate vehicle:', err);
      setErrorMsg(err.message || 'Unable to deactivate vehicle.');
    } finally {
      setUpdating(false);
    }
  };

  const handleAskAI = () => {
    if (onAskAI) {
      const prompt = `Give me a comprehensive operational and maintenance status for commercial vehicle ${vehicle.vehicle_code} (${vehicle.type}), including its current payload utilization, assigned driver, active shipments, and fuel level.`;
      onClose();
      onAskAI(prompt);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'Available':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'In Transit':
        return 'bg-teal-100 text-teal-800 border-teal-300';
      case 'Assigned':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Maintenance':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'Deactivated':
        return 'bg-slate-200 text-slate-700 border-slate-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const usedPct = vehicle.utilization_pct || 0;
  const freeCap = Math.max(0, vehicle.max_capacity_kg - vehicle.current_load_kg);
  const freeVol = Math.max(0, (vehicle.max_volume_m3 || 80.0) - (vehicle.current_volume_m3 || 0.0));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto animate-in fade-in">
      <div className="relative w-full max-w-4xl rounded-2xl bg-white border border-slate-200 shadow-modal overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/90 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-600 shadow-2xs">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 font-mono tracking-tight">
                  {vehicle.vehicle_code}
                </h3>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(vehicle.status)}`}>
                  {vehicle.status}
                </span>
                <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  {vehicle.type}
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                {vehicle.model} • Odometer: {vehicle.mileage_km?.toLocaleString()} km • {vehicle.fuel_type}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onAskAI && (
              <button
                type="button"
                onClick={handleAskAI}
                className="px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
              >
                <Bot className="w-3.5 h-3.5 text-indigo-600" />
                <span>Ask AI</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
            >
              <Edit3 className="w-3.5 h-3.5 text-slate-600" />
              <span>Edit Vehicle</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Notifications */}
        {actionSuccessMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2 shadow-2xs animate-in fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionSuccessMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex items-center gap-2 shadow-2xs animate-in fade-in">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Body Content */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* 4-Card Operational Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {/* Payload Capacity */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Gross Payload</span>
              <div className="flex items-center gap-1.5 text-slate-900 font-mono font-bold text-sm">
                <Scale className="w-3.5 h-3.5 text-blue-600" />
                <span>{vehicle.max_capacity_kg?.toLocaleString()} kg</span>
              </div>
              <span className="text-[11px] text-emerald-700 font-semibold block">
                {freeCap.toLocaleString()} kg available
              </span>
            </div>

            {/* Capacity Utilization */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Payload Utilization</span>
              <div className="flex items-center gap-1.5 font-mono font-bold text-sm">
                <Gauge className="w-3.5 h-3.5 text-blue-600" />
                <span className={usedPct > 90 ? 'text-rose-700' : usedPct > 60 ? 'text-blue-700' : 'text-emerald-700'}>
                  {usedPct}%
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                {vehicle.current_load_kg?.toLocaleString()} kg loaded
              </span>
            </div>

            {/* Fuel & Powertrain */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Fuel / Energy</span>
              <div className="flex items-center gap-1.5 font-mono font-bold text-sm text-slate-900">
                <Fuel className="w-3.5 h-3.5 text-amber-600" />
                <span>{vehicle.fuel_level_pct}%</span>
              </div>
              <span className="text-[10px] text-slate-500 font-medium">
                {vehicle.fuel_type} • {vehicle.mileage_km?.toLocaleString()} km
              </span>
            </div>

            {/* Cargo Volume */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Cargo Volume</span>
              <div className="flex items-center gap-1.5 font-mono font-bold text-sm text-slate-900">
                <Box className="w-3.5 h-3.5 text-indigo-600" />
                <span>{vehicle.max_volume_m3 || 80} m³</span>
              </div>
              <span className="text-[11px] text-emerald-700 font-semibold block">
                {freeVol.toFixed(1)} m³ free space
              </span>
            </div>
          </div>

          {/* Capacity Meter Bar */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-1.5">
                <Scale className="w-3.5 h-3.5 text-blue-600" />
                <span>Payload Load Distribution</span>
              </span>
              <span className="font-mono text-slate-900 font-bold">
                {vehicle.current_load_kg.toLocaleString()} / {vehicle.max_capacity_kg.toLocaleString()} kg ({usedPct}%)
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full transition-all rounded-full ${
                  usedPct > 90 ? 'bg-rose-500' : usedPct > 60 ? 'bg-blue-600' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, usedPct)}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>Stationed Base: <strong className="text-slate-800">{vehicle.current_location}</strong></span>
              <span className="font-mono font-semibold text-emerald-700">
                {freeCap.toLocaleString()} kg Remaining Capacity
              </span>
            </div>
          </div>

          {/* Assigned Commercial Driver & Active Shipment Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Driver Profile */}
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-card space-y-2.5 text-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Assigned Commercial Driver</span>
                </span>
                {vehicle.driver_name && (
                  <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono text-[10px] font-bold border border-indigo-200">
                    {vehicle.driver_code || 'Certified'}
                  </span>
                )}
              </div>

              {vehicle.driver_name ? (
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Driver Name:</span>
                    <strong className="text-slate-900 font-bold">{vehicle.driver_name}</strong>
                  </div>
                  {vehicle.driver_phone && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Contact:</span>
                      <span className="font-mono text-slate-800 font-semibold">{vehicle.driver_phone}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Assignment Status:</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Active Operator
                    </span>
                  </div>
                </div>
              ) : (
                <div className="py-3 text-center text-slate-400 space-y-1">
                  <User className="w-6 h-6 mx-auto text-slate-300" />
                  <p className="font-semibold text-slate-600">No Driver Assigned</p>
                  <p className="text-[11px]">Vehicle is ready for driver allocation in dispatch queue.</p>
                </div>
              )}
            </div>

            {/* Active In-Transit Shipment */}
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-card space-y-2.5 text-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <Package className="w-3.5 h-3.5 text-blue-600" />
                  <span>Active In-Transit Shipment</span>
                </span>
                {vehicle.active_shipment_code && (
                  <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-mono text-[10px] font-bold border border-blue-200">
                    {vehicle.active_shipment_status || 'In Transit'}
                  </span>
                )}
              </div>

              {vehicle.active_shipment_code ? (
                <div className="space-y-2 pt-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Shipment Code:</span>
                    <strong className="text-blue-700 font-mono font-bold">{vehicle.active_shipment_code}</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Transit Corridor:</span>
                    <span className="text-slate-800 font-semibold truncate max-w-[200px]">
                      {vehicle.origin_hub || 'Origin'} ➔ {vehicle.destination_hub || 'Destination'}
                    </span>
                  </div>
                  {vehicle.active_shipment_weight_kg && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Payload Weight:</span>
                      <span className="font-mono text-slate-900 font-bold">
                        {vehicle.active_shipment_weight_kg.toLocaleString()} kg
                      </span>
                    </div>
                  )}
                  {onViewShipment && (
                    <button
                      type="button"
                      onClick={() => {
                        onViewShipment(vehicle.active_shipment_code!);
                        onClose();
                      }}
                      className="w-full mt-1 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors border border-blue-200 cursor-pointer shadow-2xs"
                    >
                      <span>Inspect Shipment Details</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ) : (
                <div className="py-3 text-center text-slate-400 space-y-1">
                  <Package className="w-6 h-6 mx-auto text-slate-300" />
                  <p className="font-semibold text-slate-600">No Active Shipment Assigned</p>
                  <p className="text-[11px]">Vehicle capacity is available for new cargo bookings.</p>
                </div>
              )}
            </div>
          </div>

          {/* Operational Status & Dispatch Controls Panel */}
          <form onSubmit={handleQuickSave} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Edit3 className="w-3.5 h-3.5 text-blue-600" />
                <span>Operational Status & Dispatch Control</span>
              </h4>
              {vehicle.status !== 'Deactivated' && (
                <button
                  type="button"
                  onClick={handleDeactivate}
                  disabled={updating}
                  className="text-[11px] font-bold text-rose-600 hover:text-rose-700 flex items-center gap-1 cursor-pointer"
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>Deactivate Vehicle</span>
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value as any)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 font-semibold outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer"
                >
                  {statuses.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Assigned Driver</label>
                <select
                  value={selectedDriverId}
                  onChange={(e) => setSelectedDriverId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer"
                >
                  <option value="">-- None (Unassigned) --</option>
                  {drivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.driver_code}) [{d.status}]
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Fuel Level (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={fuelLevel}
                  onChange={(e) => setFuelLevel(Number(e.target.value))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-mono font-bold text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">Current Checkpoint / Location Hub</label>
              <input
                type="text"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                placeholder="e.g. Central Distribution Hub, Chicago, IL"
                className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-2xs"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                type="submit"
                disabled={updating}
                className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-all cursor-pointer"
              >
                {updating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                <span>{updating ? 'Saving...' : 'Apply Dispatch Changes'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Edit Vehicle Modal */}
      {isEditModalOpen && (
        <EditVehicleModal
          vehicle={vehicle}
          onClose={() => setIsEditModalOpen(false)}
          onSuccess={(updated) => {
            setVehicle(updated);
            onUpdate(updated);
            setActionSuccessMsg(`Vehicle ${updated.vehicle_code} successfully updated!`);
            setTimeout(() => setActionSuccessMsg(null), 4000);
          }}
        />
      )}
    </div>
  );
};
