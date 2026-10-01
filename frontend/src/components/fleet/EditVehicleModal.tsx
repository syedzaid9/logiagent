import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { Driver, Vehicle } from '../../types';
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
  Save
} from 'lucide-react';

interface EditVehicleModalProps {
  vehicle: Vehicle;
  onClose: () => void;
  onSuccess: (updatedVehicle: Vehicle) => void;
}

export const EditVehicleModal: React.FC<EditVehicleModalProps> = ({
  vehicle,
  onClose,
  onSuccess,
}) => {
  const [model, setModel] = useState(vehicle.model);
  const [type, setType] = useState(vehicle.type);
  const [status, setStatus] = useState(vehicle.status);
  const [maxCapacityKg, setMaxCapacityKg] = useState<number>(vehicle.max_capacity_kg);
  const [currentLoadKg, setCurrentLoadKg] = useState<number>(vehicle.current_load_kg);
  const [maxVolumeM3, setMaxVolumeM3] = useState<number>(vehicle.max_volume_m3 || 80.0);
  const [fuelType, setFuelType] = useState(vehicle.fuel_type || 'Diesel');
  const [fuelLevelPct, setFuelLevelPct] = useState<number>(vehicle.fuel_level_pct);
  const [currentLocation, setCurrentLocation] = useState(vehicle.current_location);
  const [latitude, setLatitude] = useState<number>(vehicle.latitude);
  const [longitude, setLongitude] = useState<number>(vehicle.longitude);
  const [mileageKm, setMileageKm] = useState<number>(vehicle.mileage_km);
  const [driverId, setDriverId] = useState<number | ''>(vehicle.driver_id || '');

  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loadingDrivers, setLoadingDrivers] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const vehicleTypes = [
    'Semi-Truck (Dry Van)',
    'Reefer (Refrigerated)',
    'Flatbed',
    'Box Truck',
    'Sprinter Van',
  ];

  const statuses = ['Available', 'Assigned', 'In Transit', 'Maintenance', 'Deactivated'];

  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        setLoadingDrivers(true);
        const data = await api.getDrivers();
        setDrivers(data || []);
      } catch (err) {
        console.error('Failed to load drivers for editing:', err);
      } finally {
        setLoadingDrivers(false);
      }
    };
    fetchDrivers();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!model.trim()) {
      setErrorMsg('Model name is required.');
      return;
    }
    if (maxCapacityKg <= 0) {
      setErrorMsg('Max capacity must be greater than 0 kg.');
      return;
    }

    try {
      setSubmitting(true);
      const payload: Partial<Vehicle> = {
        model: model.trim(),
        type,
        status: status as any,
        max_capacity_kg: Number(maxCapacityKg),
        current_load_kg: Number(currentLoadKg),
        max_volume_m3: Number(maxVolumeM3),
        fuel_type: fuelType,
        fuel_level_pct: Number(fuelLevelPct),
        current_location: currentLocation.trim(),
        latitude: Number(latitude),
        longitude: Number(longitude),
        mileage_km: Number(mileageKm),
        driver_id: driverId === '' ? undefined : Number(driverId),
      };

      const updated = await api.updateVehicle(vehicle.vehicle_code, payload);
      onSuccess(updated);
      onClose();
    } catch (err: any) {
      console.error('Failed to update vehicle:', err);
      setErrorMsg(err.message || 'Unable to update vehicle in Supabase. Please verify input data.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto animate-in fade-in">
      <div className="relative w-full max-w-2xl rounded-2xl bg-white border border-slate-200 shadow-modal overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 border border-blue-200 text-blue-600 shadow-2xs">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 font-mono">
                  Edit Vehicle: {vehicle.vehicle_code}
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  {vehicle.type}
                </span>
              </div>
              <p className="text-xs text-slate-500">Modify fleet specifications, assigned driver, and operational state.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {/* Row 1: Model & Class */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Make & Model</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-semibold shadow-2xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Vehicle Class / Body Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 font-semibold outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs cursor-pointer"
              >
                {vehicleTypes.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 2: Status & Driver */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Operational Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 font-semibold outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs cursor-pointer"
              >
                {statuses.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center justify-between">
                <span>Assigned Commercial Driver</span>
                {loadingDrivers && <span className="text-[10px] text-slate-400">Loading...</span>}
              </label>
              <select
                value={driverId}
                onChange={(e) => setDriverId(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs cursor-pointer"
              >
                <option value="">-- No Driver Assigned (Available) --</option>
                {drivers.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.driver_code}) [{d.status} | HOS: {d.hours_of_service_remaining}h]
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 3: Max Payload & Current Load */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Max Payload (kg)</label>
              <div className="relative">
                <input
                  type="number"
                  min="500"
                  step="100"
                  value={maxCapacityKg}
                  onChange={(e) => setMaxCapacityKg(Number(e.target.value))}
                  required
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono font-bold text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
                />
                <Scale className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Current Load (kg)</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max={maxCapacityKg}
                  step="50"
                  value={currentLoadKg}
                  onChange={(e) => setCurrentLoadKg(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono font-bold text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
                />
                <Scale className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Volume (m³)</label>
              <div className="relative">
                <input
                  type="number"
                  min="5"
                  step="1"
                  value={maxVolumeM3}
                  onChange={(e) => setMaxVolumeM3(Number(e.target.value))}
                  required
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono font-bold text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
                />
                <Box className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
              </div>
            </div>
          </div>

          {/* Row 4: Fuel & Mileage */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Fuel Type</label>
              <select
                value={fuelType}
                onChange={(e) => setFuelType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs cursor-pointer"
              >
                <option value="Diesel">Diesel</option>
                <option value="Electric">Electric (BEV)</option>
                <option value="Hybrid">Hybrid</option>
                <option value="CNG">Compressed Natural Gas</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Fuel Level (%)</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={fuelLevelPct}
                  onChange={(e) => setFuelLevelPct(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono font-bold text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
                />
                <Fuel className="w-4 h-4 text-amber-500 absolute left-2.5 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Odometer Mileage (km)</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={mileageKm}
                  onChange={(e) => setMileageKm(Number(e.target.value))}
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono font-bold text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
                />
                <Gauge className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
              </div>
            </div>
          </div>

          {/* Row 5: Current Location & GPS */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Station / Location Hub</label>
              <div className="relative">
                <input
                  type="text"
                  value={currentLocation}
                  onChange={(e) => setCurrentLocation(e.target.value)}
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-white border border-slate-300 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
                />
                <MapPin className="w-4 h-4 text-blue-600 absolute left-2.5 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(e) => setLatitude(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(e) => setLongitude(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-300 text-xs font-mono text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-2xs"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors cursor-pointer shadow-2xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-all cursor-pointer"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              <span>{submitting ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
