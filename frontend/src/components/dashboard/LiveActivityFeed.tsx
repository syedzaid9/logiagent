import React from 'react';
import { Activity, CheckCircle, AlertTriangle, Truck, MapPin } from 'lucide-react';

interface ActivityItem {
  id: number;
  shipment_id: number;
  status: string;
  location: string;
  notes: string;
  time_ago: string;
}

interface LiveActivityFeedProps {
  activities: ActivityItem[];
  onInspectShipment?: (id: number) => void;
}

export const LiveActivityFeed: React.FC<LiveActivityFeedProps> = ({ activities, onInspectShipment }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Delayed':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
      case 'Delivered':
        return <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />;
      case 'In Transit':
        return <Truck className="w-3.5 h-3.5 text-blue-600" />;
      default:
        return <MapPin className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-bold text-slate-900">Recent Activity</h4>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 live-pulse"></span>
          Live feed
        </span>
      </div>

      <div className="space-y-3 overflow-y-auto max-h-56 pr-1">
        {activities.map((act) => (
          <div
            key={act.id}
            className="flex items-start gap-2.5 text-xs pb-2.5 border-b border-slate-100 last:border-0 last:pb-0"
          >
            <div className="mt-0.5 p-1 rounded-md bg-slate-50 border border-slate-200 shrink-0">
              {getStatusIcon(act.status)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-1">
                <span className="font-semibold text-slate-800 truncate">{act.location}</span>
                <span className="text-[10px] text-slate-400 shrink-0 font-mono">{act.time_ago}</span>
              </div>
              <p className="text-[11px] text-slate-500 truncate mt-0.5">{act.notes}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
