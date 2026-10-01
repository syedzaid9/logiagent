import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { LoginView } from './components/auth/LoginView';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardOverview } from './components/dashboard/DashboardOverview';
import { AIAssistantPanel } from './components/chat/AIAssistantPanel';
import { ShipmentList } from './components/shipments/ShipmentList';
import { VehicleGrid } from './components/fleet/VehicleGrid';
import { DriverRoster } from './components/fleet/DriverRoster';
import { RouteVisualizerMap } from './components/map/RouteVisualizerMap';
import { AnalyticsView } from './components/analytics/AnalyticsView';
import { PolicyExplorer } from './components/rag/PolicyExplorer';
import { NotificationCenter } from './components/notifications/NotificationCenter';
import { UserManagementView } from './components/admin/UserManagementView';
import { SystemSettingsView } from './components/settings/SystemSettingsView';
import { UnauthorizedAccess } from './components/common/UnauthorizedAccess';
import { Truck } from 'lucide-react';

export const App: React.FC = () => {
  const { isAuthenticated, isLoading, role, unreadCount, hasPermission } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [inspectRouteCode, setInspectRouteCode] = useState('SHP-1001');
  const [assistantInitialQuery, setAssistantInitialQuery] = useState<string | null>(null);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const handleInspectRoute = (code: string) => {
    setInspectRouteCode(code);
    setActiveTab('routes');
  };

  const handleAskAI = (prompt: string) => {
    setAssistantInitialQuery(prompt);
    setActiveTab('chat');
  };

  const handleNavigate = (tab: string) => {
    setActiveTab(tab);
    setIsMobileSidebarOpen(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F5F7F9] flex flex-col items-center justify-center text-slate-800">
        <div className="h-12 w-12 rounded-xl bg-blue-600 flex items-center justify-center shadow-md mb-4 animate-pulse">
          <Truck className="h-6 w-6 text-white" />
        </div>
        <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2" />
        <div className="text-xs text-slate-500 font-medium">Restoring LogiAgent Security Session...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return (
    <div className="min-h-screen bg-[#F5F7F9] text-slate-850 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Navigation Bar */}
      <Header
        activeTab={activeTab}
        onNavigate={handleNavigate}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
        isMobileSidebarOpen={isMobileSidebarOpen}
      />

      <div className="flex flex-1 relative bg-[#F5F7F9]">
        {/* Left Sidebar (Desktop & Mobile Drawer) */}
        <div className={`
          ${isMobileSidebarOpen ? 'block fixed inset-y-16 left-0 z-50 shadow-2xl' : 'hidden md:flex'}
        `}>
          <Sidebar
            activeTab={activeTab}
            onNavigate={handleNavigate}
            unreadCount={unreadCount}
          />
        </div>

        {/* Mobile Backdrop */}
        {isMobileSidebarOpen && (
          <div
            onClick={() => setIsMobileSidebarOpen(false)}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 md:hidden"
          ></div>
        )}

        {/* Main Dashboard & Workspace Canvas */}
        <main className="flex-1 p-4 sm:p-6 lg:p-7 max-w-7xl mx-auto w-full bg-[#F5F7F9]">
          {activeTab === 'dashboard' && (
            <DashboardOverview 
              onNavigate={handleNavigate} 
              onViewRoute={handleInspectRoute}
            />
          )}

          {(activeTab === 'chat' || activeTab === 'assistant') && (
            <AIAssistantPanel 
              onNavigateTab={handleNavigate}
              initialQuery={assistantInitialQuery}
              onClearInitialQuery={() => setAssistantInitialQuery(null)}
            />
          )}

          {activeTab === 'shipments' && (
            <ShipmentList 
              onViewRoute={handleInspectRoute}
              onAskAI={handleAskAI}
            />
          )}

          {(activeTab === 'vehicles' || activeTab === 'fleet') && (
            <VehicleGrid 
              onAskAI={handleAskAI}
              onViewShipment={(code) => {
                setInspectRouteCode(code);
                setActiveTab('routes');
              }}
            />
          )}

          {activeTab === 'drivers' && (
            role === 'Driver' ? (
              <UnauthorizedAccess
                requiredPermission="drivers:read_all"
                requiredRoles={['Admin', 'Logistics Manager', 'Dispatcher', 'Fleet Manager']}
                resourceName="Driver Roster Administration"
                onNavigateHome={() => handleNavigate('dashboard')}
              />
            ) : (
              <DriverRoster 
                onAskAI={handleAskAI}
                onViewVehicle={(_vehicleCode) => {
                  setActiveTab('vehicles');
                }}
                onViewShipment={(code) => {
                  setInspectRouteCode(code);
                  setActiveTab('routes');
                }}
              />
            )
          )}

          {activeTab === 'routes' && (
            <RouteVisualizerMap 
              initialShipmentCode={inspectRouteCode} 
              onNavigate={handleNavigate}
              onAskAI={handleAskAI}
            />
          )}

          {activeTab === 'analytics' && (
            role === 'Driver' ? (
              <UnauthorizedAccess
                requiredPermission="analytics:read_all"
                requiredRoles={['Admin', 'Logistics Manager', 'Dispatcher', 'Fleet Manager', 'Analyst']}
                resourceName="Executive Analytics & Cost Modeling"
                onNavigateHome={() => handleNavigate('dashboard')}
              />
            ) : (
              <AnalyticsView />
            )
          )}

          {(activeTab === 'documents' || activeTab === 'rag') && (
            <PolicyExplorer />
          )}

          {activeTab === 'users' && (
            (role === 'Admin' || role === 'Logistics Manager' || hasPermission('users:read')) ? (
              <UserManagementView />
            ) : (
              <UnauthorizedAccess
                requiredPermission="users:read"
                requiredRoles={['Admin', 'Logistics Manager']}
                resourceName="User Accounts & RBAC Governance"
                onNavigateHome={() => handleNavigate('dashboard')}
              />
            )
          )}

          {activeTab === 'notifications' && (
            <NotificationCenter />
          )}

          {activeTab === 'settings' && (
            (role === 'Admin' || hasPermission('settings:manage') || hasPermission('settings:read')) ? (
              <SystemSettingsView onNavigate={handleNavigate} />
            ) : (
              <UnauthorizedAccess
                requiredPermission="settings:manage"
                requiredRoles={['Admin']}
                resourceName="System Configuration & Settings"
                onNavigateHome={() => handleNavigate('dashboard')}
              />
            )
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
