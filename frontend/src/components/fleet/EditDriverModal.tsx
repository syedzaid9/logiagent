import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { Driver, Vehicle } from '../../types';
import {
  X,
  Users,
  Mail,
  Phone,
  ShieldCheck,
  Clock,
  Star,
  Truck,
  Loader2,
  AlertCircle,
  Save
} from 'lucide-react';

interface EditDriverModalProps {
  driver: Driver;
  onClose: () => void;
  onSuccess: (updatedDriver: Driver) => void;
}

export const EditDriverModal: React.FC<EditDriverModalProps> = ({
  driver,
  onClose,
  onSuccess,
}) => {
  // Form State
  const [name, setName] = useState(driver.name);
  const [email, setEmail] = useState(driver.email);
  const [phone, setPhone] = useState(driver.phone);
  const [licenseNumber, setLicenseNumber] = useState(driver.license_number);
  const [licenseType, setLicenseType] = useState(driver.license_type || 'CDL-A');
  const [status, setStatus] = useState<Driver['status']>(driver.status || 'Available');
  const [rating, setRating] = useState<number>(driver.rating || 4.8);
  const [hoursRemaining, setHoursRemaining] = useState<number>(driver.hours_of_service_remaining ?? 11.0);
  const [currentVehicleId, setCurrentVehicleId] = useState<number | ''>(driver.current_vehicle_id || '');

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loadingVehicles, setLoadingVehicles] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchVehicles = async () => {
      try {
        setLoadingVehicles(true);
        // Fetch all vehicles
        const vList = await api.getVehicles();
        setVehicles(vList || []);
      } catch (err) {
        console.error('Failed to load vehicles:', err);
      } finally {
        setLoadingVehicles(false);
      }
    };

    fetchVehicles();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!name.trim()) {
      setErrorMsg('Please enter the full legal name of the driver.');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setErrorMsg('Please enter a valid corporate email address.');
      return;
    }
    if (!licenseNumber.trim()) {
      setErrorMsg('Please specify the CDL license number.');
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        name: name.trim(),
        email: email.trim().toLowerCase(),
        phone: phone.trim(),
        license_number: licenseNumber.trim().toUpperCase(),
        license_type: licenseType,
        status: status,
        rating: Number(rating),
        hours_of_service_remaining: Number(hoursRemaining),
        current_vehicle_id: currentVehicleId ? Number(currentVehicleId) : null,
      };

      const result = await api.updateDriver(driver.driver_code, payload);
      onSuccess(result);
      onClose();
    } catch (err: any) {
      console.error('Failed to update driver:', err);
      setErrorMsg(err.message || 'Failed to update driver details. Please check values and retry.');
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
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 tracking-tight">
                  Edit Driver Profile
                </h3>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  {driver.driver_code}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Update FMCSA HOS balance, CDL credentials, operational status, and vehicle assignments.
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
          {/* Row 1: Full Name & Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Full Legal Name <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                required
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Operational Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as Driver['status'])}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs cursor-pointer"
              >
                <option value="Available">Available (Ready for Dispatch)</option>
                <option value="Assigned">Assigned (Assigned to Vehicle/Load)</option>
                <option value="On Duty">On Duty (Active Commercial Operations)</option>
                <option value="Rest">Rest (Mandatory DOT Rest Break)</option>
                <option value="Off Duty">Off Duty (Off Shift)</option>
              </select>
            </div>
          </div>

          {/* Row 2: Email & Phone */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Corporate Email <span className="text-blue-600">*</span>
              </label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Contact Phone <span className="text-blue-600">*</span>
              </label>
              <div className="relative">
                <Phone className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                  required
                />
              </div>
            </div>
          </div>

          {/* Row 3: CDL License Number & License Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                License / CDL Number <span className="text-blue-600">*</span>
              </label>
              <div className="relative">
                <ShieldCheck className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={licenseNumber}
                  onChange={(e) => setLicenseNumber(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                License Endorsement / Class
              </label>
              <select
                value={licenseType}
                onChange={(e) => setLicenseType(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs cursor-pointer"
              >
                <option value="CDL-A">CDL-A (Combination Freight & Heavy-Duty)</option>
                <option value="CDL-B">CDL-B (Single Commercial Heavy Vehicle)</option>
                <option value="Standard">Standard Commercial (Light Fleet)</option>
              </select>
            </div>
          </div>

          {/* Row 4: HOS Remaining & Driver Rating */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Hours of Service Remaining (Max 11.0h)
              </label>
              <div className="relative">
                <Clock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="11"
                  value={hoursRemaining}
                  onChange={(e) => setHoursRemaining(Number(e.target.value))}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Safety & Performance Rating
              </label>
              <div className="relative">
                <Star className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                <input
                  type="number"
                  step="0.1"
                  min="1.0"
                  max="5.0"
                  value={rating}
                  onChange={(e) => setRating(Number(e.target.value))}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs"
                />
              </div>
            </div>
          </div>

          {/* Row 5: Assign Fleet Truck */}
          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              Assigned Fleet Truck (Bidirectional Sync)
            </label>
            <div className="relative">
              <Truck className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
              <select
                value={currentVehicleId}
                onChange={(e) => setCurrentVehicleId(e.target.value ? Number(e.target.value) : '')}
                className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none shadow-2xs cursor-pointer"
              >
                <option value="">No Vehicle Assigned (Pool Driver)</option>
                {vehicles.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.vehicle_code} — {v.model} ({v.type}) [{v.status}]
                  </option>
                ))}
              </select>
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
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
