import React from 'react';
import { CheckCircle2, Wrench, Clock, Zap } from 'lucide-react';
import { ToolCallDetail } from '../../types';

interface ExecutionTraceProps {
  actions: string[];
  toolsUsed?: string[];
  toolCalls?: ToolCallDetail[];
  latencyMs?: number;
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({
  actions,
  toolsUsed = [],
  toolCalls = [],
  latencyMs,
}) => {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="my-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200/90 text-xs space-y-2">
      <div className="flex items-center justify-between pb-1.5 border-b border-slate-200">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800">
          <Zap className="w-3.5 h-3.5 text-blue-600" />
          <span>Operational Actions Performed</span>
        </div>
        {latencyMs !== undefined && (
          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-500">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>{latencyMs}ms</span>
          </div>
        )}
      </div>

      {/* Sequential Action Steps */}
      <div className="space-y-1">
        {actions.map((action, idx) => (
          <div key={idx} className="flex items-start gap-1.5 text-slate-700 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
            <span>{action}</span>
          </div>
        ))}
      </div>

      {/* Tools Called Badges */}
      {toolsUsed.length > 0 && (
        <div className="pt-1.5 border-t border-slate-200/70 flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Tools Executed:
          </span>
          {toolsUsed.map((tool, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700 font-mono text-[10px] shadow-2xs font-medium"
            >
              <Wrench className="w-2.5 h-2.5 text-slate-400" />
              {tool}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
