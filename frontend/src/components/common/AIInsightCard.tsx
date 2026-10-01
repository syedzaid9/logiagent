import React from 'react';
import { Sparkles, Database, Brain, Lightbulb, HelpCircle, ArrowRight } from 'lucide-react';

export interface AIInsightItem {
  type: 'FACT' | 'PREDICTION' | 'RECOMMENDATION' | 'UNKNOWN';
  title: string;
  description: string;
  evidence?: string[];
  actionLabel?: string;
  onAction?: () => void;
  requiresConfirmation?: boolean;
}

export interface AIInsightCardProps {
  title?: string;
  insights: AIInsightItem[];
  compact?: boolean;
}

export const AIInsightCard: React.FC<AIInsightCardProps> = ({
  title = 'AI Operations Intelligence',
  insights,
  compact = false,
}) => {
  const getBadge = (type: AIInsightItem['type']) => {
    switch (type) {
      case 'FACT':
        return {
          label: 'DATABASE FACT',
          icon: Database,
          bg: 'bg-slate-100 text-slate-700 border-slate-200',
          dot: 'bg-slate-500',
        };
      case 'PREDICTION':
        return {
          label: 'ML PREDICTION',
          icon: Brain,
          bg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
          dot: 'bg-indigo-500',
        };
      case 'RECOMMENDATION':
        return {
          label: 'AI RECOMMENDATION',
          icon: Lightbulb,
          bg: 'bg-amber-50 text-amber-800 border-amber-200',
          dot: 'bg-amber-500',
        };
      case 'UNKNOWN':
      default:
        return {
          label: 'UNKNOWN / MISSING',
          icon: HelpCircle,
          bg: 'bg-slate-50 text-slate-500 border-slate-200',
          dot: 'bg-slate-400',
        };
    }
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100">
            <Sparkles className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">{title}</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-400 font-semibold uppercase">
          Live Model Grounded
        </span>
      </div>

      <div className="space-y-3">
        {insights.length === 0 ? (
          <p className="text-xs text-slate-400 py-3 text-center">No AI insights generated for current parameters.</p>
        ) : (
          insights.map((item, idx) => {
            const badge = getBadge(item.type);
            const Icon = badge.icon;
            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border text-xs transition-colors ${
                  item.type === 'RECOMMENDATION'
                    ? 'bg-amber-50/40 border-amber-200/80'
                    : item.type === 'PREDICTION'
                    ? 'bg-indigo-50/30 border-indigo-200/70'
                    : 'bg-slate-50 border-slate-200/80'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold border font-mono ${badge.bg}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                    <Icon className="w-3 h-3" />
                    <span>{badge.label}</span>
                  </span>

                  {item.requiresConfirmation && (
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded">
                      Confirmation Required
                    </span>
                  )}
                </div>

                <div className="font-semibold text-slate-900 mt-1">{item.title}</div>
                <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">{item.description}</p>

                {item.evidence && item.evidence.length > 0 && !compact && (
                  <div className="mt-2 pt-2 border-t border-slate-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Grounding Evidence:</span>
                    <ul className="list-disc list-inside text-[11px] text-slate-500 space-y-0.5">
                      {item.evidence.map((ev, eIdx) => (
                        <li key={eIdx}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {item.actionLabel && item.onAction && (
                  <div className="mt-3 pt-2 border-t border-slate-200/60 flex justify-end">
                    <button
                      onClick={item.onAction}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-semibold transition-colors cursor-pointer"
                    >
                      <span>{item.actionLabel}</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
