import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: LucideIcon;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There are no active items matching your criteria at this time.',
  icon: Icon = Inbox,
  actionText,
  onAction,
}) => {
  return (
    <div className="py-12 px-4 text-center bg-white border border-slate-200/90 rounded-xl space-y-3">
      <div className="w-10 h-10 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center mx-auto text-slate-400">
        <Icon className="w-5 h-5" />
      </div>
      <div className="max-w-xs mx-auto">
        <h4 className="text-xs font-bold text-slate-800">{title}</h4>
        <p className="text-[11px] text-slate-500 mt-0.5">{description}</p>
      </div>
      {actionText && onAction && (
        <div className="pt-1">
          <button
            onClick={onAction}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            {actionText}
          </button>
        </div>
      )}
    </div>
  );
};
