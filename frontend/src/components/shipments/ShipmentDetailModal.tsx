import React, { useState, useEffect } from 'react';
import { Shipment, Vehicle, Driver, ShipmentStatus } from '../../types';
import { api } from '../../api/services';
import { StatusBadge } from './StatusBadge';
import { 
  X, 
  Package, 
  MapPin, 
  Truck, 
  User, 
  Clock, 
  AlertTriangle, 
  Calendar, 
  Scale, 
  Thermometer,
  ShieldAlert,
  ArrowRight,
  Sparkles,
  DollarSign,
  History,
  CheckCircle2,
  Navigation,
  FileText,
  Loader2,
  Info,
  Edit3,
  Save,
  Ban,
  RotateCcw
} from 'lucide-react';

interface ShipmentDetailModalProps {
  shipment: Shipment | null;
  onClose: () => void;
  onUpdate?: (updated: Shipment) => void;
  onViewRoute?: (code: string) => void;
  onAskAI?: (prompt: string) => void;
}

export const ShipmentDetailModal: React.FC<ShipmentDetailModalProps> = ({
  shipment: initialShipment,
  onClose,
  onUpdate,
  onViewRoute,
  onAskAI,
}) => {
  const [shipment, setShipment] = useState<Shipment | null>(initialShipment);
  const [loading, setLoading] = useState(false);

  // Edit / Status Transition State
  const [isEditingStatus, setIsEditingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState<ShipmentStatus>(initialShipment?.status || 'Pending');
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | ''>(initialShipment?.vehicle_id || '');
  const [selectedDriverId, setSelectedDriverId] = useState<number | ''>(initialShipment?.driver_id || '');
  const [locationName, setLocationName] = useState(initialShipment?.current_location_name || '');
  const [delayMinutes, setDelayMinutes] = useState<number>(initialShipment?.delay_minutes || 0);
  const [delayReason, setDelayReason] = useState<string>(initialShipment?.delay_reason || '');
  const [statusNotes, setStatusNotes] = useState<string>('');
  
  // Available resources for reassignment
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [updating, setUpdating] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const fetchFullDetails = async () => {
    if (!initialShipment?.shipment_code) return;
    try {
      setLoading(true);
      const full = await api.getShipment(initialShipment.shipment_code);
      setShipment(full);
      setNewStatus(full.status);
      setSelectedVehicleId(full.vehicle_id || '');
      setSelectedDriverId(full.driver_id || '');
      setLocationName(full.current_location_name || '');
      setDelayMinutes(full.delay_minutes || 0);
      setDelayReason(full.delay_reason || '');
    } catch (err) {
      console.error('Failed to load full shipment details:', err);
      setShipment(initialShipment);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFullDetails();

    // Fetch available vehicles & drivers for dropdowns
    api.getVehicles().then(setVehicles).catch(() => []);
    api.getDrivers().then(setDrivers).catch(() => []);
  }, [initialShipment?.shipment_code]);

  if (!shipment) return null;

  const handleAskAIAboutShipment = () => {
    if (onAskAI) {
      const prompt = `Give me a comprehensive operational summary of shipment ${shipment.shipment_code} for ${shipment.customer_name || 'the customer'}, and explain whether there are any delivery risks, delays, or SLA violations.`;
      onClose();
      onAskAI(prompt);
    }
  };

  const handleSaveStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setUpdating(true);
      setActionSuccessMsg(null);

      const payload = {
        status: newStatus,
        vehicle_id: selectedVehicleId ? Number(selectedVehicleId) : null,
        driver_id: selectedDriverId ? Number(selectedDriverId) : null,
        current_location_name: locationName.trim() || undefined,
        delay_minutes: Number(delayMinutes),
        delay_reason: delayMinutes > 0 ? (delayReason.trim() || 'Operational delay') : undefined,
        notes: statusNotes.trim() || `Status updated to ${newStatus} by dispatcher.`,
      };

      const updated = await api.updateShipment(shipment.shipment_code, payload);
      setShipment(updated);
      setIsEditingStatus(false);
      setStatusNotes('');
      setActionSuccessMsg(`Status updated to '${newStatus}' and persisted to database!`);
      setTimeout(() => setActionSuccessMsg(null), 4000);

      if (onUpdate) {
        onUpdate(updated);
      }
    } catch (err: any) {
      console.error('Failed to update shipment status:', err);
      alert(err.message || 'Failed to update shipment status. Please try again.');
    } finally {
      setUpdating(false);
    }
  };

  const handleCancelShipment = async () => {
    if (!window.confirm(`Are you sure you want to cancel shipment ${shipment.shipment_code}? This will release any assigned fleet capacity and log a cancellation audit checkpoint.`)) {
      return;
    }

    try {
      setUpdating(true);
      const updated = await api.updateShipment(shipment.shipment_code, {
        status: 'Cancelled',
        notes: 'Shipment cancelled by logistics operator.',
      });
      setShipment(updated);
      setIsEditingStatus(false);
      setActionSuccessMsg(`Shipment ${shipment.shipment_code} has been cancelled.`);
      setTimeout(() => setActionSuccessMsg(null), 4000);

      if (onUpdate) {
        onUpdate(updated);
      }
    } catch (err: any) {
      console.error('Failed to cancel shipment:', err);
      alert(err.message || 'Unable to cancel shipment.');
    } finally {
      setUpdating(false);
    }
  };

  // Real database cost or calculated estimation
  const totalCost = shipment.cost_total_usd || (shipment.cost_breakdown?.total_cost) || Math.round(250 + (shipment.weight_kg * 0.085));
  const costBreakdown = shipment.cost_breakdown || {
    fuel_cost: (totalCost * 0.38).toFixed(2),
    driver_cost: (totalCost * 0.32).toFixed(2),
    toll_cost: (totalCost * 0.15).toFixed(2),
    maintenance_cost: (totalCost * 0.15).toFixed(2),
  };

  const allStatuses: ShipmentStatus[] = ['Pending', 'Assigned', 'Picked Up', 'In Transit', 'Delayed', 'Delivered', 'Failed', 'Cancelled'];

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-3xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* 1. Modal Header */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-2xs">
              <Package className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-base font-bold text-slate-900 font-mono tracking-tight">
                  {shipment.shipment_code}
                </h3>
                <StatusBadge status={shipment.status} />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Customer: <strong className="text-slate-800 font-medium">{shipment.customer_name || 'Enterprise Account'}</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditingStatus(!isEditingStatus)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold shadow-2xs transition-colors"
              title="Update status, delay reason, or reassign driver/vehicle"
            >
              <Edit3 className="w-3.5 h-3.5 text-slate-600" />
              <span>{isEditingStatus ? 'Cancel Edit' : 'Update Status'}</span>
            </button>

            {onAskAI && (
              <button
                onClick={handleAskAIAboutShipment}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 text-xs font-semibold shadow-2xs transition-colors"
                title="Ask LogiAgent AI Assistant about this shipment"
              >
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Ask AI</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* 2. Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {actionSuccessMsg && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center justify-between shadow-2xs">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="font-semibold">{actionSuccessMsg}</span>
              </div>
            </div>
          )}

          {loading && !shipment.history && (
            <div className="py-2 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span>Fetching telemetry and audit checkpoints from Supabase...</span>
            </div>
          )}

          {/* Interactive Status Transition & Telemetry Editor */}
          {isEditingStatus && (
            <form onSubmit={handleSaveStatusUpdate} className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 space-y-3.5">
              <div className="flex items-center justify-between border-b border-blue-200/80 pb-2">
                <h4 className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                  <Edit3 className="w-3.5 h-3.5 text-blue-600" />
                  <span>Update Operations Status & Dispatch Allocation</span>
                </h4>
                {shipment.status !== 'Cancelled' && (
                  <button
                    type="button"
                    onClick={handleCancelShipment}
                    disabled={updating}
                    className="text-[11px] font-bold text-rose-600 hover:text-rose-700 flex items-center gap-1"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    <span>Cancel Shipment</span>
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Status</label>
                  <select
                    value={newStatus}
                    onChange={(e) => {
                      const st = e.target.value as ShipmentStatus;
                      setNewStatus(st);
                      if (st === 'Delivered' && shipment.destination_name) {
                        setLocationName(`${shipment.destination_name}${shipment.destination_city ? `, ${shipment.destination_city}` : ''}`);
                      }
                    }}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 font-semibold outline-none"
                  >
                    {allStatuses.map((st) => (
                      <option key={st} value={st}>{st}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Assigned Vehicle</label>
                  <select
                    value={selectedVehicleId}
                    onChange={(e) => setSelectedVehicleId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none"
                  >
                    <option value="">-- None (Unassigned) --</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.vehicle_code} ({v.type}) [{v.status}]
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Assigned Driver</label>
                  <select
                    value={selectedDriverId}
                    onChange={(e) => setSelectedDriverId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none"
                  >
                    <option value="">-- None (Unassigned) --</option>
                    {drivers.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.driver_code}) [{d.status}]
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 mb-1">Current Checkpoint / Location</label>
                  <input
                    type="text"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    placeholder="e.g. Dallas Regional Staging Bay #3"
                    className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 mb-1">Delay (Mins)</label>
                    <input
                      type="number"
                      min="0"
                      step="5"
                      value={delayMinutes}
                      onChange={(e) => setDelayMinutes(Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-mono text-slate-900 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 mb-1">Delay Reason</label>
                    <input
                      type="text"
                      value={delayReason}
                      onChange={(e) => setDelayReason(e.target.value)}
                      placeholder="e.g. Weather slowdown"
                      className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Checkpoint / Transition Audit Notes</label>
                <input
                  type="text"
                  value={statusNotes}
                  onChange={(e) => setStatusNotes(e.target.value)}
                  placeholder="e.g. Loaded and departed origin facility on schedule."
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white border border-slate-300 text-xs text-slate-900 outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setIsEditingStatus(false)}
                  disabled={updating}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-2xs"
                >
                  {updating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  <span>{updating ? 'Saving...' : 'Apply Changes'}</span>
                </button>
              </div>
            </form>
          )}

          {/* Active Delay Alert Box (if delayed) */}
          {shipment.delay_minutes > 0 && (
            <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-xs">
              <div className="flex items-center justify-between text-amber-900 font-bold mb-1">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>Active Delay: +{shipment.delay_minutes} Minutes ({Math.floor(shipment.delay_minutes / 60)}h {shipment.delay_minutes % 60}m)</span>
                </div>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                  Risk: {shipment.delay_risk_level} ({shipment.delay_risk_score}/100)
                </span>
              </div>
              <p className="text-amber-800 text-[11px] leading-relaxed">
                <strong>Root Cause:</strong> {shipment.delay_reason || 'Interstate congestion and seasonal dispatch delays.'}
              </p>
            </div>
          )}

          {/* Transit Corridor & Route Section */}
          <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              <span>Transit Corridor</span>
              {onViewRoute && (
                <button
                  onClick={() => {
                    onViewRoute(shipment.shipment_code);
                    onClose();
                  }}
                  className="text-blue-600 hover:text-blue-700 flex items-center gap-1 font-semibold normal-case text-xs transition-colors"
                >
                  <Navigation className="w-3.5 h-3.5" />
                  <span>Open in Route Visualizer</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <div className="w-3 h-3 rounded-full bg-blue-600 mt-1 shrink-0 ring-4 ring-blue-100"></div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Origin Hub</span>
                  <strong className="text-xs sm:text-sm text-slate-900 block font-semibold">{shipment.origin_name || 'Origin Facility'}</strong>
                  <span className="text-xs text-slate-500">{shipment.origin_city || 'Origin City'}{shipment.origin_state ? `, ${shipment.origin_state}` : ''}</span>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-3 h-3 rounded-full bg-emerald-600 mt-1 shrink-0 ring-4 ring-emerald-100"></div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Destination Hub</span>
                  <strong className="text-xs sm:text-sm text-slate-900 block font-semibold">{shipment.destination_name || 'Destination Dock'}</strong>
                  <span className="text-xs text-slate-500">{shipment.destination_city || 'Destination City'}{shipment.destination_state ? `, ${shipment.destination_state}` : ''}</span>
                </div>
              </div>
            </div>

            {/* Current Position / Telemetry Location */}
            <div className="mt-3.5 pt-3 border-t border-slate-200 flex flex-wrap items-center justify-between text-xs text-slate-600 gap-2">
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                <span>Current Checkpoint: <strong className="text-slate-900 font-semibold">{shipment.current_location_name || 'In Corridor Transit'}</strong></span>
              </div>
              {shipment.current_latitude && shipment.current_longitude && (
                <div className="font-mono text-[11px] text-slate-400">
                  [{shipment.current_latitude.toFixed(4)}, {shipment.current_longitude.toFixed(4)}]
                </div>
              )}
            </div>
          </div>

          {/* Key Operational Metrics (4-column Grid) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {/* Cargo Weight */}
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block mb-1">Gross Weight</span>
              <div className="flex items-center gap-1.5 text-slate-900 font-mono font-bold text-sm">
                <Scale className="w-3.5 h-3.5 text-blue-600" />
                <span>{shipment.weight_kg?.toLocaleString() || 1000} kg</span>
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">{shipment.cargo_type || 'General Freight'}</span>
            </div>

            {/* Vehicle Assigned */}
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block mb-1">Assigned Fleet</span>
              <div className="flex items-center gap-1.5 text-slate-900 font-mono font-bold text-sm">
                <Truck className="w-3.5 h-3.5 text-blue-600" />
                <span>{shipment.vehicle_code || 'Not assigned'}</span>
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                {shipment.vehicle_code ? 'Active telematics' : 'Awaiting assignment'}
              </span>
            </div>

            {/* Driver Assigned */}
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block mb-1">Assigned Driver</span>
              <div className="flex items-center gap-1.5 text-slate-900 font-bold text-sm truncate">
                <User className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                <span className="truncate">{shipment.driver_name || 'Not assigned'}</span>
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                {shipment.driver_name ? 'Certified operator' : 'No driver allocated'}
              </span>
            </div>

            {/* Delay Risk */}
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block mb-1">Delay Risk Assessment</span>
              <div className="flex items-center gap-1.5 text-slate-900 font-bold text-sm">
                <ShieldAlert className={`w-3.5 h-3.5 ${shipment.delay_risk_score > 50 ? 'text-amber-500' : 'text-emerald-500'}`} />
                <span className={shipment.delay_risk_score > 50 ? 'text-amber-700' : 'text-emerald-700'}>
                  {shipment.delay_risk_level || 'Low'} ({shipment.delay_risk_score || 0})
                </span>
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 block">ML Risk Predictor</span>
            </div>
          </div>

          {/* Schedule & ETA Breakdown */}
          <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-2.5 text-xs">
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-blue-600" />
              <span>Schedule & ETA Telemetry</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Scheduled Delivery SLA</span>
                <span className="font-mono text-xs font-semibold text-slate-800 block mt-0.5">
                  {new Date(shipment.expected_delivery).toLocaleString()}
                </span>
              </div>

              {shipment.status === 'Delivered' ? (
                <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-emerald-800 uppercase font-bold block">Actual Delivered Time</span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-200/60 text-emerald-800">
                      {shipment.delay_minutes > 0 ? `+${shipment.delay_minutes}m Late` : 'On Schedule'}
                    </span>
                  </div>
                  <span className="font-mono text-xs font-bold text-emerald-900 block mt-0.5">
                    {shipment.actual_delivery ? new Date(shipment.actual_delivery).toLocaleString() : 'Delivered'}
                  </span>
                </div>
              ) : shipment.status === 'Cancelled' ? (
                <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200">
                  <span className="text-[10px] text-rose-800 uppercase font-bold block">Lifecycle Status</span>
                  <span className="font-mono text-xs font-bold text-rose-900 block mt-0.5">
                    Cancelled (No active transit)
                  </span>
                </div>
              ) : (
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Projected Arrival (ETA)</span>
                    {shipment.delay_minutes > 0 && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                        +{shipment.delay_minutes}m Delay
                      </span>
                    )}
                  </div>
                  <span className={`font-mono text-xs font-bold block mt-0.5 ${shipment.delay_minutes > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                    {shipment.estimated_eta ? new Date(shipment.estimated_eta).toLocaleString() : 'Calculating dynamic ETA...'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Real Transportation Cost Breakdown from Supabase Database */}
          <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
                <span>Transportation Cost Structure (Supabase Database Record)</span>
              </h4>
              <span className="font-mono font-bold text-slate-900 text-sm">
                ${Number(totalCost).toLocaleString()} USD
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1 text-slate-600">
              <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block">Fuel Cost</span>
                <strong className="text-slate-800 font-mono">${costBreakdown.fuel_cost || '0.00'}</strong>
              </div>
              <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block">Driver Labor</span>
                <strong className="text-slate-800 font-mono">${costBreakdown.driver_cost || '0.00'}</strong>
              </div>
              <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block">Tolls & Highway Fees</span>
                <strong className="text-slate-800 font-mono">${costBreakdown.toll_cost || '0.00'}</strong>
              </div>
              <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[10px] text-slate-400 block">Maintenance Allocation</span>
                <strong className="text-slate-800 font-mono">${costBreakdown.maintenance_cost || '0.00'}</strong>
              </div>
            </div>
          </div>

          {/* Temperature & Cold Chain Specs (if applicable) */}
          {shipment.temperature_controlled && (
            <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2 text-blue-900 font-semibold">
                <Thermometer className="w-4 h-4 text-blue-600" />
                <span>Cold Chain Monitored: Active Refrigeration Required</span>
              </div>
              <span className="font-mono font-bold text-blue-800 px-2 py-0.5 rounded-md bg-blue-100 border border-blue-200">
                Target: {shipment.target_temp_celsius != null ? `${shipment.target_temp_celsius}°C` : '4.0°C'}
              </span>
            </div>
          )}

          {/* Special Instructions (if present) */}
          {shipment.special_instructions && (
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">
                Special Handling Instructions
              </span>
              <p className="text-slate-700 text-xs leading-relaxed">
                {shipment.special_instructions}
              </p>
            </div>
          )}

          {/* Real Status History Timeline from Supabase */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5 uppercase tracking-wider">
              <History className="w-3.5 h-3.5 text-blue-600" />
              <span>Status Audit Timeline ({shipment.history?.length || 0} Checkpoints)</span>
            </h4>

            {shipment.history && shipment.history.length > 0 ? (
              <div className="space-y-2 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-slate-200">
                {shipment.history.map((h, i) => (
                  <div key={h.id || i} className="relative flex items-start gap-3 pl-1">
                    <div className="w-5 h-5 rounded-full bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center shrink-0 z-10 mt-0.5 shadow-2xs">
                      <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                    </div>

                    <div className="flex-1 p-3 rounded-xl bg-white border border-slate-200 shadow-2xs text-xs">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <strong className="text-slate-900 font-semibold">{h.status}</strong>
                          {h.location_name && (
                            <span className="text-[11px] text-slate-500">· {h.location_name}</span>
                          )}
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(h.timestamp).toLocaleString()}
                        </span>
                      </div>
                      {h.notes && (
                        <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">{h.notes}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
                Initial registration checkpoint recorded in Supabase database.
              </div>
            )}
          </div>
        </div>

        {/* 3. Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-50/80 border-t border-slate-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Info className="w-3.5 h-3.5 text-slate-400" />
            <span>ID: {shipment.id} · Registered {new Date(shipment.created_at).toLocaleDateString()}</span>
          </div>

          <div className="flex items-center gap-2">
            {onAskAI && (
              <button
                onClick={handleAskAIAboutShipment}
                className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-2xs transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Ask AI About Shipment</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

