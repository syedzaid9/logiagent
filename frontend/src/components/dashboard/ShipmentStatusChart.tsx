import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

interface StatusDistributionProps {
  data: { status: string; count: number; percentage: number }[];
}

const COLORS: Record<string, string> = {
  'In Transit': '#2563EB', // Blue
  'Delivered': '#10B981', // Emerald
  'Delayed': '#F59E0B', // Amber
  'Pending': '#94A3B8', // Slate
  'Assigned': '#6366F1', // Indigo
  'Picked Up': '#8B5CF6', // Purple
  'Failed': '#EF4444', // Red
};

export const ShipmentStatusChart: React.FC<StatusDistributionProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    name: d.status,
    value: d.count,
    color: COLORS[d.status] || '#64748B',
  }));

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl shadow-2xs p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-bold text-slate-900">Shipment Status Breakdown</h4>
        <span className="text-[11px] text-slate-400 font-medium">36 Total</span>
      </div>

      <div className="h-48 w-full my-1">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={72}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#FFFFFF" strokeWidth={2} />
              ))}
            </Pie>
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
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-3 border-t border-slate-100">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center gap-1.5 text-xs">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: COLORS[item.status] || '#64748B' }}
            ></span>
            <span className="text-slate-600 truncate">{item.status}:</span>
            <strong className="text-slate-900 font-medium">{item.count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
};
