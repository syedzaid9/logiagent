import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { Customer, LocationItem, Vehicle, Driver, Shipment } from '../../types';
import { 
  X, 
  PackagePlus, 
  Building2, 
  MapPin, 
  Truck, 
  User, 
  Calendar, 
  Scale, 
  Box, 
  Thermometer, 
  FileText, 
  Loader2, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

interface CreateShipmentModalProps {
  onClose: () => void;
  onSuccess: (newShipment: Shipment) => void;
  existingCodes?: string[];
}

export const CreateShipmentModal: React.FC<CreateShipmentModalProps> = ({
  onClose,
  onSuccess,
  existingCodes = [],
}) => {
  // Form State
  const [shipmentCode, setShipmentCode] = useState('');
  const [customerId, setCustomerId] = useState<number | ''>('');
  const [originId, setOriginId] = useState<number | ''>('');
  const [destinationId, setDestinationId] = useState<number | ''>('');
  const [vehicleId, setVehicleId] = useState<number | ''>('');
  const [driverId, setDriverId] = useState<number | ''>('');
  const [cargoType, setCargoType] = useState('General Freight');
  const [weightKg, setWeightKg] = useState<number>(2500);
  const [volumeM3, setVolumeM3] = useState<number>(18.5);
  const [temperatureControlled, setTemperatureControlled] = useState(false);
  const [targetTempCelsius, setTargetTempCelsius] = useState<number | ''>('');
  const [expectedDelivery, setExpectedDelivery] = useState('');
  const [specialInstructions, setSpecialInstructions] = useState('');

  // Dropdown options
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [locations, setLocations] = useState<LocationItem[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);

  // Submitting state
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    // Generate suggested code
    const highestNum = existingCodes.reduce((max, code) => {
      const match = code.match(/SHP-(\d+)/i);
      if (match) {
        const num = parseInt(match[1], 10);
        return num > max ? num : max;
      }
      return max;
    }, 1000);
    setShipmentCode(`SHP-${highestNum + 1}`);

    // Default expected delivery 48 hours from now
    const d = new Date();
    d.setHours(d.getHours() + 48);
    // Format for datetime-local input YYYY-MM-DDTHH:mm
    const localIso = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    setExpectedDelivery(localIso);

    // Fetch resources
    const fetchResources = async () => {
      try {
        setLoadingMeta(true);
        const [custData, locData, vehData, drivData] = await Promise.all([
          api.getCustomers().catch(() => []),
          api.getLocations().catch(() => []),
          api.getVehicles({ status: 'Available' }).catch(() => []),
          api.getDrivers({ status: 'Available' }).catch(() => []),
        ]);

        setCustomers(custData || []);
        setLocations(locData || []);
        setVehicles(vehData || []);
        setDrivers(drivData || []);

        if (custData && custData.length > 0) setCustomerId(custData[0].id);
        if (locData && locData.length > 1) {
          setOriginId(locData[0].id);
          setDestinationId(locData[1].id);
        }
      } catch (err) {
        console.error('Failed to load resources for shipment creation:', err);
      } finally {
        setLoadingMeta(false);
      }
    };

    fetchResources();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // Form validation
    if (!shipmentCode.trim()) {
      setErrorMsg('Please specify a unique shipment code (e.g. SHP-1037).');
      return;
    }
    if (!customerId) {
      setErrorMsg('Please select a customer.');
      return;
    }
    if (!originId || !destinationId) {
      setErrorMsg('Please specify both origin and destination hubs.');
      return;
    }
    if (originId === destinationId) {
      setErrorMsg('Origin and destination locations cannot be identical.');
      return;
    }
    if (!expectedDelivery) {
      setErrorMsg('Please specify the scheduled delivery deadline.');
      return;
    }
    if (weightKg <= 0) {
      setErrorMsg('Cargo weight must be greater than 0 kg.');
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        shipment_code: shipmentCode.trim().toUpperCase(),
        customer_id: Number(customerId),
        origin_id: Number(originId),
        destination_id: Number(destinationId),
        vehicle_id: vehicleId ? Number(vehicleId) : null,
        driver_id: driverId ? Number(driverId) : null,
        status: vehicleId && driverId ? 'Assigned' : 'Pending',
        cargo_type: cargoType.trim(),
        weight_kg: Number(weightKg),
        volume_m3: Number(volumeM3) || 10.0,
        temperature_controlled: Boolean(temperatureControlled),
        target_temp_celsius: temperatureControlled && targetTempCelsius !== '' ? Number(targetTempCelsius) : null,
        expected_delivery: new Date(expectedDelivery).toISOString(),
        special_instructions: specialInstructions.trim() || null,
      };

      const result = await api.createShipment(payload);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      console.error('Create shipment error:', err);
      setErrorMsg(err.message || 'Unable to register shipment. Please check parameters and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-2xs">
              <PackagePlus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Create New Shipment</h3>
              <p className="text-xs text-slate-500">Register freight manifest into the Supabase database.</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body / Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {errorMsg && (
            <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {loadingMeta ? (
            <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span>Loading customer and network hubs from Supabase...</span>
            </div>
          ) : (
            <>
              {/* Row 1: Code & Customer */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Shipment Code <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={shipmentCode}
                    onChange={(e) => setShipmentCode(e.target.value)}
                    placeholder="e.g. SHP-1037"
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs font-mono font-semibold text-slate-900 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Customer Account <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={customerId}
                    onChange={(e) => setCustomerId(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  >
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.company_name})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 2: Origin & Destination */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Origin Hub <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={originId}
                    onChange={(e) => setOriginId(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  >
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} — {loc.city}, {loc.state}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Destination Hub / Site <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={destinationId}
                    onChange={(e) => setDestinationId(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  >
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} — {loc.city}, {loc.state}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 3: Cargo specs */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Cargo Classification
                  </label>
                  <input
                    type="text"
                    value={cargoType}
                    onChange={(e) => setCargoType(e.target.value)}
                    placeholder="e.g. Consumer Electronics"
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Gross Weight (kg) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="number"
                    min="1"
                    step="10"
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs font-mono text-slate-900 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Volume (m³)
                  </label>
                  <input
                    type="number"
                    min="0.1"
                    step="0.5"
                    value={volumeM3}
                    onChange={(e) => setVolumeM3(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs font-mono text-slate-900 outline-none"
                  />
                </div>
              </div>

              {/* Row 4: Fleet & Driver Assignment (Optional) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Assign Vehicle (Optional)
                  </label>
                  <select
                    value={vehicleId}
                    onChange={(e) => setVehicleId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  >
                    <option value="">-- No vehicle assigned (Pending) --</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.vehicle_code} — {v.type} ({v.current_location})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Assign Driver (Optional)
                  </label>
                  <select
                    value={driverId}
                    onChange={(e) => setDriverId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  >
                    <option value="">-- No driver assigned (Pending) --</option>
                    {drivers.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.driver_code}) · {d.hours_of_service_remaining}h HOS
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 5: Schedule & Cold Chain */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Scheduled Delivery Window <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={expectedDelivery}
                    onChange={(e) => setExpectedDelivery(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                  />
                </div>

                <div className="flex flex-col justify-end">
                  <label className="flex items-center gap-2 cursor-pointer pb-2 text-xs font-semibold text-slate-700 select-none">
                    <input
                      type="checkbox"
                      checked={temperatureControlled}
                      onChange={(e) => setTemperatureControlled(e.target.checked)}
                      className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                    />
                    <span>Requires Cold Chain / Temperature Control</span>
                  </label>

                  {temperatureControlled && (
                    <input
                      type="number"
                      step="0.5"
                      value={targetTempCelsius}
                      onChange={(e) => setTargetTempCelsius(e.target.value ? Number(e.target.value) : '')}
                      placeholder="Target temp in °C (e.g. 4.0)"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none"
                    />
                  )}
                </div>
              </div>

              {/* Special Instructions */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Special Delivery Instructions / Handling Protocols
                </label>
                <textarea
                  value={specialInstructions}
                  onChange={(e) => setSpecialInstructions(e.target.value)}
                  rows={2}
                  placeholder="e.g. High-value freight; mandatory dock check-in; call receiver 1 hour prior."
                  className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-900 outline-none resize-none"
                />
              </div>
            </>
          )}

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || loadingMeta}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold shadow-2xs transition-colors flex items-center gap-1.5"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{submitting ? 'Creating Shipment...' : 'Create Shipment'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
