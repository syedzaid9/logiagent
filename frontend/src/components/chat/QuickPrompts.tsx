import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Package, 
  Truck, 
  AlertTriangle, 
  Route as RouteIcon, 
  BookOpen, 
  Users, 
  DollarSign, 
  BarChart2, 
  Clock, 
  ShieldCheck 
} from 'lucide-react';
import { api } from '../../api/services';
import { SuggestedPrompt } from '../../types';

interface QuickPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
  role?: string;
  customPrompts?: SuggestedPrompt[];
}

const getCategoryIcon = (category: string) => {
  const c = category.toLowerCase();
  if (c.includes('shipment') || c.includes('track')) return Package;
  if (c.includes('vehicle') || c.includes('fleet') || c.includes('truck')) return Truck;
  if (c.includes('route') || c.includes('corridor') || c.includes('navigation')) return RouteIcon;
  if (c.includes('eta') || c.includes('arrival') || c.includes('schedule')) return Clock;
  if (c.includes('sop') || c.includes('polic') || c.includes('compliance')) return BookOpen;
  if (c.includes('dispatch') || c.includes('driver')) return Users;
  if (c.includes('cost') || c.includes('financ') || c.includes('spend')) return DollarSign;
  if (c.includes('risk') || c.includes('delay') || c.includes('alert')) return AlertTriangle;
  if (c.includes('analytics') || c.includes('performance') || c.includes('kpi')) return BarChart2;
  return Sparkles;
};

export const QuickPrompts: React.FC<QuickPromptsProps> = ({ 
  onSelectPrompt, 
  disabled, 
  role,
  customPrompts 
}) => {
  const [prompts, setPrompts] = useState<SuggestedPrompt[]>(customPrompts || []);
  const [loading, setLoading] = useState(!customPrompts);

  useEffect(() => {
    if (customPrompts && customPrompts.length > 0) {
      setPrompts(customPrompts);
      setLoading(false);
      return;
    }

    let isMounted = true;
    api.getAgentCapabilities()
      .then((caps) => {
        if (isMounted && caps?.suggested_prompts) {
          setPrompts(caps.suggested_prompts);
        }
      })
      .catch((err) => {
        console.warn('Failed to load dynamic capabilities, using fallback prompt set', err);
        // Clean dynamic role fallback without hardcoded IDs
        const normRole = (role || '').toUpperCase().replace(' ', '_');
        if (normRole === 'DRIVER') {
          setPrompts([
            { label: 'Where is my next shipment?', query: 'Where is my next shipment and delivery schedule?', category: 'Shipments' },
            { label: 'What vehicle is assigned to me?', query: 'What vehicle is assigned to me?', category: 'Vehicle' },
            { label: 'What is my active route & ETA?', query: 'What is the optimal route for my active shipment?', category: 'Navigation' },
            { label: 'Driver safety & HOS rules', query: 'Show standard safety procedures and hours of service rules', category: 'SOP' },
          ]);
        } else if (normRole === 'DISPATCHER') {
          setPrompts([
            { label: 'Show delayed & at-risk shipments', query: 'Show all delayed and at-risk shipments requiring attention', category: 'Operations' },
            { label: 'Which vehicles are available?', query: 'Which vehicles are available for 2000 kg cargo payload?', category: 'Fleet' },
            { label: 'Show driver roster & HOS', query: 'Show available drivers and remaining hours of service', category: 'Dispatch' },
            { label: 'Fastest route for corridors', query: 'Calculate fastest route for primary highway corridors', category: 'Corridors' },
          ]);
        } else {
          setPrompts([
            { label: 'Fleet operational performance', query: 'How is our fleet performing this month?', category: 'Analytics' },
            { label: 'Total transportation spend', query: 'What is our total transportation spend and cost per km?', category: 'Financials' },
            { label: 'Delay root-cause analysis', query: 'What are the main causes of active shipment delays?', category: 'Performance' },
            { label: 'Fleet capacity utilization', query: 'Show fleet capacity utilization and available trucks', category: 'Capacity' },
          ]);
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [role, customPrompts]);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
        <Sparkles className="w-3.5 h-3.5 text-blue-600" />
        <span>Personalized {role ? `${role} ` : ''}Operational Suggestions</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {prompts.map((p, idx) => {
          const IconComp = getCategoryIcon(p.category);
          return (
            <button
              key={idx}
              disabled={disabled || loading}
              onClick={() => onSelectPrompt(p.query)}
              className="px-2.5 py-1.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 hover:text-blue-700 hover:border-blue-300 text-xs font-medium transition-all shadow-2xs disabled:opacity-50 disabled:cursor-not-allowed text-left flex items-center gap-1.5"
            >
              <IconComp className="w-3 h-3 text-slate-400 shrink-0" />
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

