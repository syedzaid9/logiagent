import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';

interface PermissionGateProps {
  permission?: string;
  allowedRoles?: UserRole[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  permission,
  allowedRoles,
  fallback = null,
  children,
}) => {
  const { role, hasPermission } = useAuth();

  if (role === 'Admin') {
    return <>{children}</>;
  }

  if (permission && !hasPermission(permission)) {
    return <>{fallback}</>;
  }

  if (allowedRoles && role && !allowedRoles.includes(role)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

export const RoleGate: React.FC<{
  allowedRoles: UserRole[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}> = ({ allowedRoles, fallback = null, children }) => {
  const { role } = useAuth();
  if (!role) return <>{fallback}</>;
  if (role === 'Admin' || allowedRoles.includes(role)) {
    return <>{children}</>;
  }
  return <>{fallback}</>;
};
