import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { DriverDashboard } from './DriverDashboard';
import { DispatcherDashboard } from './DispatcherDashboard';
import { AdminDashboard } from './AdminDashboard';
import { FleetManagerDashboard } from './FleetManagerDashboard';
import { AnalystDashboard } from './AnalystDashboard';
import { OperationsTeamDashboard } from './OperationsTeamDashboard';
import { LogisticsManagerDashboard } from './LogisticsManagerDashboard';

interface DashboardOverviewProps {
  onNavigate: (tab: string) => void;
  onViewRoute?: (code: string) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ onNavigate, onViewRoute }) => {
  const { role } = useAuth();

  switch (role) {
    case 'Driver':
      return <DriverDashboard onNavigate={onNavigate} />;
    case 'Dispatcher':
      return <DispatcherDashboard onNavigate={onNavigate} onViewRoute={onViewRoute} />;
    case 'Admin':
      return <AdminDashboard onNavigateToUsers={() => onNavigate('users')} onNavigate={onNavigate} />;
    case 'Fleet Manager':
      return <FleetManagerDashboard onNavigate={onNavigate} />;
    case 'Analyst':
      return <AnalystDashboard onNavigate={onNavigate} />;
    case 'Operations Team':
      return <OperationsTeamDashboard onNavigate={onNavigate} onViewRoute={onViewRoute} />;
    case 'Logistics Manager':
    default:
      return <LogisticsManagerDashboard onNavigate={onNavigate} onViewRoute={onViewRoute} />;
  }
};

export default DashboardOverview;
