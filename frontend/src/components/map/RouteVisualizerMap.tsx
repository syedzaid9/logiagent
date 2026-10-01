import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { 
  RouteItem, 
  RouteStats, 
  RouteOptimizeResult, 
  Shipment, 
  Vehicle, 
  Driver, 
  LocationItem 
} from '../../types';
import { 
  Map, 
  Navigation, 
  ArrowRight, 
  MapPin, 
  Truck, 
  AlertTriangle, 
  Clock, 
  DollarSign, 
  RefreshCw,
  Zap,
  Gauge,
  Search,
  Filter,
  Plus,
  Info,
  CheckCircle2,
  ExternalLink,
  Bot,
  User as UserIcon,
  Layers,
  X,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  Compass
} from 'lucide-react';

interface RouteVisualizerProps {
  initialShipmentCode?: string;
  onNavigate?: (tab: string) => void;
  onAskAI?: (prompt: string) => void;
}

export const RouteVisualizerMap: React.FC<RouteVisualizerProps> = ({ 
  initialShipmentCode = 'SHP-1001',
  onNavigate,
  onAskAI
}) => {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [stats, setStats] = useState<RouteStats | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<RouteItem | null>(null);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [locations, setLocations] = useState<LocationItem[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  
  // Modals
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [inspectedRoute, setInspectedRoute] = useState<RouteItem | null>(null);
  
  const [isOptimizeModalOpen, setIsOptimizeModalOpen] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizeResult, setOptimizeResult] = useState<RouteOptimizeResult | null>(null);
  const [optimizePriority, setOptimizePriority] = useState<'fastest' | 'shortest' | 'lowest_cost'>('fastest');
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    route_code: '',
    shipment_id: '',
    origin_id: '',
    destination_id: '',
    vehicle_id: '',
    driver_id: '',
    traffic_condition: 'Moderate',
    weather_condition: 'Clear',
    status: 'Planned'
  });

  // Map coordinates projection for SVG canvas (US Mainland: Lat 24 to 50, Lng -125 to -66)
  const mapWidth = 800;
  const mapHeight = 440;

  const projectCoords = (lat: number, lng: number): [number, number] => {
    const minLat = 24.0;
    const maxLat = 50.0;
    const minLng = -125.0;
    const maxLng = -66.0;

    const x = ((lng - minLng) / (maxLng - minLng)) * mapWidth;
    const y = mapHeight - ((lat - minLat) / (maxLat - minLat)) * mapHeight;
    return [Math.round(x), Math.round(y)];
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [routesData, statsData, shipmentsData, vehiclesData, driversData, locsData] = await Promise.all([
        api.getRoutes({
          search: searchQuery || undefined,
          status: statusFilter !== 'All' ? statusFilter : undefined
        }),
        api.getRouteStats(),
        api.getShipments(),
        api.getVehicles(),
        api.getDrivers(),
        api.getLocations()
      ]);

      setRoutes(routesData);
      setStats(statsData);
      setShipments(shipmentsData);
      setVehicles(vehiclesData);
      setDrivers(driversData);
      setLocations(locsData);

      // Set initial selected route
      if (routesData.length > 0) {
        if (initialShipmentCode) {
          const match = routesData.find(r => r.shipment_code === initialShipmentCode);
          setSelectedRoute(match || routesData[0]);
        } else if (!selectedRoute) {
          setSelectedRoute(routesData[0]);
        }
      }
    } catch (err) {
      console.error('Error loading route center data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleOpenOptimize = async (route?: RouteItem) => {
    const target = route || selectedRoute;
    if (!target) return;
    
    setInspectedRoute(target);
    setIsOptimizeModalOpen(true);
    setOptimizing(true);
    try {
      const result = await api.optimizeRoute({
        route_code: target.route_code,
        shipment_code: target.shipment_code,
        priority: optimizePriority
      });
      setOptimizeResult(result);
    } catch (err) {
      console.error('Error optimizing route:', err);
    } finally {
      setOptimizing(false);
    }
  };

  const handleApplyOptimization = async () => {
    if (!inspectedRoute) return;
    setOptimizing(true);
    try {
      const result = await api.optimizeRoute({
        route_code: inspectedRoute.route_code,
        shipment_code: inspectedRoute.shipment_code,
        priority: optimizePriority,
        persist: true
      });
      setOptimizeResult(result);
      if (result.persisted_route) {
        setSelectedRoute(result.persisted_route);
      }
      await loadData();
      setIsOptimizeModalOpen(false);
    } catch (err) {
      console.error('Error persisting route optimization:', err);
    } finally {
      setOptimizing(false);
    }
  };

  const handleCreateRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.origin_id || !createForm.destination_id) return;
    
    setCreating(true);
    try {
      const payload = {
        route_code: createForm.route_code || undefined,
        shipment_id: createForm.shipment_id ? parseInt(createForm.shipment_id) : undefined,
        origin_id: parseInt(createForm.origin_id),
        destination_id: parseInt(createForm.destination_id),
        vehicle_id: createForm.vehicle_id ? parseInt(createForm.vehicle_id) : undefined,
        driver_id: createForm.driver_id ? parseInt(createForm.driver_id) : undefined,
        traffic_condition: createForm.traffic_condition,
        weather_condition: createForm.weather_condition,
        status: createForm.status
      };

      const newRoute = await api.createRoute(payload);
      setSelectedRoute(newRoute);
      setIsCreateModalOpen(false);
      setCreateForm({
        route_code: '',
        shipment_id: '',
        origin_id: '',
        destination_id: '',
        vehicle_id: '',
        driver_id: '',
        traffic_condition: 'Moderate',
        weather_condition: 'Clear',
        status: 'Planned'
      });
      await loadData();
    } catch (err) {
      console.error('Error creating route:', err);
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'In Transit':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Completed':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Delayed':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'Assigned':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Cancelled':
        return 'bg-slate-100 text-slate-600 border-slate-300';
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <Compass className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Route Operations & Optimization</h1>
              <p className="text-xs text-slate-500">
                Dynamic corridor navigation, multi-hub waypoint tracking, and live transportation cost optimization.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => handleOpenOptimize()}
            disabled={!selectedRoute}
            className="px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs flex items-center gap-1.5 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Optimize Route</span>
          </button>

          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-2xs flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Plan Route</span>
          </button>

          <button
            onClick={loadData}
            className="p-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg transition-colors cursor-pointer"
            title="Refresh routes"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Dynamic Route KPIs */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-slate-500 uppercase block tracking-wider">Total Routes</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-slate-900 font-mono">{stats.total_routes}</span>
              <span className="text-[10px] text-slate-400 font-medium">network</span>
            </div>
          </div>

          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-blue-600 uppercase block tracking-wider">In Transit</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-blue-700 font-mono">{stats.active_routes}</span>
              <span className="text-[10px] text-blue-500 font-medium">active</span>
            </div>
          </div>

          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-amber-600 uppercase block tracking-wider">Planned</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-amber-700 font-mono">{stats.planned_routes}</span>
              <span className="text-[10px] text-amber-500 font-medium">queued</span>
            </div>
          </div>

          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-emerald-600 uppercase block tracking-wider">Completed</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-emerald-700 font-mono">{stats.completed_routes}</span>
              <span className="text-[10px] text-emerald-500 font-medium">delivered</span>
            </div>
          </div>

          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-slate-500 uppercase block tracking-wider">Avg Distance</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-slate-900 font-mono">{stats.average_distance_km}</span>
              <span className="text-[10px] text-slate-400 font-medium">km</span>
            </div>
          </div>

          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-indigo-600 uppercase block tracking-wider">Efficiency</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-indigo-700 font-mono">{stats.average_efficiency_pct}%</span>
              <span className="text-[10px] text-indigo-500 font-medium">SLA</span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Interactive Topology Map & Live Telemetry Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SVG Route Topology Visualizer */}
        <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-card flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between mb-3 z-10">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
              <Navigation className="w-4 h-4 text-blue-600" />
              <span>Continental US Supply Chain Corridor Topology</span>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Smooth</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Moderate</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500"></span> Heavy Delay</span>
            </div>
          </div>

          {/* SVG Map Canvas */}
          <div className="w-full aspect-[16/9] relative bg-slate-50/80 rounded-xl border border-slate-200 overflow-hidden flex items-center justify-center">
            {loading && routes.length === 0 ? (
              <div className="text-center font-mono text-xs text-blue-600 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                <span>Loading route topology...</span>
              </div>
            ) : (
              <svg
                viewBox={`0 0 ${mapWidth} ${mapHeight}`}
                className="w-full h-full"
                preserveAspectRatio="xMidYMid meet"
              >
                {/* Background Grid */}
                <defs>
                  <pattern id="routeGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="0.8" />
                  </pattern>
                  <linearGradient id="routeGradientLine" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#2563EB" />
                    <stop offset="50%" stopColor="#4F46E5" />
                    <stop offset="100%" stopColor="#059669" />
                  </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill="url(#routeGrid)" />

                {/* Regional Interstate Backbone Network */}
                <path
                  d="M 500 130 L 375 295 L 545 275 L 85 265 L 690 155 L 75 85 L 600 370 L 275 165 Z"
                  fill="none"
                  stroke="#CBD5E1"
                  strokeWidth="1.2"
                  strokeDasharray="4 4"
                />

                {/* Major Database Locations / Hub Nodes */}
                {locations.map((loc) => {
                  const [lx, ly] = projectCoords(loc.latitude, loc.longitude);
                  return (
                    <g key={loc.id} className="cursor-pointer group">
                      <circle cx={lx} cy={ly} r="4" fill="#2563EB" opacity="0.4" />
                      <circle cx={lx} cy={ly} r="2.5" fill="#2563EB" />
                      <text
                        x={lx}
                        y={ly - 7}
                        textAnchor="middle"
                        fill="#475569"
                        fontSize="9"
                        fontFamily="JetBrains Mono, monospace"
                        fontWeight="600"
                      >
                        {loc.location_code || loc.city}
                      </text>
                    </g>
                  );
                })}

                {/* Active Selected Route Polyline */}
                {selectedRoute?.polyline && selectedRoute.polyline.length > 1 && (
                  <>
                    <polyline
                      points={selectedRoute.polyline
                        .map(([lat, lng]) => projectCoords(lat, lng).join(','))
                        .join(' ')}
                      fill="none"
                      stroke="url(#routeGradientLine)"
                      strokeWidth="5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="drop-shadow-[0_2px_8px_rgba(37,99,235,0.3)]"
                    />

                    {/* Animated Pulse on Live Transit Path */}
                    <polyline
                      points={selectedRoute.polyline
                        .map(([lat, lng]) => projectCoords(lat, lng).join(','))
                        .join(' ')}
                      fill="none"
                      stroke="#FFFFFF"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeDasharray="8 14"
                      className="animate-pulse"
                    />
                  </>
                )}

                {/* Waypoints & Stops */}
                {selectedRoute?.waypoints && selectedRoute.waypoints.map((stop, idx) => {
                  const [sx, sy] = projectCoords(stop.lat, stop.lng);
                  const isOrigin = idx === 0;
                  const isDest = idx === selectedRoute.waypoints!.length - 1;

                  return (
                    <g key={idx}>
                      <circle
                        cx={sx}
                        cy={sy}
                        r={isOrigin || isDest ? "7" : "4.5"}
                        fill={isOrigin ? "#2563EB" : isDest ? "#059669" : "#D97706"}
                      />
                      <circle
                        cx={sx}
                        cy={sy}
                        r={isOrigin || isDest ? "3.5" : "2"}
                        fill="#FFFFFF"
                      />
                      <text
                        x={sx}
                        y={sy + 16}
                        textAnchor="middle"
                        fill="#0F172A"
                        fontSize="9"
                        fontWeight="bold"
                        fontFamily="sans-serif"
                      >
                        {isOrigin ? 'Origin' : isDest ? 'Destination' : 'Stop'}
                      </text>
                    </g>
                  );
                })}
              </svg>
            )}
          </div>

          {/* Active Route Telemetry Footer */}
          <div className="mt-3.5 p-3 rounded-lg bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-700">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 font-mono">{selectedRoute?.route_code || 'RT-SELECT'}:</span>
              <span className="font-medium text-slate-800">{selectedRoute?.origin_city || selectedRoute?.origin_name || 'Origin'} ➔ {selectedRoute?.destination_city || selectedRoute?.destination_name || 'Destination'}</span>
              {selectedRoute?.shipment_code && (
                <span className="text-slate-500 font-mono">({selectedRoute.shipment_code})</span>
              )}
            </div>
            
            <div className="flex items-center gap-3 font-mono text-[11px]">
              <span className="text-blue-700 font-bold">{selectedRoute?.planned_distance_km || 0} km</span>
              <span className="text-slate-300">|</span>
              <span className="text-emerald-700 font-bold">{selectedRoute?.planned_duration_min ? `${Math.floor(selectedRoute.planned_duration_min / 60)}h ${selectedRoute.planned_duration_min % 60}m` : '0h 0m'}</span>
            </div>
          </div>
        </div>

        {/* Selected Route Telemetry Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Selected Corridor</span>
                <h3 className="text-base font-bold text-slate-900 font-mono mt-0.5">
                  {selectedRoute?.route_code || 'Select Route'}
                </h3>
              </div>
              {selectedRoute && (
                <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${getStatusBadgeClass(selectedRoute.status)}`}>
                  {selectedRoute.status}
                </span>
              )}
            </div>

            {selectedRoute ? (
              <div className="mt-4 space-y-3.5 text-xs">
                {/* Corridor Overview */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Origin:</span>
                    <strong className="text-slate-800">{selectedRoute.origin_city}, {selectedRoute.origin_state}</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Destination:</span>
                    <strong className="text-slate-800">{selectedRoute.destination_city}, {selectedRoute.destination_state}</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Canonical Distance:</span>
                    <strong className="text-slate-900 font-mono font-bold">{selectedRoute.planned_distance_km} km</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Est. Duration:</span>
                    <strong className="text-slate-900 font-mono">
                      {Math.floor(selectedRoute.planned_duration_min / 60)}h {selectedRoute.planned_duration_min % 60}m
                    </strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Est. Transportation Cost:</span>
                    <strong className="text-emerald-700 font-mono font-bold">
                      ${selectedRoute.cost_total_usd?.toLocaleString() || '0.00'} USD
                    </strong>
                  </div>
                </div>

                {/* Assignments */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium flex items-center gap-1.5">
                      <Truck className="w-3.5 h-3.5 text-blue-600" /> Vehicle:
                    </span>
                    <span className="font-mono font-semibold text-slate-800">
                      {selectedRoute.vehicle_code || 'Unassigned'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium flex items-center gap-1.5">
                      <UserIcon className="w-3.5 h-3.5 text-purple-600" /> Driver:
                    </span>
                    <span className="font-semibold text-slate-800">
                      {selectedRoute.driver_name || 'Unassigned'}
                    </span>
                  </div>
                  {selectedRoute.shipment_code && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Linked Shipment:</span>
                      <span className="font-mono font-bold text-blue-600">
                        {selectedRoute.shipment_code}
                      </span>
                    </div>
                  )}
                </div>

                {/* Waypoint Stops Count */}
                <div className="flex items-center justify-between px-1 text-slate-500 text-[11px]">
                  <span>Waypoints: {selectedRoute.waypoints?.length || 0} checkpoints</span>
                  <span>Traffic: {selectedRoute.traffic_condition}</span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-400 text-xs">
                Select a route from the table below to inspect real-time corridor telemetry.
              </div>
            )}
          </div>

          {selectedRoute && (
            <div className="pt-3 border-t border-slate-100 flex items-center gap-2">
              <button
                onClick={() => {
                  setInspectedRoute(selectedRoute);
                  setIsDetailModalOpen(true);
                }}
                className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
              >
                Inspect Details
              </button>
              
              <button
                onClick={() => handleOpenOptimize(selectedRoute)}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Optimize</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 4. Live Routes Filter & Data Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        {/* Table Filter Bar */}
        <div className="p-4 border-b border-slate-100 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-slate-50/50">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by route code, shipment, vehicle, driver, city..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
            />
          </form>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium"
            >
              <option value="All">All Statuses</option>
              <option value="Planned">Planned</option>
              <option value="Assigned">Assigned</option>
              <option value="In Transit">In Transit</option>
              <option value="Delayed">Delayed</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase text-[10px] font-bold tracking-wider">
              <tr>
                <th className="px-4 py-3">Route Code</th>
                <th className="px-4 py-3">Origin ➔ Destination</th>
                <th className="px-4 py-3">Shipment</th>
                <th className="px-4 py-3">Vehicle / Driver</th>
                <th className="px-4 py-3">Distance & Time</th>
                <th className="px-4 py-3">Cost (USD)</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {routes.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400 text-xs">
                    {loading ? 'Loading route records...' : 'No routes found matching filter criteria.'}
                  </td>
                </tr>
              ) : (
                routes.map((r) => {
                  const isSelected = selectedRoute?.id === r.id;
                  return (
                    <tr
                      key={r.id}
                      onClick={() => setSelectedRoute(r)}
                      className={`hover:bg-blue-50/40 transition-colors cursor-pointer ${
                        isSelected ? 'bg-blue-50/60 font-medium' : ''
                      }`}
                    >
                      <td className="px-4 py-3">
                        <span className="font-mono font-bold text-slate-900">{r.route_code}</span>
                      </td>

                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5 text-slate-800">
                          <span>{r.origin_city || r.origin_name}</span>
                          <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>{r.destination_city || r.destination_name}</span>
                        </div>
                      </td>

                      <td className="px-4 py-3">
                        {r.shipment_code ? (
                          <span className="font-mono font-semibold text-blue-600">
                            {r.shipment_code}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">Unassigned</span>
                        )}
                      </td>

                      <td className="px-4 py-3">
                        <div className="text-slate-700">
                          <span className="font-mono font-semibold">{r.vehicle_code || '—'}</span>
                          {r.driver_name && (
                            <span className="text-slate-500 block text-[11px]">{r.driver_name}</span>
                          )}
                        </div>
                      </td>

                      <td className="px-4 py-3 font-mono">
                        <div className="text-slate-900 font-bold">{r.planned_distance_km} km</div>
                        <div className="text-slate-500 text-[11px]">
                          {Math.floor(r.planned_duration_min / 60)}h {r.planned_duration_min % 60}m
                        </div>
                      </td>

                      <td className="px-4 py-3 font-mono font-semibold text-emerald-700">
                        ${r.cost_total_usd?.toLocaleString() || '0.00'}
                      </td>

                      <td className="px-4 py-3">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadgeClass(r.status)}`}>
                          {r.status}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-right space-x-1.5" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => {
                            setInspectedRoute(r);
                            setIsDetailModalOpen(true);
                          }}
                          className="px-2 py-1 text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-medium transition-colors cursor-pointer"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleOpenOptimize(r)}
                          className="px-2 py-1 text-[11px] bg-blue-50 hover:bg-blue-100 text-blue-700 rounded font-medium transition-colors cursor-pointer"
                        >
                          Optimize
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODAL 1: Route Optimization Engine Modal */}
      {/* ========================================================================= */}
      {isOptimizeModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Route Optimization Engine</h3>
                  <p className="text-xs text-slate-500">
                    Calculated optimal highway corridors vs toll-free alternatives using live highway metrics.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOptimizeModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {optimizing ? (
                <div className="py-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                  <p className="text-xs font-medium text-slate-600">
                    Evaluating road networks, traffic conditions, and fuel efficiency models...
                  </p>
                </div>
              ) : optimizeResult ? (
                <div className="space-y-4">
                  {/* Origin ➔ Destination Banner */}
                  <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100 flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700">Corridor:</span>
                    <div className="flex items-center gap-1.5 font-bold text-blue-900">
                      <span>{optimizeResult.origin}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-blue-500" />
                      <span>{optimizeResult.destination}</span>
                    </div>
                  </div>

                  {/* Priority Selector */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-600">Optimization Goal:</span>
                    {(['fastest', 'shortest', 'lowest_cost'] as const).map((p) => (
                      <button
                        key={p}
                        onClick={async () => {
                          setOptimizePriority(p);
                          if (inspectedRoute) {
                            setOptimizing(true);
                            const res = await api.optimizeRoute({
                              route_code: inspectedRoute.route_code,
                              shipment_code: inspectedRoute.shipment_code,
                              priority: p
                            });
                            setOptimizeResult(res);
                            setOptimizing(false);
                          }
                        }}
                        className={`px-3 py-1 text-xs rounded-lg font-medium capitalize border transition-all cursor-pointer ${
                          optimizePriority === p
                            ? 'bg-blue-600 text-white border-blue-600 shadow-2xs'
                            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        {p.replace('_', ' ')}
                      </button>
                    ))}
                  </div>

                  {/* Comparison Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Primary Recommended Route */}
                    <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                          Recommended Primary
                        </span>
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">
                        {optimizeResult.recommended_route.corridor}
                      </h4>
                      <div className="space-y-1.5 text-xs text-slate-600 font-mono">
                        <div className="flex justify-between">
                          <span>Distance:</span>
                          <strong className="text-slate-900">{optimizeResult.recommended_route.distance_km} km</strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Est. Duration:</span>
                          <strong className="text-slate-900">{optimizeResult.recommended_route.duration_formatted}</strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Traffic:</span>
                          <span className="text-amber-700 font-sans font-medium">{optimizeResult.recommended_route.traffic_condition}</span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-emerald-200/60">
                          <span className="font-sans font-medium">Estimated Cost:</span>
                          <strong className="text-emerald-800 text-sm">
                            ${optimizeResult.recommended_route.estimated_cost_usd} USD
                          </strong>
                        </div>
                      </div>
                    </div>

                    {/* Alternative Bypass Route */}
                    {optimizeResult.alternative_routes && optimizeResult.alternative_routes[0] && (
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 bg-slate-200 px-2 py-0.5 rounded">
                            Alternative Route
                          </span>
                          <Clock className="w-4 h-4 text-slate-400" />
                        </div>
                        <h4 className="text-sm font-bold text-slate-800">
                          {optimizeResult.alternative_routes[0].corridor}
                        </h4>
                        <div className="space-y-1.5 text-xs text-slate-600 font-mono">
                          <div className="flex justify-between">
                            <span>Distance:</span>
                            <strong className="text-slate-800">{optimizeResult.alternative_routes[0].distance_km} km</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Est. Duration:</span>
                            <strong className="text-slate-800">{optimizeResult.alternative_routes[0].duration_formatted}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Traffic:</span>
                            <span className="text-slate-700 font-sans font-medium">{optimizeResult.alternative_routes[0].traffic_condition}</span>
                          </div>
                          <div className="flex justify-between pt-1 border-t border-slate-200">
                            <span className="font-sans font-medium">Estimated Cost:</span>
                            <strong className="text-slate-900 text-sm">
                              ${optimizeResult.alternative_routes[0].estimated_cost_usd} USD
                            </strong>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Summary / Guidance */}
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
                    <p className="leading-relaxed">
                      💡 {optimizeResult.recommendation_summary}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-xs text-slate-400">
                  No optimization results available.
                </div>
              )}
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2.5">
              <button
                onClick={() => setIsOptimizeModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer"
              >
                Close
              </button>
              <button
                onClick={handleApplyOptimization}
                disabled={optimizing || !optimizeResult}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Apply & Persist Corridor</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: Route Detail Inspection Modal (Step 15) */}
      {/* ========================================================================= */}
      {isDetailModalOpen && inspectedRoute && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-2xl rounded-2xl border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 font-mono font-bold text-xs">
                  {inspectedRoute.route_code.slice(0, 4)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900 font-mono">{inspectedRoute.route_code}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadgeClass(inspectedRoute.status)}`}>
                      {inspectedRoute.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Authoritative corridor telemetry and integrated logistics assignment.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsDetailModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Route Information Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Canonical Distance</span>
                  <strong className="text-base text-slate-900 font-mono font-bold">{inspectedRoute.planned_distance_km} km</strong>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Est. Duration</span>
                  <strong className="text-base text-blue-700 font-mono font-bold">
                    {Math.floor(inspectedRoute.planned_duration_min / 60)}h {inspectedRoute.planned_duration_min % 60}m
                  </strong>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Traffic Impact</span>
                  <strong className="text-sm text-slate-800 font-semibold">{inspectedRoute.traffic_condition}</strong>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Total Cost</span>
                  <strong className="text-base text-emerald-700 font-mono font-bold">
                    ${inspectedRoute.cost_total_usd?.toLocaleString() || '0.00'}
                  </strong>
                </div>
              </div>

              {/* Cross-Module Operational Links (Step 20) */}
              <div className="space-y-2.5">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Connected Logistics Entities
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Linked Shipment */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">Shipment</span>
                      <strong className="text-xs font-mono font-bold text-blue-600 block mt-0.5">
                        {inspectedRoute.shipment_code || 'Unlinked'}
                      </strong>
                      <span className="text-[11px] text-slate-500 block truncate">
                        {inspectedRoute.customer_name || 'Direct Corridor'}
                      </span>
                    </div>
                    {inspectedRoute.shipment_code && onNavigate && (
                      <button
                        onClick={() => {
                          setIsDetailModalOpen(false);
                          onNavigate('shipments');
                        }}
                        className="mt-2 text-[11px] text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 cursor-pointer"
                      >
                        <span>View Shipment</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>

                  {/* Linked Vehicle */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">Assigned Truck</span>
                      <strong className="text-xs font-mono font-bold text-slate-800 block mt-0.5">
                        {inspectedRoute.vehicle_code || 'Unassigned'}
                      </strong>
                      <span className="text-[11px] text-slate-500 block truncate">
                        {inspectedRoute.vehicle_type || 'Standard Fleet'}
                      </span>
                    </div>
                    {inspectedRoute.vehicle_code && onNavigate && (
                      <button
                        onClick={() => {
                          setIsDetailModalOpen(false);
                          onNavigate('fleet');
                        }}
                        className="mt-2 text-[11px] text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 cursor-pointer"
                      >
                        <span>View Fleet Unit</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>

                  {/* Linked Driver */}
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">Commercial Driver</span>
                      <strong className="text-xs font-bold text-slate-800 block mt-0.5">
                        {inspectedRoute.driver_name || 'Unassigned'}
                      </strong>
                      <span className="text-[11px] text-slate-500 font-mono block">
                        {inspectedRoute.driver_code || '—'}
                      </span>
                    </div>
                    {inspectedRoute.driver_code && onNavigate && (
                      <button
                        onClick={() => {
                          setIsDetailModalOpen(false);
                          onNavigate('drivers');
                        }}
                        className="mt-2 text-[11px] text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1 cursor-pointer"
                      >
                        <span>View Driver</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Waypoint Checkpoints */}
              {inspectedRoute.waypoints && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Corridor Checkpoint Schedule
                  </h4>
                  <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1 text-xs">
                    {inspectedRoute.waypoints.map((st, i) => (
                      <div key={i} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            st.type === 'Origin' ? 'bg-blue-500' : st.type === 'Destination' ? 'bg-emerald-500' : 'bg-amber-500'
                          }`}></span>
                          <span className="font-semibold text-slate-800">{st.name}</span>
                          <span className="text-slate-400 text-[11px]">({st.location})</span>
                        </div>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-600">
                          {st.type}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
              {onAskAI && (
                <button
                  onClick={() => {
                    setIsDetailModalOpen(false);
                    onAskAI(`Show details and optimize route ${inspectedRoute.route_code}`);
                  }}
                  className="px-3 py-1.5 text-xs font-semibold text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <Bot className="w-3.5 h-3.5" />
                  <span>Ask AI Assistant</span>
                </button>
              )}

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsDetailModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: Plan / Create New Route Modal (Step 4) */}
      {/* ========================================================================= */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                  <Plus className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Plan Dynamic Logistics Route</h3>
                  <p className="text-xs text-slate-500">
                    Assign shipment, origin hub, destination terminal, and fleet personnel.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateRoute} className="p-6 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Route Code (Optional):</label>
                  <input
                    type="text"
                    placeholder="Auto-generated (e.g. RT-XXXX)"
                    value={createForm.route_code}
                    onChange={(e) => setCreateForm({ ...createForm, route_code: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Link Shipment:</label>
                  <select
                    value={createForm.shipment_id}
                    onChange={(e) => {
                      const sId = e.target.value;
                      const matched = shipments.find(s => s.id.toString() === sId);
                      setCreateForm({
                        ...createForm,
                        shipment_id: sId,
                        origin_id: matched ? matched.origin_id.toString() : createForm.origin_id,
                        destination_id: matched ? matched.destination_id.toString() : createForm.destination_id,
                        vehicle_id: matched?.vehicle_id ? matched.vehicle_id.toString() : createForm.vehicle_id,
                        driver_id: matched?.driver_id ? matched.driver_id.toString() : createForm.driver_id
                      });
                    }}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                  >
                    <option value="">None (Corridor Only)</option>
                    {shipments.map(s => (
                      <option key={s.id} value={s.id}>
                        {s.shipment_code} ({s.origin_city} ➔ {s.destination_city})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Origin Hub *:</label>
                  <select
                    required
                    value={createForm.origin_id}
                    onChange={(e) => setCreateForm({ ...createForm, origin_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium"
                  >
                    <option value="">Select Origin...</option>
                    {locations.map(loc => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.city}, {loc.state})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Destination Terminal *:</label>
                  <select
                    required
                    value={createForm.destination_id}
                    onChange={(e) => setCreateForm({ ...createForm, destination_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-medium"
                  >
                    <option value="">Select Destination...</option>
                    {locations.map(loc => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.city}, {loc.state})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assign Vehicle:</label>
                  <select
                    value={createForm.vehicle_id}
                    onChange={(e) => setCreateForm({ ...createForm, vehicle_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 font-mono"
                  >
                    <option value="">Unassigned</option>
                    {vehicles.map(v => (
                      <option key={v.id} value={v.id}>
                        {v.vehicle_code} — {v.model} ({v.type}) [{v.status}]
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assign Driver:</label>
                  <select
                    value={createForm.driver_id}
                    onChange={(e) => setCreateForm({ ...createForm, driver_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                  >
                    <option value="">Unassigned</option>
                    {drivers.map(d => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.driver_code}) — {d.license_type} [{d.status}]
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2.5 -mx-6 -mb-6 mt-4">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{creating ? 'Planning...' : 'Create Route'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
