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
  Plus
} from 'lucide-react';

interface CreateVehicleModalProps {
  onClose: () => void;
  onSuccess: (newVehicle: Vehicle) => void;
  existingCodes?: string[];
}

export const CreateVehicleModal: React.FC<CreateVehicleModalProps> = ({
  onClose,
  onSuccess,
  existingCodes = [],
}) => {
  // Form State
  const [vehicleCode, setVehicleCode] = useState('');
  const [model, setModel] = useState('Freightliner Cascadia 2026');
  const [type, setType] = useState('Semi-Truck (Dry Van)');
  const [maxCapacityKg, setMaxCapacityKg] = useState<number>(20000);
  const [maxVolumeM3, setMaxVolumeM3] = useState<number>(80.0);
  const [fuelType, setFuelType] = useState('Diesel');
  const [fuelLevelPct, setFuelLevelPct] = useState<number>(100);
  const [currentLocation, setCurrentLocation] = useState('Central Superhub, Chicago, IL');
  const [latitude, setLatitude] = useState<number>(41.8781);
  const [longitude, setLongitude] = useState<number>(-87.6298);
  const [mileageKm, setMileageKm] = useState<number>(25000);
  const [driverId, setDriverId] = useState<number | ''>('');

  const [availableDrivers, setAvailableDrivers] = useState<Driver[]>([]);
  const [loadingDrivers, setLoadingDrivers] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const vehicleTypes = [
    { label: 'Semi-Truck (Dry Van)', defaultCap: 20000, defaultVol: 80 },
    { label: 'Reefer (Refrigerated)', defaultCap: 18000, defaultVol: 72 },
    { label: 'Flatbed', defaultCap: 22000, defaultVol: 85 },
    { label: 'Box Truck', defaultCap: 6000, defaultVol: 35 },
    { label: 'Sprinter Van', defaultCap: 2200, defaultVol: 14 },
  ];

  useEffect(() => {
    // Generate suggested code
    const highestNum = existingCodes.reduce((max, code) => {
      const match = code.match(/TRK-(\d+)/i);
      if (match) {
        const num = parseInt(match[1], 10);
        return num > max ? num : max;
      }
      return max;
    }, 100);
    setVehicleCode(`TRK-${highestNum + 1}`);

    // Fetch available drivers
    const fetchDrivers = async () => {
      try {
        setLoadingDrivers(true);
        const drivers = await api.getDrivers({ status: 'Available' });
        setAvailableDrivers(drivers || []);
      } catch (err) {
        console.error('Failed to load available drivers:', err);
      } finally {
        setLoadingDrivers(false);
      }
    };

    fetchDrivers();
  }, [existingCodes]);

  const handleTypeChange = (selectedType: string) => {
    setType(selectedType);
    const match = vehicleTypes.find((v) => v.label === selectedType);
    if (match) {
      setMaxCapacityKg(match.defaultCap);
      setMaxVolumeM3(match.defaultVol);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!vehicleCode.trim()) {
      setErrorMsg('Please enter a unique vehicle code (e.g. TRK-113).');
      return;
    }
    if (!model.trim()) {
      setErrorMsg('Please specify the vehicle manufacturer & model.');
      return;
    }
    if (maxCapacityKg <= 0) {
      setErrorMsg('Maximum capacity must be greater than 0 kg.');
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        vehicle_code: vehicleCode.trim().toUpperCase(),
        model: model.trim(),
        type,
        max_capacity_kg: Number(maxCapacityKg),
        current_load_kg: 0.0,
        max_volume_m3: Number(maxVolumeM3),
        current_volume_m3: 0.0,
        status: driverId ? 'Assigned' : 'Available',
        current_location: currentLocation.trim(),
        latitude: Number(latitude),
        longitude: Number(longitude),
        fuel_level_pct: Number(fuelLevelPct),
        fuel_type: fuelType,
        mileage_km: Number(mileageKm),
        driver_id: driverId ? Number(driverId) : null,
      };

      const result = await api.createVehicle(payload);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      console.error('Failed to register vehicle:', err);
      setErrorMsg(err.message || 'Failed to register vehicle. Please check connection and retry.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl shadow-modal overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-2xs">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Register New Fleet Vehicle
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Add a commercial freight vehicle with payload telemetry and initial hub location.
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
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1 text-xs">
          {/* Row 1: Vehicle Code & Model */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Vehicle Code <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                value={vehicleCode}
                onChange={(e) => setVehicleCode(e.target.value)}
                placeholder="e.g. TRK-113"
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                required
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Make & Model <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="e.g. Freightliner Cascadia 2026"
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                required
              />
            </div>
          </div>

          {/* Row 2: Vehicle Class / Type & Fuel Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Vehicle Class <span className="text-blue-600">*</span>
              </label>
              <select
                value={type}
                onChange={(e) => handleTypeChange(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs cursor-pointer"
              >
                {vehicleTypes.map((t) => (
                  <option key={t.label} value={t.label}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Powertrain / Fuel Type
              </label>
              <select
                value={fuelType}
                onChange={(e) => setFuelType(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs cursor-pointer"
              >
                <option value="Diesel">Diesel</option>
                <option value="Electric">Electric (BEV)</option>
                <option value="Hybrid">Hybrid</option>
              </select>
            </div>
          </div>

          {/* Row 3: Max Capacity (kg) & Max Volume (m3) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Max Payload Capacity (kg) <span className="text-blue-600">*</span>
              </label>
              <div className="relative">
                <Scale className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="number"
                  min="100"
                  max="45000"
                  value={maxCapacityKg}
                  onChange={(e) => setMaxCapacityKg(Number(e.target.value))}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Max Cargo Volume (m³)
              </label>
              <div className="relative">
                <Box className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="number"
                  min="5"
                  max="120"
                  value={maxVolumeM3}
                  onChange={(e) => setMaxVolumeM3(Number(e.target.value))}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                />
              </div>
            </div>
          </div>

          {/* Row 4: Initial Location & Driver Assignment */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Current Hub Location
              </label>
              <div className="relative">
                <MapPin className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={currentLocation}
                  onChange={(e) => setCurrentLocation(e.target.value)}
                  placeholder="e.g. Dallas Freight Hub, TX"
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Assign Commercial Driver (Optional)
              </label>
              <div className="relative">
                <User className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <select
                  value={driverId}
                  onChange={(e) => setDriverId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs cursor-pointer"
                >
                  <option value="">Unassigned (Ready for Dispatch)</option>
                  {availableDrivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.driver_code}) — {d.license_type}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Row 5: Coordinates & Initial Odometer */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-500 text-[11px] mb-1 font-medium">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(e) => setLatitude(Number(e.target.value))}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-mono text-xs focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
              />
            </div>
            <div>
              <label className="block text-slate-500 text-[11px] mb-1 font-medium">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(e) => setLongitude(Number(e.target.value))}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-mono text-xs focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
              />
            </div>
            <div>
              <label className="block text-slate-500 text-[11px] mb-1 font-medium">Fuel Level (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={fuelLevelPct}
                onChange={(e) => setFuelLevelPct(Number(e.target.value))}
                className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-mono text-xs focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
              />
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 font-semibold transition-colors cursor-pointer shadow-2xs"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-all shadow-2xs flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Registering...</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Register Vehicle</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
