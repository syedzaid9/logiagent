import React, { useState } from 'react';
import { NotificationItem } from '../../types';
import { 
  AlertTriangle, 
  AlertCircle, 
  Clock, 
  Check, 
  ChevronRight,
  CheckCircle2
} from 'lucide-react';

interface DashboardAlertsProps {
  notifications: NotificationItem[];
  loading: boolean;
  onMarkRead?: (id: number) => void;
  onNavigateToNotifications?: () => void;
}

export const DashboardAlerts: React.FC<DashboardAlertsProps> = ({
  notifications,
  loading,
  onMarkRead,
  onNavigateToNotifications,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  const filteredNotifications = notifications.filter((n) => {
    if (severityFilter === 'ALL') return true;
    return n.severity.toLowerCase() === severityFilter.toLowerCase();
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            Critical
          </span>
        );
      case 'high':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            Warning
          </span>
        );
      case 'medium':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
            <Clock className="w-3 h-3 text-blue-600" />
            Notice
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
            {severity}
          </span>
        );
    }
  };

  const getTypeLabel = (type: string) => {
    return type.replace('_', ' ').toLowerCase();
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs p-5 flex flex-col justify-between space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-slate-900">
              Operational Alerts
            </h3>
            <span className="text-[11px] px-2 py-0.2 rounded-full font-medium bg-rose-50 text-rose-700 border border-rose-200">
              {notifications.filter(n => n.status === 'unread').length} Unread
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time exception stream from SLA monitors & route telemetry.
          </p>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg self-start sm:self-auto">
          {['ALL', 'Critical', 'High', 'Medium'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSeverityFilter(lvl)}
              className={`px-2 py-0.5 rounded-md text-xs font-medium transition-all ${
                severityFilter === lvl
                  ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Alert Feed */}
      {loading ? (
        <div className="py-8 flex flex-col items-center justify-center space-y-2">
          <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-500">Loading alerts...</span>
        </div>
      ) : filteredNotifications.length === 0 ? (
        <div className="py-8 text-center bg-slate-50/50 rounded-lg border border-dashed border-slate-200">
          <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto mb-1 opacity-70" />
          <p className="text-xs font-semibold text-slate-700">No active alerts</p>
          <p className="text-[11px] text-slate-400">All corridors operating within normal parameters.</p>
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
          {filteredNotifications.map((notif) => (
            <div
              key={notif.id}
              className="p-3 rounded-lg border border-slate-200 bg-white hover:border-slate-300 transition-all space-y-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  {getSeverityBadge(notif.severity)}
                  <span className="text-[11px] text-slate-400 capitalize font-medium">
                    • {getTypeLabel(notif.notification_type)}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>

              <h4 className="text-xs font-semibold text-slate-900">{notif.title}</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                {notif.message}
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                <span>
                  Sent to: <span className="text-slate-600 font-medium">{notif.recipient}</span> ({notif.channel})
                </span>
                {onMarkRead && notif.status === 'unread' && (
                  <button
                    onClick={() => onMarkRead(notif.id)}
                    className="text-blue-600 hover:text-blue-700 flex items-center gap-1 font-semibold transition-colors"
                  >
                    <Check className="w-3 h-3" />
                    <span>Acknowledge</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>Delivery exceptions monitored 24/7</span>
        {onNavigateToNotifications && (
          <button
            onClick={onNavigateToNotifications}
            className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 transition-colors"
          >
            <span>All Notifications</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
