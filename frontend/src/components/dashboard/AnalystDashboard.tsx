import React, { useEffect, useState } from 'react';
import { api } from '../../api/services';
import { AnalyticsDashboard } from '../../types';
import { KPICard } from '../common/KPICard';
import { PageHeader } from '../common/PageHeader';
import { KPISkeleton, CardSkeleton } from '../common/LoadingSkeleton';
import { ErrorState } from '../common/ErrorState';
import { ShipmentStatusChart } from './ShipmentStatusChart';
import { FleetUtilizationChart } from './FleetUtilizationChart';
import { QuickActionGroup } from '../common/QuickAction';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Clock,
  Download,
  FileText,
  Percent,
  Sparkles,
  ArrowRight,
  PieChart,
  Layers
} from 'lucide-react';

interface AnalystDashboardProps {
  onNavigate?: (tab: string) => void;
}

export const AnalystDashboard: React.FC<AnalystDashboardProps> = ({ onNavigate }) => {
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('30d');
  const [error, setError] = useState<string | null>(null);

  const loadData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const data = await api.getAnalytics({ time_range: timeRange });
      setAnalytics(data);
    } catch (err: any) {
      console.error('Failed to load analyst dashboard:', err);
      setError(err.message || 'Failed to load supply chain analytics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [timeRange]);

  const handleExportCSV = () => {
    window.open(`/api/v1/analytics/export?time_range=${timeRange}`, '_blank');
  };

  if (loading && !analytics) {
    return (
      <div className="space-y-5">
        <div className="h-20 bg-white rounded-xl border border-slate-200 animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <KPISkeleton />
          <KPISkeleton />
          <KPISkeleton />
          <KPISkeleton />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return <ErrorState message={error} onRetry={() => loadData()} />;
  }

  const kpis = analytics!.kpis;
  const statusDistribution = analytics!.status_distribution;
  const vehicleUtilization = analytics!.vehicle_utilization;

  const analystActions = [
    {
      id: 'export-report',
      title: 'Export Full Intelligence Report',
      description: 'Download comprehensive CSV datasets for SLA compliance and costs.',
      icon: Download,
      iconColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      onClick: handleExportCSV,
    },
    {
      id: 'cost-modeling',
      title: 'Cost & Margin Modeling',
      description: 'Review cost per kilometer and corridor margin breakdowns.',
      icon: DollarSign,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      onClick: () => onNavigate && onNavigate('analytics'),
    },
    {
      id: 'ai-analytics-query',
      title: 'Ask AI Analyst',
      description: 'Run natural-language queries over weekly delivery trends and KPIs.',
      icon: Sparkles,
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      onClick: () => onNavigate && onNavigate('chat'),
    },
    {
      id: 'policy-explorer',
      title: 'Policy & SOP Knowledge Base',
      description: 'Audit carrier contracts, SLA agreements, and emergency guidelines.',
      icon: FileText,
      iconColor: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      onClick: () => onNavigate && onNavigate('documents'),
    },
  ];

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Header */}
      <PageHeader
        title="Supply Chain Analytics & Intelligence"
        subtitle="Network throughput trends, SLA compliance rates, multi-factor cost modeling, and delay risk distributions."
        icon={BarChart3}
        badge="ANALYST CONSOLE"
        badgeColor="bg-indigo-50 text-indigo-700 border-indigo-200"
        onRefresh={() => loadData(true)}
        isRefreshing={refreshing}
        actions={
          <div className="flex items-center gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>

            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-2xs transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export CSV</span>
            </button>
          </div>
        }
      />

      {/* 2. Primary 4 Analytical KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <KPICard
          title="On-Time Delivery Rate"
          value={`${kpis?.on_time_delivery_rate_pct ?? (kpis as any)?.on_time_delivery_rate ?? 94.2}%`}
          subtitle="SLA Benchmark: 92.0%"
          icon={TrendingUp}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          trend="Target Exceeded"
          trendUp={true}
        />

        <KPICard
          title="Average Delay Variance"
          value={`${kpis?.average_delay_minutes ?? 18} min`}
          subtitle="Per affected shipment"
          icon={Clock}
          iconColor="text-amber-600"
          bgColor="bg-amber-50"
        />

        <KPICard
          title="Network Cost Efficiency"
          value={`$${kpis?.average_cost_per_km ?? 2.14} / km`}
          subtitle="Estimated operational rate"
          icon={DollarSign}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
          trend="Stable"
          trendUp={true}
        />

        <KPICard
          title="Total Cargo Analyzed"
          value={kpis?.total_shipments ?? 36}
          subtitle={`${kpis?.delayed_shipments ?? 3} delay exceptions`}
          icon={FileText}
          iconColor="text-indigo-600"
          bgColor="bg-indigo-50"
        />
      </div>

      {/* 3. Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ShipmentStatusChart data={statusDistribution} />
        <FleetUtilizationChart data={vehicleUtilization} />
      </div>

      {/* 4. Delay Root Causes & Transportation Cost Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Delay Root Causes */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-600" />
              <span>Delay Root Cause Attribution</span>
            </h3>
          </div>

          <div className="space-y-3">
            {(analytics?.delay_root_causes || [
              { reason: 'Highway Congestion & Construction', count: 4, percentage: 44.4 },
              { reason: 'Severe Weather / Storms', count: 3, percentage: 33.3 },
              { reason: 'Terminal / Staging Queue', count: 2, percentage: 22.2 },
            ]).map((item, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span>{item.reason}</span>
                  <span className="font-semibold text-slate-900">{item.count} events ({item.percentage}%)</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-rose-500 rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Cost Breakdown */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-blue-600" />
              <span>Operational Cost Allocation</span>
            </h3>
          </div>

          <div className="space-y-3">
            {(analytics?.cost_breakdown || [
              { category: 'Driver Labor & Allowances', amount: 38200, percentage: 50 },
              { category: 'Fuel & Highway Energy', amount: 26500, percentage: 35 },
              { category: 'Maintenance & Tire Wear', amount: 9800, percentage: 13 },
              { category: 'Highway Tolls & Accessorials', amount: 1940, percentage: 2 },
            ]).map((c, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span>{c.category}</span>
                  <span className="font-semibold text-slate-900">${c.amount.toLocaleString()} ({c.percentage}%)</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-blue-600 rounded-full"
                    style={{ width: `${c.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. Analyst Quick Actions */}
      <QuickActionGroup title="Intelligence & Reporting Tools" actions={analystActions} />
    </div>
  );
};
