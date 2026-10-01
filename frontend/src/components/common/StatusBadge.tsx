import React from 'react';

export interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const norm = (status || '').toLowerCase().trim();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  // Shipment / General Statuses
  if (['delivered', 'completed', 'active', 'ready', 'healthy', 'online'].includes(norm)) {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['in transit', 'in_transit', 'picked up', 'picked_up', 'assigned', 'on duty', 'on_duty'].includes(norm)) {
    colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (['delayed', 'pending_approval', 'maintenance', 'warning', 'degraded'].includes(norm)) {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (['cancelled', 'failed', 'suspended', 'critical', 'unavailable', 'deactivated'].includes(norm)) {
    colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (['pending', 'pending_activation', 'off duty', 'off_duty', 'planned', 'draft'].includes(norm)) {
    colorClasses = 'bg-slate-50 text-slate-600 border-slate-200';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-semibold rounded-md border ${sizeClasses} ${colorClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-75" />
      {status || 'Unknown'}
    </span>
  );
};
