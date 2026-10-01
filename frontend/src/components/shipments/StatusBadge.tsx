import React from 'react';
import { ShipmentStatus } from '../../types';

interface StatusBadgeProps {
  status: ShipmentStatus | string;
  size?: 'xs' | 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const styles: Record<string, { badge: string; dot: string }> = {
    'In Transit': {
      badge: 'bg-blue-50 text-blue-700 border-blue-200',
      dot: 'bg-blue-500',
    },
    'Delivered': {
      badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      dot: 'bg-emerald-500',
    },
    'Delayed': {
      badge: 'bg-amber-50 text-amber-800 border-amber-200',
      dot: 'bg-amber-500',
    },
    'Pending': {
      badge: 'bg-slate-100 text-slate-700 border-slate-200',
      dot: 'bg-slate-400',
    },
    'Assigned': {
      badge: 'bg-sky-50 text-sky-700 border-sky-200',
      dot: 'bg-sky-500',
    },
    'Picked Up': {
      badge: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      dot: 'bg-indigo-500',
    },
    'Failed': {
      badge: 'bg-rose-50 text-rose-700 border-rose-200',
      dot: 'bg-rose-500',
    },
    'Cancelled': {
      badge: 'bg-rose-50 text-rose-700 border-rose-200',
      dot: 'bg-rose-500',
    },
  };

  const current = styles[status] || {
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
  };

  const sizeClasses = 
    size === 'xs' ? 'px-2 py-0.5 text-[10px]' :
    size === 'sm' ? 'px-2.5 py-0.5 text-[11px]' : 
    'px-3 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 font-semibold rounded-full border ${sizeClasses} ${current.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${current.dot}`}></span>
      <span>{status}</span>
    </span>
  );
};
