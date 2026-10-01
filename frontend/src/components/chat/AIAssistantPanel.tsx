import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { ChatMessage as ChatMessageType } from '../../types';
import { api } from '../../api/services';
import { ChatMessage } from './ChatMessage';
import { QuickPrompts } from './QuickPrompts';
import { 
  Send, 
  Boxes, 
  Trash2, 
  Sparkles, 
  Loader2, 
  PlusCircle, 
  MessageSquare,
  ShieldCheck,
  Bot
} from 'lucide-react';

interface AIAssistantPanelProps {
  onNavigateTab?: (tab: string) => void;
  initialQuery?: string | null;
  onClearInitialQuery?: () => void;
}

export const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({ 
  onNavigateTab,
  initialQuery,
  onClearInitialQuery 
}) => {
  const { role } = useAuth();
  const [conversationId, setConversationId] = useState<string>(`session-${Date.now()}`);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (initialQuery) {
      handleSendMessage(initialQuery);
      if (onClearInitialQuery) onClearInitialQuery();
    }
  }, [initialQuery]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputQuery.trim();
    if (!query || loading) return;

    const userMessage: ChatMessageType = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setLoading(true);

    try {
      const response = await api.chatWithAgent(query, role, conversationId);
      
      const agentMessage: ChatMessageType = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        text: response.response,
        actions_performed: response.actions_performed,
        tools_used: response.tools_used,
        tool_calls: response.tool_calls,
        structured_data: response.structured_data,
        sources: response.sources,
        latency_ms: response.latency_ms,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error: any) {
      console.error('Agent chat error:', error);
      const errorMessage: ChatMessageType = {
        id: `err-${Date.now()}`,
        sender: 'agent',
        text: 'Something went wrong while processing your logistics request. Please try again.',
        isError: true,
        queryForRetry: query,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleNewConversation = () => {
    setConversationId(`session-${Date.now()}`);
    setMessages([]);
    setInputQuery('');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
      {/* 1. Header Bar */}
      <div className="px-5 py-3.5 bg-white border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-2xs">
            <Boxes className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-sm text-slate-900">
                LogiAgent Operations Assistant
              </h2>
              <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                LangGraph 9-Tool Agent
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Active Operator: <strong className="text-slate-800 font-medium">{role}</strong> · Grounded by Supabase & pgvector
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleNewConversation}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100/80 border border-blue-200 text-blue-700 text-xs font-semibold transition-colors shadow-2xs"
            title="Start new conversation session"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Conversation</span>
          </button>

          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-400 hover:text-slate-700 transition-colors"
              title="Clear messages"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* 2. Messages Stream / Empty State */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3 bg-slate-50/50">
        {messages.length === 0 ? (
          /* Useful Empty State */
          <div className="max-w-2xl mx-auto my-8 space-y-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center mx-auto text-blue-600 shadow-2xs">
              <Sparkles className="w-6 h-6" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                Your logistics operations, in one conversation.
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                Ask about active shipments, vehicle capacity, driver schedules, cost estimates, route optimization, or company logistics SOP policies.
              </p>
            </div>

            {/* Empty State Suggested Prompts */}
            <div className="pt-2 text-left">
              <QuickPrompts
                onSelectPrompt={(query) => handleSendMessage(query)}
                disabled={loading}
                role={role}
              />
            </div>
          </div>
        ) : (
          /* Render Active Message History */
          <>
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onRetry={(q) => handleSendMessage(q)}
                onNavigateTab={onNavigateTab}
              />
            ))}
          </>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex gap-3 my-4 justify-start">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-2xs mt-0.5">
              <Boxes className="w-4 h-4" />
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs max-w-[70%] space-y-2">
              <div className="flex items-center gap-2 text-blue-700 text-xs font-semibold">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>LogiAgent is analyzing operational telemetry...</span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-500 font-medium">
                <span className="w-2 h-2 rounded-full bg-blue-500 live-pulse"></span>
                <span>Selecting tools · Querying PostgreSQL database & vector store</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 3. Input Form & Quick Prompt Bar */}
      <div className="p-3.5 sm:p-4 bg-white border-t border-slate-200 space-y-2">
        {messages.length > 0 && (
          <div className="pb-1 overflow-x-auto">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 whitespace-nowrap">
              <span className="text-[11px] text-slate-400 font-medium shrink-0">Quick Prompts:</span>
              {(role?.toUpperCase().replace(' ', '_') === 'DRIVER'
                ? [
                    'Where is my next shipment?',
                    'What vehicle is assigned to me?',
                    'Calculate ETA for my shipment',
                    'Driver safety SOP'
                  ]
                : role?.toUpperCase().replace(' ', '_') === 'DISPATCHER'
                ? [
                    'Show delayed shipments',
                    'Which vehicles are available?',
                    'Show driver roster and HOS',
                    'Loading & detention policy'
                  ]
                : [
                    'How is our fleet performing this month?',
                    'Total transportation spend and cost/km',
                    'Show delayed and at-risk shipments',
                    'Cold chain temperature protocol'
                  ]
              ).map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(p)}
                  disabled={loading}
                  className="px-2.5 py-1 rounded-md bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-medium transition-colors disabled:opacity-50"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}


        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={`Ask about shipments, vehicles, routes, drivers, costs, delays, or logistics policies...`}
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-xs sm:text-sm text-slate-900 placeholder-slate-400 outline-none transition-all disabled:opacity-50 shadow-2xs"
          />

          <button
            type="submit"
            disabled={!inputQuery.trim() || loading}
            className="px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs sm:text-sm shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-1.5 shrink-0"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
