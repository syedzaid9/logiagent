import React from 'react';
import { ShieldAlert, ArrowLeft, Lock, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface UnauthorizedAccessProps {
  requiredPermission?: string;
  requiredRoles?: string[];
  resourceName?: string;
  onNavigateHome?: () => void;
}

export const UnauthorizedAccess: React.FC<UnauthorizedAccessProps> = ({
  requiredPermission,
  requiredRoles,
  resourceName = 'this section',
  onNavigateHome,
}) => {
  const { role, user } = useAuth();

  return (
    <div className="min-h-[500px] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 shadow-xl p-8 text-center space-y-6">
        {/* Shield Icon Badge */}
        <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto text-rose-600 shadow-sm animate-pulse">
          <ShieldAlert className="w-8 h-8" />
        </div>

        {/* Heading */}
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <Lock className="w-3 h-3" />
            <span>403 Forbidden Access</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900">
            Access Restricted by RBAC
          </h2>
          <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
            Your current operational role (<strong className="text-slate-800 font-semibold">{role || 'Authenticated User'}</strong>) does not have sufficient permissions to access {resourceName}.
          </p>
        </div>

        {/* Security Details Card */}
        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/90 text-left space-y-2 text-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span>Operator Identity:</span>
            <span className="font-semibold text-slate-700">{user?.email || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between text-slate-500">
            <span>Assigned Role:</span>
            <span className="font-semibold text-slate-700">{role || 'N/A'}</span>
          </div>
          {requiredPermission && (
            <div className="flex items-center justify-between text-slate-500">
              <span>Required Permission:</span>
              <span className="font-mono text-[11px] font-semibold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-100">
                {requiredPermission}
              </span>
            </div>
          )}
          {requiredRoles && requiredRoles.length > 0 && (
            <div className="flex items-center justify-between text-slate-500">
              <span>Authorized Roles:</span>
              <span className="font-semibold text-slate-700">{requiredRoles.join(', ')}</span>
            </div>
          )}
        </div>

        {/* Action Button */}
        {onNavigateHome && (
          <button
            onClick={onNavigateHome}
            className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md shadow-blue-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Accessible Dashboard</span>
          </button>
        )}
      </div>
    </div>
  );
};
