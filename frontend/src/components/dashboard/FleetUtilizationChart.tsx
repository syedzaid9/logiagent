import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface FleetUtilizationProps {
  data: { vehicle_type: string; total_count: number; active_count: number; average_load_pct: number }[];
}

export const FleetUtilizationChart: React.FC<FleetUtilizationProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    name: d.vehicle_type.replace(' (Dry Van)', '').replace(' (Refrigerated)', ''),
    utilization: d.average_load_pct,
    active: d.active_count,
    total: d.total_count,
  }));

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-bold text-slate-900">Payload Utilization</h4>
        <span className="text-[11px] text-slate-400 font-medium">% Avg Capacity</span>
      </div>

      <div className="h-48 w-full my-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} tickLine={false} />
            <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} unit="%" domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderColor: '#E2E8F0',
                borderRadius: '8px',
                color: '#0F172A',
                fontSize: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              }}
            />
            <Bar dataKey="utilization" fill="#2563EB" radius={[4, 4, 0, 0]} name="Avg Load %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500">
        <span>Target: <strong className="text-slate-700">80% – 95%</strong></span>
        <span className="text-emerald-700 font-medium">Capacity Healthy</span>
      </div>
    </div>
  );
};
