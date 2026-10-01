import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  bgColor?: string;
  trend?: string;
  trendUp?: boolean;
  highlight?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-slate-600',
  bgColor = 'bg-slate-50',
  trend,
  trendUp,
  highlight = false,
}) => {
  return (
    <div
      className={`p-4 rounded-xl border bg-white transition-all ${
        highlight
          ? 'border-blue-200 shadow-2xs ring-1 ring-blue-500/10'
          : 'border-slate-200/90 shadow-2xs hover:border-slate-300'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-500">{title}</span>
        <div className={`w-7 h-7 rounded-lg ${bgColor} flex items-center justify-center shrink-0`}>
          <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-1">
        <h3 className="text-2xl font-bold text-slate-900 tracking-tight">{value}</h3>
        {trend && (
          <span
            className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
              trendUp
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-rose-50 text-rose-700'
            }`}
          >
            {trend}
          </span>
        )}
      </div>

      {subtitle && <p className="text-[11px] text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
};
