import React from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Bot,
  Package,
  Truck,
  Users,
  Map,
  BarChart3,
  FileText,
  Bell,
  Settings,
  Sparkles,
  ArrowRight,
  UserCheck,
  Radio
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onNavigate: (tab: string) => void;
  unreadCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onNavigate, unreadCount }) => {
  const { role } = useAuth();

  const getRoleHeader = () => {
    switch (role) {
      case 'Driver':
        return 'Driver Tasks';
      case 'Dispatcher':
        return 'Dispatch Control';
      case 'Fleet Manager':
        return 'Fleet & Assets';
      case 'Analyst':
        return 'Supply Chain Analytics';
      case 'Admin':
        return 'System Governance';
      case 'Operations Team':
        return 'Operations Center';
      case 'Logistics Manager':
      default:
        return 'Logistics Operations';
    }
  };

  const getNavItems = () => {
    if (role === 'Driver') {
      return [
        { id: 'dashboard', label: 'My Portal', icon: LayoutDashboard, badge: null },
        { id: 'shipments', label: 'My Shipments', icon: Package, badge: null },
        { id: 'routes', label: 'My Route', icon: Map, badge: null },
        { id: 'chat', label: 'AI Driver Assistant', icon: Bot, badge: 'AI', isAi: true },
        { id: 'notifications', label: 'Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
      ];
    }

    if (role === 'Dispatcher') {
      return [
        { id: 'dashboard', label: 'Dispatch Console', icon: Radio, badge: null },
        { id: 'shipments', label: 'Shipment Queue', icon: Package, badge: null },
        { id: 'vehicles', label: 'Vehicle Fleet', icon: Truck, badge: null },
        { id: 'drivers', label: 'Driver Roster', icon: Users, badge: null },
        { id: 'routes', label: 'Route Optimization', icon: Map, badge: null },
        { id: 'chat', label: 'AI Assistant', icon: Bot, badge: 'AI', isAi: true },
        { id: 'documents', label: 'SOP Documents', icon: FileText, badge: null },
        { id: 'notifications', label: 'Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
      ];
    }

    if (role === 'Fleet Manager') {
      return [
        { id: 'dashboard', label: 'Fleet Console', icon: LayoutDashboard, badge: null },
        { id: 'vehicles', label: 'Vehicle Fleet', icon: Truck, badge: null },
        { id: 'drivers', label: 'Driver Roster', icon: Users, badge: null },
        { id: 'routes', label: 'Route Telemetry', icon: Map, badge: null },
        { id: 'analytics', label: 'Fleet Analytics', icon: BarChart3, badge: null },
        { id: 'documents', label: 'Maintenance SOPs', icon: FileText, badge: null },
        { id: 'chat', label: 'AI Assistant', icon: Bot, badge: 'AI', isAi: true },
        { id: 'notifications', label: 'Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
      ];
    }

    if (role === 'Analyst') {
      return [
        { id: 'dashboard', label: 'Analytics Console', icon: LayoutDashboard, badge: null },
        { id: 'analytics', label: 'KPIs & Cost Modeling', icon: BarChart3, badge: null },
        { id: 'shipments', label: 'Shipments Query', icon: Package, badge: null },
        { id: 'routes', label: 'Route Corridors', icon: Map, badge: null },
        { id: 'vehicles', label: 'Fleet Capacity', icon: Truck, badge: null },
        { id: 'documents', label: 'Policy Knowledge Base', icon: FileText, badge: null },
        { id: 'chat', label: 'AI Analyst Agent', icon: Bot, badge: 'AI', isAi: true },
        { id: 'notifications', label: 'Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
      ];
    }

    if (role === 'Admin') {
      return [
        { id: 'dashboard', label: 'Governance Console', icon: LayoutDashboard, badge: null },
        { id: 'users', label: 'User & RBAC Accounts', icon: UserCheck, badge: 'Admin' },
        { id: 'shipments', label: 'Shipments', icon: Package, badge: null },
        { id: 'vehicles', label: 'Fleet Vehicles', icon: Truck, badge: null },
        { id: 'drivers', label: 'Driver Roster', icon: Users, badge: null },
        { id: 'routes', label: 'Corridor Optimization', icon: Map, badge: null },
        { id: 'analytics', label: 'Analytics & KPIs', icon: BarChart3, badge: null },
        { id: 'documents', label: 'SOP Knowledge Base', icon: FileText, badge: null },
        { id: 'chat', label: 'AI Assistant', icon: Bot, badge: 'AI', isAi: true },
        { id: 'notifications', label: 'System Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
        { id: 'settings', label: 'System Settings', icon: Settings, badge: null },
      ];
    }

    if (role === 'Operations Team') {
      return [
        { id: 'dashboard', label: 'Operations Workspace', icon: LayoutDashboard, badge: null },
        { id: 'shipments', label: 'Cargo Exceptions', icon: Package, badge: null },
        { id: 'routes', label: 'Route Bottlenecks', icon: Map, badge: null },
        { id: 'vehicles', label: 'Fleet Status', icon: Truck, badge: null },
        { id: 'drivers', label: 'Drivers', icon: Users, badge: null },
        { id: 'documents', label: 'SOP Policies', icon: FileText, badge: null },
        { id: 'chat', label: 'AI Operations Agent', icon: Bot, badge: 'AI', isAi: true },
        { id: 'notifications', label: 'Active Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
      ];
    }

    // Default: Logistics Manager
    return [
      { id: 'dashboard', label: 'Operations Dashboard', icon: LayoutDashboard, badge: null },
      { id: 'shipments', label: 'Shipment Management', icon: Package, badge: null },
      { id: 'routes', label: 'Route Optimization', icon: Map, badge: null },
      { id: 'vehicles', label: 'Fleet & Capacity', icon: Truck, badge: null },
      { id: 'drivers', label: 'Driver Roster', icon: Users, badge: null },
      { id: 'analytics', label: 'Analytics & KPIs', icon: BarChart3, badge: null },
      { id: 'users', label: 'Team Accounts', icon: UserCheck, badge: null },
      { id: 'documents', label: 'SOP Knowledge Base', icon: FileText, badge: 'Docs' },
      { id: 'chat', label: 'AI Operations Agent', icon: Bot, badge: 'AI', isAi: true },
      { id: 'notifications', label: 'Alerts', icon: Bell, badge: unreadCount > 0 ? unreadCount : null },
    ];
  };

  const navItems = getNavItems();

  return (
    <aside className="w-60 bg-white border-r border-slate-200 flex flex-col justify-between p-3.5 min-h-[calc(100vh-4rem)] shrink-0 select-none">
      <div className="space-y-6">
        <div className="space-y-0.5">
          <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
            {getRoleHeader()}
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== null && item.badge !== undefined && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-medium ${
                      isActive
                        ? 'bg-blue-100 text-blue-800'
                        : item.isAi
                        ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                        : item.badge === 'Admin'
                        ? 'bg-slate-100 text-slate-700 border border-slate-200'
                        : typeof item.badge === 'number'
                        ? 'bg-rose-50 text-rose-700 border border-rose-200 font-bold'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom AI Assistant Card */}
      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded-md bg-indigo-600 text-white flex items-center justify-center">
            <Sparkles className="w-3 h-3" />
          </div>
          <span className="text-xs font-bold text-slate-850">LogiAgent Assistant</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-normal">
          {role === 'Driver'
            ? 'Get delivery updates and route assistance.'
            : 'Query live shipments, fleet capacity, and operational policies.'}
        </p>
        <button
          onClick={() => onNavigate('chat')}
          className="w-full py-1.5 px-2.5 rounded-lg bg-white hover:bg-slate-100 text-slate-850 text-xs font-semibold border border-slate-200 shadow-card transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <span>Ask Assistant</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
        </button>
      </div>
    </aside>
  );
};
