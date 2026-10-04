import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  Boxes, 
  Bell, 
  LogOut, 
  Search, 
  Menu, 
  X,
  ShieldCheck,
  KeyRound
} from 'lucide-react';
import { ChangePasswordModal } from '../auth/ChangePasswordModal';

interface HeaderProps {
  activeTab: string;
  onNavigate: (tab: string) => void;
  onToggleMobileSidebar?: () => void;
  isMobileSidebarOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ 
  onNavigate,
  onToggleMobileSidebar,
  isMobileSidebarOpen 
}) => {
  const { user, role, unreadCount, logout } = useAuth();
  const [headerSearch, setHeaderSearch] = useState('');
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (headerSearch.trim()) {
      onNavigate('shipments');
    }
  };

  const getRoleBadgeStyle = (r: string) => {
    switch (r) {
      case 'Admin':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Logistics Manager':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Dispatcher':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Fleet Manager':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'Analyst':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'Operations Team':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Driver':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <>
      <header className="h-15 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40">
        {/* Brand & Mobile Hamburger */}
        <div className="flex items-center gap-4">
          {/* Mobile Toggle Button */}
          {onToggleMobileSidebar && (
            <button
              onClick={onToggleMobileSidebar}
              className="md:hidden p-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
            >
              {isMobileSidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          )}

          <div 
            onClick={() => onNavigate('dashboard')}
            className="flex items-center gap-2.5 cursor-pointer select-none"
          >
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Boxes className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-slate-850">
                  LogiAgent
                </span>
                <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded border border-slate-200">
                  Operations
                </span>
              </div>
            </div>
          </div>

          {/* Live Network Status Indicator */}
          <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-slate-200 text-xs">
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 live-pulse"></span>
              <span className="font-medium text-[11px]">RBAC Active • Supabase Live</span>
            </div>
          </div>
        </div>

        {/* Center Search Bar */}
        <form onSubmit={handleSearchSubmit} className="hidden md:flex items-center flex-1 max-w-sm mx-6">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search shipments, drivers, routes..."
              value={headerSearch}
              onChange={(e) => setHeaderSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-850 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
        </form>

        {/* Right Actions: Authenticated User Badge, Password Change & Logout */}
        <div className="flex items-center gap-3">
          {/* Real User Role Badge (Non-interactive display) */}
          <div className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold ${getRoleBadgeStyle(role || 'Guest')}`}>
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{role || 'Authenticated'}</span>
          </div>

          {/* Change Password Button */}
          <button
            onClick={() => setShowChangePasswordModal(true)}
            className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 hover:text-blue-700 transition-colors cursor-pointer"
            title="Change My Password"
          >
            <KeyRound className="w-4 h-4" />
          </button>

          {/* Notification Bell */}
          <button
            onClick={() => onNavigate('notifications')}
            className="relative p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
            title="Operational Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500"></span>
            )}
          </button>

          {/* User Profile Pill & Logout Button */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
            <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-xs font-semibold text-white">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden xl:block text-left">
              <div className="text-xs font-semibold text-slate-850 leading-tight">
                {user?.full_name || 'Operator'}
              </div>
              <div className="text-[10px] text-slate-500">
                {user?.email || ''}
              </div>
            </div>

            <button
              onClick={logout}
              className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors ml-1 cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {showChangePasswordModal && (
        <ChangePasswordModal onClose={() => setShowChangePasswordModal(false)} />
      )}
    </>
  );
};
