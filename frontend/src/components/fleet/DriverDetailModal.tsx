import React, { useState } from 'react';
import { Driver } from '../../types';
import { api } from '../../api/services';
import {
  X,
  Users,
  ShieldCheck,
  Clock,
  Star,
  Truck,
  Phone,
  Mail,
  Package,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Sparkles,
  Edit,
  Loader2,
  ExternalLink,
  Shield,
  Activity,
  Award
} from 'lucide-react';

interface DriverDetailModalProps {
  driver: Driver;
  onClose: () => void;
  onEdit: (driver: Driver) => void;
  onDriverUpdated: (updated: Driver) => void;
  onAskAI?: (prompt: string) => void;
  onViewVehicle?: (vehicleCode: string) => void;
  onViewShipment?: (shipmentCode: string) => void;
}

export const DriverDetailModal: React.FC<DriverDetailModalProps> = ({
  driver,
  onClose,
  onEdit,
  onDriverUpdated,
  onAskAI,
  onViewVehicle,
  onViewShipment,
}) => {
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const hos = driver.hours_of_service_remaining ?? 11.0;
  const hosPct = Math.min(100, Math.max(0, Math.round((hos / 11.0) * 100)));

  const handleStatusChange = async (newStatus: Driver['status']) => {
    try {
      setUpdatingStatus(true);
      setErrorMsg(null);
      const updated = await api.updateDriver(driver.driver_code, { status: newStatus });
      onDriverUpdated(updated);
    } catch (err: any) {
      console.error('Failed to update driver status:', err);
      setErrorMsg(err.message || 'Failed to update status.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'Available':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'On Duty':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/30';
      case 'Assigned':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'Rest':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'Off Duty':
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl shadow-modal overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-2xs">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-base font-bold text-slate-900 tracking-tight">{driver.name}</h3>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  {driver.driver_code}
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${getStatusBadge(driver.status)}`}>
                  {driver.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Commercial Driver Profile • FMCSA DOT Hours of Service Compliance Tracking
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 text-xs">
          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card flex flex-col justify-between">
              <span className="text-slate-500 text-[11px] font-semibold flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                <span>Commercial License</span>
              </span>
              <div className="mt-1">
                <span className="text-sm font-bold text-slate-900 block">{driver.license_type}</span>
                <span className="text-[10px] text-slate-500 font-mono">{driver.license_number}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card flex flex-col justify-between">
              <span className="text-slate-500 text-[11px] font-semibold flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                <span>Safety Rating</span>
              </span>
              <div className="mt-1">
                <span className="text-sm font-bold text-amber-600 font-mono block">
                  {driver.rating ? driver.rating.toFixed(1) : '4.8'} / 5.0
                </span>
                <span className="text-[10px] text-emerald-700 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Clean Safety Record
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-card flex flex-col justify-between">
              <span className="text-slate-500 text-[11px] font-semibold flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-indigo-600" />
                <span>Completed Loads</span>
              </span>
              <div className="mt-1">
                <span className="text-sm font-bold text-slate-900 font-mono block">
                  {driver.completed_deliveries_count ?? 0} deliveries
                </span>
                <span className="text-[10px] text-slate-500">
                  {driver.active_deliveries_count ?? 0} active in-flight
                </span>
              </div>
            </div>
          </div>

          {/* DOT Hours of Service (HOS) Section */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span className="font-semibold text-slate-900">FMCSA Hours of Service (HOS) Status</span>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                  hos > 2.0
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                {driver.hos_compliance_status || (hos > 2.0 ? 'DOT Legal' : 'Rest Break Required')}
              </span>
            </div>

            {/* HOS Meter */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Daily Driving Hours Remaining:</span>
                <strong className="text-slate-900 font-mono">{hos.toFixed(1)} / 11.0h ({hosPct}%)</strong>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden border border-slate-200">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    hos < 2.0 ? 'bg-rose-500' : hos < 5.0 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${hosPct}%` }}
                ></div>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-0.5">
                <span>Maximum 11.0 hours continuous driving limit</span>
                <span>Rest period: 10h consecutive required after shift</span>
              </div>
            </div>
          </div>

          {/* Contact Details & Assigned Truck */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Contact Card */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
              <span className="font-bold text-slate-900 block text-[11px] uppercase tracking-wider">
                Contact & Profile
              </span>
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2 text-slate-700">
                  <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="font-mono">{driver.phone}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-700">
                  <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="truncate">{driver.email}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-500 text-[11px] pt-1">
                  <Calendar className="w-3 h-3 text-slate-400 shrink-0" />
                  <span>Onboarded: {new Date(driver.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Assigned Vehicle Card */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 block text-[11px] uppercase tracking-wider">
                  Assigned Fleet Truck
                </span>
                {driver.assigned_vehicle_code && onViewVehicle && (
                  <button
                    onClick={() => onViewVehicle(driver.assigned_vehicle_code!)}
                    className="text-blue-600 hover:text-blue-800 text-[10px] font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    <span>View Truck</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                )}
              </div>

              {driver.assigned_vehicle_code ? (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <Truck className="w-4 h-4 text-blue-600 shrink-0" />
                    <span className="font-mono font-bold text-slate-900 text-xs">{driver.assigned_vehicle_code}</span>
                    <span className="text-[10px] text-slate-500 font-medium">({driver.assigned_vehicle_type || 'Commercial Fleet'})</span>
                  </div>
                  <p className="text-slate-700 text-xs truncate">
                    {driver.assigned_vehicle_model || 'Standard Haul Unit'}
                  </p>
                  {driver.assigned_vehicle_location && (
                    <p className="text-[11px] text-slate-500 truncate">
                      Location: {driver.assigned_vehicle_location}
                    </p>
                  )}
                </div>
              ) : (
                <div className="py-2 text-slate-400 text-xs flex items-center gap-2">
                  <Truck className="w-4 h-4 text-slate-400" />
                  <span>No truck assigned (Pool Operator)</span>
                </div>
              )}
            </div>
          </div>

          {/* Active Assigned Shipment Card */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4 text-blue-600" />
                <span className="font-semibold text-slate-900">Active Cargo Assignment</span>
              </div>
              {driver.active_shipment_code && onViewShipment && (
                <button
                  onClick={() => onViewShipment(driver.active_shipment_code!)}
                  className="px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 text-[10px] font-semibold flex items-center gap-1 transition-colors cursor-pointer shadow-2xs"
                >
                  <span>Track Shipment</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>

            {driver.active_shipment_code ? (
              <div className="p-3 rounded-lg bg-white border border-slate-200 flex items-center justify-between shadow-2xs">
                <div>
                  <div className="flex items-center gap-2">
                    <strong className="text-xs text-blue-700 font-mono font-bold">{driver.active_shipment_code}</strong>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      {driver.active_shipment_status || 'In Transit'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1.5">
                    <span>{driver.active_shipment_origin || 'Origin Hub'}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <span className="text-slate-800 font-semibold">{driver.active_shipment_destination || 'Destination Hub'}</span>
                  </div>
                </div>
                {driver.active_shipment_weight_kg && (
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block">Payload Weight</span>
                    <strong className="text-slate-900 font-mono font-bold">{driver.active_shipment_weight_kg.toLocaleString()} kg</strong>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-500 text-xs italic">
                Driver is currently not assigned to an active shipment. Ready for load dispatch.
              </p>
            )}
          </div>

          {/* Quick Dispatch Status Controls */}
          <div className="space-y-2 pt-1 border-t border-slate-200">
            <span className="text-[11px] text-slate-600 font-semibold block">Quick Operational Status Dispatch:</span>
            <div className="flex flex-wrap items-center gap-2">
              {(['Available', 'On Duty', 'Assigned', 'Rest', 'Off Duty'] as Driver['status'][]).map((st) => (
                <button
                  key={st}
                  disabled={updatingStatus || driver.status === st}
                  onClick={() => handleStatusChange(st)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                    driver.status === st
                      ? 'bg-blue-600 border-blue-600 text-white shadow-2xs'
                      : 'bg-white border-slate-300 text-slate-700 hover:text-slate-900 hover:bg-slate-50'
                  } disabled:opacity-50 flex items-center gap-1.5`}
                >
                  {updatingStatus && driver.status !== st ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : null}
                  <span>{st}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-50/80 border-t border-slate-200 flex items-center justify-between shrink-0">
          {onAskAI ? (
            <button
              onClick={() => {
                onAskAI(`What is the current status, HOS hours, and assignment of driver ${driver.driver_code} (${driver.name})?`);
                onClose();
              }}
              className="px-3.5 py-2 rounded-xl bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Ask AI about Driver</span>
            </button>
          ) : <div></div>}

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => {
                onEdit(driver);
                onClose();
              }}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
            >
              <Edit className="w-3.5 h-3.5" />
              <span>Edit Driver</span>
            </button>

            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 hover:text-slate-900 text-xs font-semibold transition-colors cursor-pointer shadow-2xs"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
