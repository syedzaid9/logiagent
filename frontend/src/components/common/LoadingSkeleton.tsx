import React from 'react';

export const KPISkeleton: React.FC = () => (
  <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs animate-pulse">
    <div className="flex justify-between items-center mb-3">
      <div className="h-3.5 bg-slate-200 rounded w-24" />
      <div className="h-8 w-8 bg-slate-100 rounded-lg" />
    </div>
    <div className="h-7 bg-slate-200 rounded w-16 mb-2" />
    <div className="h-3 bg-slate-100 rounded w-32" />
  </div>
);

export const TableRowSkeleton: React.FC<{ cols?: number }> = ({ cols = 5 }) => (
  <tr className="animate-pulse">
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i} className="py-3.5 px-4">
        <div className="h-3.5 bg-slate-200 rounded w-full max-w-[120px]" />
      </td>
    ))}
  </tr>
);

export const CardSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => (
  <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs animate-pulse space-y-4">
    <div className="flex justify-between items-center pb-3 border-b border-slate-100">
      <div className="h-4 bg-slate-200 rounded w-36" />
      <div className="h-4 bg-slate-100 rounded w-16" />
    </div>
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-12 bg-slate-50 border border-slate-100 rounded-lg p-3 flex justify-between items-center">
          <div className="space-y-1.5 w-1/2">
            <div className="h-3 bg-slate-200 rounded w-3/4" />
            <div className="h-2.5 bg-slate-100 rounded w-1/2" />
          </div>
          <div className="h-5 bg-slate-200 rounded w-16" />
        </div>
      ))}
    </div>
  </div>
);
