import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

export interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  bgColor?: string;
  trend?: string;
  trendUp?: boolean;
  badge?: string;
  highlight?: boolean;
  onClick?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-blue-600',
  bgColor = 'bg-blue-50',
  trend,
  trendUp,
  badge,
  highlight = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white border rounded-xl p-4 transition-all ${
        highlight
          ? 'border-amber-300 ring-1 ring-amber-200/80 shadow-xs'
          : 'border-slate-200/90 shadow-2xs hover:border-slate-300'
      } ${onClick ? 'cursor-pointer hover:shadow-xs' : ''}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 truncate">{title}</span>
        <div className={`p-2 rounded-lg ${bgColor} ${iconColor} shrink-0`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-2.5 flex items-baseline justify-between gap-2">
        <span className="text-2xl font-bold text-slate-900 tracking-tight">{value}</span>
        {badge && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {badge}
          </span>
        )}
      </div>

      {(subtitle || trend) && (
        <div className="mt-1.5 flex items-center justify-between text-[11px]">
          {subtitle && <span className="text-slate-500 truncate">{subtitle}</span>}
          {trend && (
            <span
              className={`inline-flex items-center gap-0.5 font-medium ml-auto shrink-0 ${
                trendUp === true
                  ? 'text-emerald-600'
                  : trendUp === false
                  ? 'text-rose-600'
                  : 'text-slate-500'
              }`}
            >
              {trendUp === true && <TrendingUp className="w-3 h-3" />}
              {trendUp === false && <TrendingDown className="w-3 h-3" />}
              {trend}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
