import React from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export interface AlertBadgeProps {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' | string;
  showIcon?: boolean;
}

export const AlertBadge: React.FC<AlertBadgeProps> = ({ severity, showIcon = true }) => {
  const norm = (severity || 'LOW').toUpperCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  let Icon = Info;

  switch (norm) {
    case 'CRITICAL':
      styles = 'bg-rose-50 text-rose-700 border-rose-200';
      Icon = AlertCircle;
      break;
    case 'HIGH':
      styles = 'bg-amber-50 text-amber-700 border-amber-200';
      Icon = AlertTriangle;
      break;
    case 'MEDIUM':
      styles = 'bg-blue-50 text-blue-700 border-blue-200';
      Icon = AlertCircle;
      break;
    case 'LOW':
    case 'INFO':
    default:
      styles = 'bg-slate-100 text-slate-600 border-slate-200';
      Icon = Info;
      break;
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold border ${styles}`}>
      {showIcon && <Icon className="w-3 h-3 shrink-0" />}
      <span>{norm}</span>
    </span>
  );
};
