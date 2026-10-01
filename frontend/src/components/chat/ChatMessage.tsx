import React, { useState } from 'react';
import { ChatMessage as ChatMessageType } from '../../types';
import { Boxes, User, Copy, Check, RotateCcw, AlertTriangle } from 'lucide-react';
import { ExecutionTrace } from './ExecutionTrace';
import { ResultCardRenderer } from './ResultCardRenderer';

interface ChatMessageProps {
  message: ChatMessageType;
  onRetry?: (query: string) => void;
  onNavigateTab?: (tab: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onRetry,
  onNavigateTab 
}) => {
  const isUser = message.sender === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper to format inline bold, code, and status badges
  const renderInlineText = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const inner = part.slice(2, -2);
        return <strong key={i} className="font-semibold text-slate-900">{inner}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        const inner = part.slice(1, -1);
        return (
          <code key={i} className="font-mono text-[11px] bg-slate-100 text-slate-800 px-1 py-0.5 rounded border border-slate-200">
            {inner}
          </code>
        );
      }
      return part;
    });
  };

  // Render markdown tables
  const renderTable = (lines: string[], keyPrefix: string) => {
    if (lines.length < 2) return null;
    const headerLine = lines[0];
    const headerCols = headerLine.split('|').map(s => s.trim()).filter(Boolean);
    const bodyLines = lines.slice(2); // Skip header & separator

    return (
      <div key={keyPrefix} className="my-2.5 overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px]">
              {headerCols.map((col, idx) => (
                <th key={idx} className="py-2 px-3">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {bodyLines.map((rowLine, rIdx) => {
              const cells = rowLine.split('|').map(s => s.trim()).filter(Boolean);
              return (
                <tr key={rIdx} className="hover:bg-slate-50/50 transition-colors">
                  {cells.map((cell, cIdx) => (
                    <td key={cIdx} className="py-2 px-3 text-slate-700">
                      {cell === 'Delivered' ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">Delivered</span>
                      ) : cell.includes('Delayed') ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200">{cell}</span>
                      ) : cell === 'In Transit' ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">In Transit</span>
                      ) : cell === 'Available' ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">Available</span>
                      ) : (
                        renderInlineText(cell)
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  // Structured Markdown Parser
  const parseContent = (content: string) => {
    const rawLines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let tableBuffer: string[] = [];

    const flushTable = (index: number) => {
      if (tableBuffer.length > 0) {
        elements.push(renderTable(tableBuffer, `table-${index}`));
        tableBuffer = [];
      }
    };

    rawLines.forEach((line, idx) => {
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        tableBuffer.push(line.trim());
        return;
      } else {
        flushTable(idx);
      }

      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={idx} className="text-sm font-bold text-slate-900 mt-2 mb-1 tracking-tight">
            {renderInlineText(line.replace('### ', ''))}
          </h3>
        );
      } else if (line.startsWith('#### ')) {
        elements.push(
          <h4 key={idx} className="text-xs font-semibold text-slate-800 mt-1.5 mb-0.5">
            {renderInlineText(line.replace('#### ', ''))}
          </h4>
        );
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        elements.push(
          <li key={idx} className="ml-4 list-disc text-xs text-slate-700 my-0.5 leading-relaxed">
            {renderInlineText(line.replace(/^[-*]\s+/, ''))}
          </li>
        );
      } else if (/^\d+\.\s+/.test(line)) {
        elements.push(
          <li key={idx} className="ml-4 list-decimal text-xs text-slate-700 my-0.5 leading-relaxed">
            {renderInlineText(line.replace(/^\d+\.\s+/, ''))}
          </li>
        );
      } else if (line.trim().length > 0) {
        elements.push(
          <p key={idx} className="text-xs text-slate-700 leading-relaxed my-1">
            {renderInlineText(line)}
          </p>
        );
      }
    });

    flushTable(rawLines.length);
    return elements;
  };

  return (
    <div className={`flex gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-2xs mt-0.5">
          <Boxes className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-[85%] sm:max-w-[78%] rounded-xl transition-all ${
        isUser
          ? 'bg-blue-600 text-white p-3.5 shadow-2xs'
          : 'bg-white border border-slate-200/90 text-slate-900 p-4 sm:p-5 shadow-2xs'
      }`}>
        <div className="flex items-center justify-between gap-4 mb-1.5 pb-1 border-b border-black/5">
          <span className={`text-[11px] font-semibold tracking-tight ${isUser ? 'text-blue-100' : 'text-slate-600'}`}>
            {isUser ? 'You' : 'LogiAgent Assistant'}
          </span>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono ${isUser ? 'text-blue-200' : 'text-slate-400'}`}>
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            {!isUser && (
              <button
                onClick={handleCopy}
                className="text-slate-400 hover:text-slate-700 transition-colors"
                title="Copy message"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            )}
          </div>
        </div>

        {/* Error State with Retry Button */}
        {message.isError ? (
          <div className="py-2 space-y-2 text-xs">
            <div className="flex items-center gap-2 text-rose-700 font-semibold">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>{message.text}</span>
            </div>
            {message.queryForRetry && onRetry && (
              <button
                onClick={() => onRetry(message.queryForRetry!)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 text-xs font-semibold transition-colors mt-1"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Retry Query</span>
              </button>
            )}
          </div>
        ) : (
          <>
            {/* Operational Execution Trace */}
            {!isUser && message.actions_performed && message.actions_performed.length > 0 && (
              <ExecutionTrace
                actions={message.actions_performed}
                toolsUsed={message.tools_used}
                toolCalls={message.tool_calls}
                latencyMs={message.latency_ms}
              />
            )}

            {/* Formatted Content */}
            <div className={`space-y-1 ${isUser ? 'text-white text-xs leading-relaxed' : ''}`}>
              {isUser ? message.text : parseContent(message.text)}
            </div>

            {/* Structured Cards & Grounded RAG Sources */}
            {!isUser && (
              <ResultCardRenderer
                structuredData={message.structured_data}
                sources={message.sources}
              />
            )}
          </>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-white shrink-0 shadow-2xs mt-0.5">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
