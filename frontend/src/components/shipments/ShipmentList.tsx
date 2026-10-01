import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../../api/services';
import { Shipment, Customer } from '../../types';
import { StatusBadge } from './StatusBadge';
import { ShipmentDetailModal } from './ShipmentDetailModal';
import { CreateShipmentModal } from './CreateShipmentModal';
import { 
  Package, 
  Search, 
  Filter, 
  AlertTriangle, 
  Eye, 
  Truck, 
  MapPin, 
  RefreshCw,
  Clock,
  ArrowUpDown,
  Plus,
  Navigation,
  Sparkles,
  CheckCircle2,
  Boxes,
  Layers,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  XCircle
} from 'lucide-react';

interface ShipmentListProps {
  onViewRoute?: (code: string) => void;
  onAskAI?: (prompt: string) => void;
}

export const ShipmentList: React.FC<ShipmentListProps> = ({ onViewRoute, onAskAI }) => {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [customerFilter, setCustomerFilter] = useState('All');
  const [delayedOnly, setDelayedOnly] = useState(false);
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'eta' | 'delay' | 'weight' | 'code'>('newest');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Modals
  const [selectedShipment, setSelectedShipment] = useState<Shipment | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const statuses = ['All', 'In Transit', 'Delayed', 'Delivered', 'Pending', 'Assigned', 'Picked Up', 'Failed', 'Cancelled'];

  const loadData = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);

      const [shipmentsData, customersData] = await Promise.all([
        api.getShipments(),
        api.getCustomers().catch(() => []),
      ]);

      setShipments(shipmentsData || []);
      setCustomers(customersData || []);
    } catch (err: any) {
      console.error('Error loading shipments:', err);
      setErrorMsg('Unable to load shipment records from database. Please check connection and retry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleShipmentUpdated = (updated: Shipment) => {
    setShipments((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    setSelectedShipment(updated);
    setToastMessage(`Shipment ${updated.shipment_code} updated successfully in Supabase!`);
    setTimeout(() => setToastMessage(null), 5000);
  };

  // Filter & Search Logic
  const filteredShipments = useMemo(() => {
    return shipments.filter((s) => {
      // Status Filter
      if (statusFilter !== 'All') {
        if (statusFilter === 'Delayed') {
          if (s.status !== 'Delayed' && s.delay_minutes <= 0) return false;
        } else if (s.status.toLowerCase() !== statusFilter.toLowerCase()) {
          return false;
        }
      }

      // Delayed Only toggle
      if (delayedOnly) {
        if (s.status !== 'Delayed' && s.delay_minutes <= 0) return false;
      }

      // Customer Filter
      if (customerFilter !== 'All') {
        if (s.customer_name !== customerFilter && String(s.customer_id) !== customerFilter) {
          return false;
        }
      }

      // Search Query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const codeMatch = s.shipment_code?.toLowerCase().includes(query);
        const custMatch = s.customer_name?.toLowerCase().includes(query);
        const originMatch = (s.origin_city || s.origin_name)?.toLowerCase().includes(query);
        const destMatch = (s.destination_city || s.destination_name)?.toLowerCase().includes(query);
        const cargoMatch = s.cargo_type?.toLowerCase().includes(query);
        const driverMatch = s.driver_name?.toLowerCase().includes(query);
        const vehicleMatch = s.vehicle_code?.toLowerCase().includes(query);
        const reasonMatch = s.delay_reason?.toLowerCase().includes(query);

        if (!codeMatch && !custMatch && !originMatch && !destMatch && !cargoMatch && !driverMatch && !vehicleMatch && !reasonMatch) {
          return false;
        }
      }

      return true;
    });
  }, [shipments, statusFilter, customerFilter, delayedOnly, searchQuery]);

  // Sorting Logic
  const sortedShipments = useMemo(() => {
    const list = [...filteredShipments];
    switch (sortBy) {
      case 'newest':
        return list.sort((a, b) => new Date(b.created_at || b.expected_delivery).getTime() - new Date(a.created_at || a.expected_delivery).getTime());
      case 'oldest':
        return list.sort((a, b) => new Date(a.created_at || a.expected_delivery).getTime() - new Date(b.created_at || b.expected_delivery).getTime());
      case 'eta':
        return list.sort((a, b) => new Date(a.estimated_eta || a.expected_delivery).getTime() - new Date(b.estimated_eta || b.expected_delivery).getTime());
      case 'delay':
        return list.sort((a, b) => b.delay_minutes - a.delay_minutes);
      case 'weight':
        return list.sort((a, b) => b.weight_kg - a.weight_kg);
      case 'code':
        return list.sort((a, b) => a.shipment_code.localeCompare(b.shipment_code));
      default:
        return list;
    }
  }, [filteredShipments, sortBy]);

  // Dynamic KPI Calculations from REAL database records
  const kpis = useMemo(() => {
    const total = shipments.length;
    const inTransit = shipments.filter((s) => s.status === 'In Transit').length;
    const delivered = shipments.filter((s) => s.status === 'Delivered').length;
    const delayed = shipments.filter((s) => s.status === 'Delayed' || s.delay_minutes > 0).length;
    const pending = shipments.filter((s) => s.status === 'Pending' || s.status === 'Assigned').length;

    return { total, inTransit, delivered, delayed, pending };
  }, [shipments]);

  // Pagination Slice
  const totalPages = Math.max(1, Math.ceil(sortedShipments.length / pageSize));
  const paginatedShipments = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedShipments.slice(startIndex, startIndex + pageSize);
  }, [sortedShipments, currentPage, pageSize]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, customerFilter, delayedOnly, searchQuery, pageSize]);

  const handleCreateSuccess = (newShipment: Shipment) => {
    setShipments((prev) => [newShipment, ...prev]);
    setToastMessage(`Shipment ${newShipment.shipment_code} created successfully in Supabase!`);
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setStatusFilter('All');
    setCustomerFilter('All');
    setDelayedOnly(false);
    setSortBy('newest');
  };

  const existingCodes = useMemo(() => shipments.map((s) => s.shipment_code), [shipments]);

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-2xs animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-700 hover:text-emerald-900">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-2xs">
              <Package className="w-4 h-4" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Shipments</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Monitor and manage all shipments from one place.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-2xs transition-colors"
            title="Reload shipment telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-semibold text-white shadow-2xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Create Shipment</span>
          </button>
        </div>
      </div>

      {/* 2. KPI Summary Cards (Real database data) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Total Shipments */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Total Shipments</span>
            <div className="w-7 h-7 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-600">
              <Layers className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">{kpis.total}</div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Supabase freight records</span>
        </div>

        {/* In Transit */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-blue-600 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">In Transit</span>
            <div className="w-7 h-7 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <Truck className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-700 font-mono">{kpis.inTransit}</div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Active on interstate routes</span>
        </div>

        {/* Delivered */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-emerald-600 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Delivered</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-700 font-mono">{kpis.delivered}</div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Successful completions</span>
        </div>

        {/* Delayed */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-amber-600 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Delayed</span>
            <div className="w-7 h-7 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-800 font-mono">{kpis.delayed}</div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Requiring dispatcher review</span>
        </div>

        {/* Pending / Assigned */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Pending / Queued</span>
            <div className="w-7 h-7 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
              <Clock className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-800 font-mono">{kpis.pending}</div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Awaiting dispatch/pickup</span>
        </div>
      </div>

      {/* 3. Filter & Search Controls Card */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-3.5">
        {/* Top Row: Search bar & Sort dropdown */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Search Bar */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by shipment code, customer, city, cargo, driver, or vehicle..."
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-xs text-slate-900 placeholder-slate-400 outline-none transition-all shadow-2xs"
            />
          </div>

          {/* Customer Dropdown Filter & Sort */}
          <div className="flex items-center gap-2.5 w-full md:w-auto shrink-0">
            <select
              value={customerFilter}
              onChange={(e) => setCustomerFilter(e.target.value)}
              className="flex-1 md:flex-none px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 text-xs text-slate-700 font-medium outline-none shadow-2xs"
            >
              <option value="All">All Customers</option>
              {customers.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>

            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 shadow-2xs">
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-transparent text-xs text-slate-700 font-medium outline-none cursor-pointer"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="eta">Delivery / ETA</option>
                <option value="delay">Highest Delay</option>
                <option value="weight">Heaviest Weight</option>
                <option value="code">Shipment Code</option>
              </select>
            </div>
          </div>
        </div>

        {/* Bottom Row: Status Tabs & Delayed Toggle */}
        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
              <Filter className="w-3 h-3" />
              <span>Status:</span>
            </span>
            {statuses.map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                  statusFilter === st
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Delayed Only Toggle */}
          <button
            type="button"
            onClick={() => setDelayedOnly(!delayedOnly)}
            className={`px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
              delayedOnly
                ? 'bg-amber-100 text-amber-800 border border-amber-300 shadow-2xs'
                : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
            }`}
          >
            <AlertTriangle className={`w-3.5 h-3.5 ${delayedOnly ? 'text-amber-600' : 'text-slate-400'}`} />
            <span>Delayed Only</span>
          </button>
        </div>
      </div>

      {/* Error State Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={loadData}
            className="px-3 py-1 rounded-lg bg-rose-600 text-white font-semibold text-xs hover:bg-rose-700 transition-colors shadow-2xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* 4. Shipment Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        {loading ? (
          <div className="p-16 text-center text-slate-500 text-xs flex flex-col items-center justify-center gap-3">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
            <span className="font-medium">Loading telemetry records from Supabase PostgreSQL...</span>
          </div>
        ) : sortedShipments.length === 0 ? (
          /* Empty State */
          <div className="p-16 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center mx-auto text-slate-400">
              <Package className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">No shipments found</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                No active records match the current filter criteria. Try adjusting your search query or status filter.
              </p>
            </div>
            <button
              onClick={handleResetFilters}
              className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4 pl-5">Shipment</th>
                  <th className="py-3.5 px-4">Customer</th>
                  <th className="py-3.5 px-4">Origin ➔ Destination</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Vehicle & Driver</th>
                  <th className="py-3.5 px-4">Weight</th>
                  <th className="py-3.5 px-4">ETA / Schedule</th>
                  <th className="py-3.5 px-4 pr-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedShipments.map((s) => (
                  <tr
                    key={s.id}
                    onClick={() => setSelectedShipment(s)}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                  >
                    {/* Shipment Code */}
                    <td className="py-3.5 px-4 pl-5">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-md bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0">
                          <Package className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <strong className="font-mono font-bold text-slate-900 block group-hover:text-blue-600 transition-colors">
                            {s.shipment_code}
                          </strong>
                          <span className="text-[10px] text-slate-400 block truncate max-w-[120px]">
                            {s.cargo_type || 'Freight'}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Customer */}
                    <td className="py-3.5 px-4 text-slate-700 font-medium">
                      <span className="block truncate max-w-[140px]">{s.customer_name || 'Enterprise Client'}</span>
                    </td>

                    {/* Corridor */}
                    <td className="py-3.5 px-4 text-slate-700">
                      <div className="flex items-center gap-1.5">
                        <span className="text-slate-500 font-medium">{s.origin_city || 'Origin'}</span>
                        <span className="text-blue-600 text-xs font-bold">➔</span>
                        <span className="text-slate-900 font-semibold">{s.destination_city || 'Dest'}</span>
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3.5 px-4">
                      <StatusBadge status={s.status} size="sm" />
                    </td>

                    {/* Vehicle & Driver */}
                    <td className="py-3.5 px-4 text-slate-600">
                      <div className="text-[11px] leading-tight">
                        <strong className="text-slate-800 font-mono block">
                          {s.vehicle_code || <span className="text-slate-400 font-sans font-normal italic">Unassigned</span>}
                        </strong>
                        <span className="text-slate-500 block truncate max-w-[120px]">
                          {s.driver_name || <span className="text-slate-400 italic">No driver</span>}
                        </span>
                      </div>
                    </td>

                    {/* Weight */}
                    <td className="py-3.5 px-4 font-mono text-slate-700">
                      {s.weight_kg?.toLocaleString() || 1000} kg
                    </td>

                    {/* ETA / Delay */}
                    <td className="py-3.5 px-4">
                      {s.delay_minutes > 0 ? (
                        <div className="flex items-center gap-1 text-amber-800 font-bold text-[11px]">
                          <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                          <span>+{s.delay_minutes}m Delay</span>
                        </div>
                      ) : s.status === 'Delivered' ? (
                        <span className="text-emerald-700 font-medium text-[11px]">Delivered</span>
                      ) : (
                        <div className="text-slate-600 text-[11px]">
                          <span className="text-emerald-700 font-medium block">On Schedule</span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {new Date(s.expected_delivery).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 pr-5 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => setSelectedShipment(s)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors flex items-center gap-1 shadow-2xs"
                          title="View complete shipment details and timeline"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Details</span>
                        </button>

                        {onViewRoute && (
                          <button
                            type="button"
                            onClick={() => onViewRoute(s.shipment_code)}
                            className="p-1.5 rounded-lg bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 text-slate-600 hover:text-blue-600 transition-colors shadow-2xs"
                            title="Open route corridor map"
                          >
                            <Navigation className="w-3 h-3" />
                          </button>
                        )}

                        {onAskAI && (
                          <button
                            type="button"
                            onClick={() => onAskAI(`Explain current status, ETA, and any delivery risks for shipment ${s.shipment_code}.`)}
                            className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 transition-colors shadow-2xs"
                            title="Ask LogiAgent about this shipment"
                          >
                            <Sparkles className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 5. Pagination Controls Footer */}
        {!loading && sortedShipments.length > 0 && (
          <div className="px-5 py-3.5 bg-slate-50/80 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <strong className="text-slate-900 font-semibold">{((currentPage - 1) * pageSize) + 1}</strong> to{' '}
              <strong className="text-slate-900 font-semibold">
                {Math.min(currentPage * pageSize, sortedShipments.length)}
              </strong>{' '}
              of <strong className="text-slate-900 font-semibold">{sortedShipments.length}</strong> shipments
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] text-slate-400">Rows per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                  className="px-2 py-1 rounded bg-white border border-slate-200 text-xs text-slate-700 font-medium outline-none shadow-2xs cursor-pointer"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 shadow-2xs transition-colors"
                  title="Previous page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>

                <div className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 font-mono text-xs font-semibold text-slate-800 shadow-2xs">
                  {currentPage} / {totalPages}
                </div>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 shadow-2xs transition-colors"
                  title="Next page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 6. Shipment Detail Modal */}
      {selectedShipment && (
        <ShipmentDetailModal
          shipment={selectedShipment}
          onClose={() => setSelectedShipment(null)}
          onUpdate={handleShipmentUpdated}
          onViewRoute={onViewRoute}
          onAskAI={onAskAI}
        />
      )}

      {/* 7. Create Shipment Modal */}
      {isCreateModalOpen && (
        <CreateShipmentModal
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleCreateSuccess}
          existingCodes={existingCodes}
        />
      )}
    </div>
  );
};
