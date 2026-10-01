import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../../api/services';
import { Driver, DriverStats } from '../../types';
import { CreateDriverModal } from './CreateDriverModal';
import { EditDriverModal } from './EditDriverModal';
import { DriverDetailModal } from './DriverDetailModal';
import {
  Users,
  Clock,
  Star,
  ShieldCheck,
  Truck,
  Phone,
  Mail,
  RefreshCw,
  AlertCircle,
  Plus,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  Eye,
  Edit,
  Trash2,
  Package,
  Sparkles,
  ArrowUpDown,
  SlidersHorizontal,
  Check,
  Award
} from 'lucide-react';

interface DriverRosterProps {
  onAskAI?: (prompt: string) => void;
  onViewVehicle?: (vehicleCode: string) => void;
  onViewShipment?: (shipmentCode: string) => void;
}

export const DriverRoster: React.FC<DriverRosterProps> = ({
  onAskAI,
  onViewVehicle,
  onViewShipment,
}) => {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [stats, setStats] = useState<DriverStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [licenseFilter, setLicenseFilter] = useState('All');
  const [availableOnly, setAvailableOnly] = useState(false);

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null);
  const [editingDriver, setEditingDriver] = useState<Driver | null>(null);
  const [deactivatingDriver, setDeactivatingDriver] = useState<Driver | null>(null);
  const [deactivating, setDeactivating] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastError, setToastError] = useState<string | null>(null);

  const statuses = ['All', 'Available', 'Assigned', 'On Duty', 'Rest', 'Off Duty'];
  const licenseClasses = ['All', 'CDL-A', 'CDL-B', 'Standard'];

  const loadData = async () => {
    try {
      setLoading(true);
      const [driverList, statsData] = await Promise.all([
        api.getDrivers({
          status: statusFilter === 'All' ? undefined : statusFilter,
          license_type: licenseFilter === 'All' ? undefined : licenseFilter,
          search: searchQuery.trim() || undefined,
        }),
        api.getDriverStats().catch((err) => {
          console.error('Failed to load stats:', err);
          return null;
        }),
      ]);

      setDrivers(driverList || []);
      if (statsData) setStats(statsData);
    } catch (err) {
      console.error('Error loading drivers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, licenseFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleCreateSuccess = (newDriver: Driver) => {
    setDrivers((prev) => [newDriver, ...prev]);
    setToastMessage(`Commercial driver ${newDriver.name} (${newDriver.driver_code}) successfully onboarded!`);
    loadData();
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleUpdateSuccess = (updatedDriver: Driver) => {
    setDrivers((prev) => prev.map((d) => (d.id === updatedDriver.id ? updatedDriver : d)));
    if (selectedDriver?.id === updatedDriver.id) {
      setSelectedDriver(updatedDriver);
    }
    setToastMessage(`Driver ${updatedDriver.name} (${updatedDriver.driver_code}) updated successfully.`);
    loadData();
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleDeactivateConfirm = async () => {
    if (!deactivatingDriver) return;
    try {
      setDeactivating(true);
      setToastError(null);
      await api.deactivateDriver(deactivatingDriver.driver_code);
      setToastMessage(`Driver ${deactivatingDriver.driver_code} (${deactivatingDriver.name}) has been deactivated.`);
      setDeactivatingDriver(null);
      if (selectedDriver?.id === deactivatingDriver.id) {
        setSelectedDriver(null);
      }
      loadData();
      setTimeout(() => setToastMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to deactivate driver:', err);
      setToastError(err.message || 'Failed to deactivate driver.');
    } finally {
      setDeactivating(false);
    }
  };

  // Client-side quick filter for Available Only toggle or text search
  const filteredDrivers = useMemo(() => {
    return drivers.filter((d) => {
      if (availableOnly && d.status !== 'Available') return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches =
          d.name.toLowerCase().includes(q) ||
          d.driver_code.toLowerCase().includes(q) ||
          d.license_number.toLowerCase().includes(q) ||
          d.phone.toLowerCase().includes(q) ||
          (d.assigned_vehicle_code && d.assigned_vehicle_code.toLowerCase().includes(q));
        if (!matches) return false;
      }
      return true;
    });
  }, [drivers, availableOnly, searchQuery]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Available':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'On Duty':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Assigned':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'Rest':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Off Duty':
        return 'bg-slate-100 text-slate-600 border-slate-200';
      case 'Deactivated':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Toast Success Notification */}
      {toastMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-card animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-600 hover:text-emerald-900 cursor-pointer">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Toast Error Notification */}
      {toastError && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex items-center justify-between shadow-card animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{toastError}</span>
          </div>
          <button onClick={() => setToastError(null)} className="text-rose-600 hover:text-rose-900 cursor-pointer">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Header */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-600">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>Commercial Driver Operations & HOS Center</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Real-time commercial driver roster, FMCSA Hours of Service compliance, safety performance, and truck assignments.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {onAskAI && (
            <button
              onClick={() => onAskAI('Which drivers are currently available for load dispatch and have over 6 hours of HOS?')}
              className="px-3 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Ask AI Roster</span>
            </button>
          )}

          <button
            onClick={loadData}
            className="px-3 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 hover:text-slate-900 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Driver</span>
          </button>
        </div>
      </div>

      {/* Dynamic Telemetry KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-500 text-xs font-semibold">Total Drivers</span>
            <div className="text-2xl font-bold text-slate-900 font-mono">
              {stats ? stats.total_drivers : drivers.length}
            </div>
            <span className="text-[11px] text-slate-400">Commercial operators</span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
            <Users className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-500 text-xs font-semibold">Ready / Available</span>
            <div className="text-2xl font-bold text-emerald-700 font-mono">
              {stats ? stats.available_drivers : drivers.filter((d) => d.status === 'Available').length}
            </div>
            <span className="text-[11px] text-emerald-600">Available for dispatch</span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-500 text-xs font-semibold">Assigned & On Duty</span>
            <div className="text-2xl font-bold text-blue-700 font-mono">
              {stats ? stats.assigned_drivers + stats.on_duty_drivers : drivers.filter((d) => ['Assigned', 'On Duty'].includes(d.status)).length}
            </div>
            <span className="text-[11px] text-blue-600">
              {stats ? stats.drivers_with_active_shipments : 0} with active loads
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
            <Truck className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-500 text-xs font-semibold">Average HOS Left</span>
            <div className="text-2xl font-bold text-indigo-700 font-mono">
              {stats ? stats.average_hos_remaining.toFixed(1) : '10.5'}h
            </div>
            <span className="text-[11px] text-indigo-600">FMCSA 11.0h limit</span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
            <Clock className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-card space-y-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search driver name, code (DRV-...), license, truck..."
              className="w-full pl-9 pr-8 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}
          </form>

          {/* Available Only Toggle */}
          <div className="flex items-center gap-2 self-end md:self-auto">
            <button
              onClick={() => setAvailableOnly(!availableOnly)}
              className={`px-3 py-2 rounded-xl text-xs font-semibold border flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs ${
                availableOnly
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                  : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center ${
                availableOnly ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-slate-400'
              }`}>
                {availableOnly && <Check className="w-2.5 h-2.5" />}
              </div>
              <span>Available Only</span>
            </button>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1 mr-2 text-slate-500 font-semibold text-[11px] uppercase">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span>Status:</span>
          </div>
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

          <div className="flex items-center gap-1 mx-2 text-slate-500 font-semibold text-[11px] uppercase border-l border-slate-200 pl-3">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
            <span>License:</span>
          </div>
          {licenseClasses.map((lc) => (
            <button
              key={lc}
              onClick={() => setLicenseFilter(lc)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                licenseFilter === lc
                  ? 'bg-indigo-600 text-white shadow-2xs'
                  : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
              }`}
            >
              {lc}
            </button>
          ))}
        </div>
      </div>

      {/* Driver Cards Grid */}
      {loading ? (
        <div className="p-16 text-center text-slate-500 font-mono text-xs flex items-center justify-center gap-2 bg-white rounded-2xl border border-slate-200 shadow-card">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Loading dynamic driver roster from Supabase...</span>
        </div>
      ) : filteredDrivers.length === 0 ? (
        <div className="p-16 text-center text-slate-500 text-xs bg-white rounded-2xl border border-slate-200 shadow-card space-y-2">
          <Users className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="font-semibold text-slate-800 text-sm">No commercial drivers match the selected filters.</p>
          <p className="text-[11px] text-slate-500">Try adjusting search parameters or onboarding a new driver.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDrivers.map((d) => {
            const hos = d.hours_of_service_remaining ?? 11.0;
            const hosPct = Math.min(100, Math.max(0, Math.round((hos / 11.0) * 100)));

            return (
              <div
                key={d.id}
                className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 transition-all shadow-card hover:shadow-md space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-3.5">
                  {/* Driver Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-sm font-bold text-white shadow-2xs shrink-0">
                        {d.name.split(' ').map((n) => n[0]).join('')}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <strong className="text-sm text-slate-900 hover:text-blue-600 cursor-pointer font-bold" onClick={() => setSelectedDriver(d)}>
                            {d.name}
                          </strong>
                          <span className="text-[10px] text-slate-400 font-mono">({d.driver_code})</span>
                        </div>
                        <span className="text-xs text-blue-600 font-semibold">{d.license_type} License</span>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(d.status)}`}>
                      {d.status}
                    </span>
                  </div>

                  {/* FMCSA HOS Meter */}
                  <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-blue-600" />
                        <span>Hours of Service (HOS):</span>
                      </span>
                      <strong className="text-slate-900 font-mono">{hos.toFixed(1)} / 11.0h</strong>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden border border-slate-200">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          hos < 2.0 ? 'bg-rose-500' : hos < 5.0 ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${hosPct}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-500">Compliance:</span>
                      <span className={`font-semibold ${hos > 2.0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                        {hos > 2.0 ? 'DOT Legal' : 'Rest Break Required'}
                      </span>
                    </div>
                  </div>

                  {/* Rating & Assigned Vehicle / Active Shipment */}
                  <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-slate-100 text-slate-600">
                    <div className="flex items-center gap-1.5">
                      <Star className="w-3.5 h-3.5 text-amber-500 shrink-0 fill-amber-500" />
                      <span>Rating: <strong className="text-slate-900 font-mono">{d.rating ? d.rating.toFixed(1) : '4.8'}</strong></span>
                    </div>
                    <div className="flex items-center gap-1.5 truncate">
                      <Truck className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                      <span className="truncate">
                        Truck: <strong className="text-slate-900 font-mono">{d.assigned_vehicle_code || 'None'}</strong>
                      </span>
                    </div>
                  </div>

                  {/* Active Cargo Banner (if any) */}
                  {d.active_shipment_code && (
                    <div className="p-2 rounded-lg bg-blue-50 border border-blue-200 text-[11px] text-blue-900 flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <Package className="w-3 h-3 text-blue-600 shrink-0" />
                        <span>Cargo: <strong className="font-mono">{d.active_shipment_code}</strong></span>
                      </div>
                      {onViewShipment && (
                        <button
                          onClick={() => onViewShipment(d.active_shipment_code!)}
                          className="text-[10px] text-blue-700 hover:text-blue-900 underline font-semibold cursor-pointer"
                        >
                          Track
                        </button>
                      )}
                    </div>
                  )}

                  {/* Contact Info */}
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span className="flex items-center gap-1">
                      <Phone className="w-3 h-3 text-slate-400" />
                      <span>{d.phone}</span>
                    </span>
                    <span className="font-mono text-slate-400">{d.license_number}</span>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-1.5">
                  <button
                    onClick={() => setSelectedDriver(d)}
                    className="flex-1 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 text-xs font-semibold transition-colors flex items-center justify-center gap-1 cursor-pointer"
                  >
                    <Eye className="w-3 h-3 text-blue-600" />
                    <span>Inspect</span>
                  </button>

                  <button
                    onClick={() => setEditingDriver(d)}
                    className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors cursor-pointer border border-slate-200"
                    title="Edit Driver"
                  >
                    <Edit className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => setDeactivatingDriver(d)}
                    disabled={d.status === 'Deactivated'}
                    className="p-1.5 rounded-lg bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 transition-colors disabled:opacity-30 cursor-pointer border border-slate-200"
                    title="Deactivate Driver"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Driver Modal */}
      {isCreateModalOpen && (
        <CreateDriverModal
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleCreateSuccess}
          existingCodes={drivers.map((d) => d.driver_code)}
        />
      )}

      {/* Edit Driver Modal */}
      {editingDriver && (
        <EditDriverModal
          driver={editingDriver}
          onClose={() => setEditingDriver(null)}
          onSuccess={handleUpdateSuccess}
        />
      )}

      {/* Driver Detail Modal */}
      {selectedDriver && (
        <DriverDetailModal
          driver={selectedDriver}
          onClose={() => setSelectedDriver(null)}
          onEdit={(d) => setEditingDriver(d)}
          onDriverUpdated={handleUpdateSuccess}
          onAskAI={onAskAI}
          onViewVehicle={onViewVehicle}
          onViewShipment={onViewShipment}
        />
      )}

      {/* Deactivate Confirmation Modal */}
      {deactivatingDriver && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 max-w-md w-full shadow-modal space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3 text-rose-600">
              <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900">Deactivate Commercial Driver?</h4>
                <p className="text-xs text-slate-500">
                  {deactivatingDriver.name} ({deactivatingDriver.driver_code})
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Deactivating this driver will unassign any linked fleet vehicle and mark their status as <strong className="text-rose-600">Deactivated</strong>. Historical delivery logs and audit records will remain safely preserved.
            </p>

            <div className="pt-2 flex items-center justify-end gap-2.5">
              <button
                type="button"
                disabled={deactivating}
                onClick={() => setDeactivatingDriver(null)}
                className="px-4 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold transition-colors cursor-pointer shadow-2xs"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deactivating}
                onClick={handleDeactivateConfirm}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-2xs cursor-pointer"
              >
                {deactivating ? 'Deactivating...' : 'Confirm Deactivation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
