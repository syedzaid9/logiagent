import React from 'react';
import { LucideIcon, ArrowRight } from 'lucide-react';

export interface QuickActionItem {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  iconColor?: string;
  bgColor?: string;
  onClick: () => void;
  badge?: string;
}

export interface QuickActionGroupProps {
  title?: string;
  actions: QuickActionItem[];
}

export const QuickActionGroup: React.FC<QuickActionGroupProps> = ({
  title = 'Quick Operations',
  actions,
}) => {
  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-3">
      {title && (
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">{title}</h3>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              onClick={action.onClick}
              className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-blue-50/60 border border-slate-200/80 hover:border-blue-200 transition-all text-left cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${action.bgColor || 'bg-white'} ${action.iconColor || 'text-blue-600'} border border-slate-200/60 group-hover:border-blue-200 shrink-0`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 group-hover:text-blue-700 flex items-center gap-1.5">
                    <span>{action.title}</span>
                    {action.badge && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded font-mono bg-blue-100 text-blue-800">
                        {action.badge}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{action.description}</div>
                </div>
              </div>

              <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
            </button>
          );
        })}
      </div>
    </div>
  );
};
