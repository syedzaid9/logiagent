import React from 'react';
import { Package, Truck, MapPin, AlertTriangle, BookOpen, Navigation, ArrowRight, DollarSign, FileText } from 'lucide-react';
import { RAGSource } from '../../types';

interface ResultCardRendererProps {
  structuredData?: Record<string, any>;
  sources?: RAGSource[];
  onInspectShipment?: (code: string) => void;
  onInspectRoute?: (code: string) => void;
}

export const ResultCardRenderer: React.FC<ResultCardRendererProps> = ({
  structuredData,
  sources = [],
  onInspectShipment,
  onInspectRoute,
}) => {
  if (!structuredData && sources.length === 0) return null;

  return (
    <div className="mt-3 space-y-3">
      {/* 1. Shipment Card Preview */}
      {structuredData?.shipment && structuredData.shipment.found && (
        <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-600" />
              <span className="font-bold text-sm text-slate-900 font-mono">
                {structuredData.shipment.shipment_code}
              </span>
            </div>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                structuredData.shipment.status === 'Delayed'
                  ? 'bg-amber-50 text-amber-800 border border-amber-200'
                  : structuredData.shipment.status === 'In Transit'
                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}
            >
              {structuredData.shipment.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mb-2.5">
            <div>
              <span className="text-[10px] text-slate-400 block font-medium">Origin</span>
              <span className="font-semibold text-slate-800">{structuredData.shipment.origin}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block font-medium">Destination</span>
              <span className="font-semibold text-slate-800">{structuredData.shipment.destination}</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] pt-2 border-t border-slate-100 text-slate-500">
            <span>Vehicle: <strong className="text-slate-800 font-mono">{structuredData.shipment.vehicle || '—'}</strong></span>
            <span>Driver: <strong className="text-slate-800">{structuredData.shipment.driver || '—'}</strong></span>
          </div>
        </div>
      )}

      {/* 2. Route Preview Widget */}
      {structuredData?.route && structuredData.route.success && (
        <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-blue-600 font-semibold text-xs">
              <Navigation className="w-3.5 h-3.5" />
              <span>Recommended Corridor: {structuredData.route.recommended_route?.corridor}</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono">
              {structuredData.route.recommended_route?.traffic_condition} Traffic
            </span>
          </div>

          <div className="flex items-center justify-between text-xs py-2 px-3 rounded-lg bg-slate-50 border border-slate-200 my-2">
            <div className="text-center">
              <span className="text-[10px] text-slate-400 block">Distance</span>
              <span className="font-bold text-slate-900 font-mono text-sm">
                {structuredData.route.recommended_route?.distance_km} km
              </span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            <div className="text-center">
              <span className="text-[10px] text-slate-400 block">Travel Time</span>
              <span className="font-bold text-blue-700 font-mono text-sm">
                {structuredData.route.recommended_route?.duration_formatted}
              </span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
            <div className="text-center">
              <span className="text-[10px] text-slate-400 block">Trip Cost</span>
              <span className="font-bold text-emerald-700 font-mono text-sm">
                ${structuredData.route.recommended_route?.estimated_cost_usd}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Grounded RAG Policy Sources */}
      {sources.length > 0 && (
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
          <div className="flex items-center gap-1.5 text-slate-800 font-semibold">
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            <span>Retrieved Policy & SOP Sources (pgvector Grounded)</span>
          </div>
          <div className="space-y-1.5">
            {sources.map((src, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs space-y-1">
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono font-bold text-blue-700 text-xs">
                      [{src.document_code}]
                    </span>
                    <span className="font-semibold text-slate-800 text-xs truncate max-w-[280px]">
                      {src.title}
                    </span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium shrink-0">
                    {src.category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 italic line-clamp-2 leading-relaxed">
                  "{src.snippet}"
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
