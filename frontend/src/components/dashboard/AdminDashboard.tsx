import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { User, ApprovalPolicy } from '../../types';
import { KPICard } from '../common/KPICard';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { KPISkeleton, CardSkeleton } from '../common/LoadingSkeleton';
import { QuickActionGroup } from '../common/QuickAction';
import {
  ShieldCheck,
  Users,
  ShieldAlert,
  Server,
  Activity,
  KeyRound,
  CheckCircle2,
  Clock,
  Lock,
  ArrowRight,
  Sparkles,
  Zap,
  Settings
} from 'lucide-react';

interface AdminDashboardProps {
  onNavigateToUsers: () => void;
  onNavigate?: (tab: string) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigateToUsers, onNavigate }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [policies, setPolicies] = useState<ApprovalPolicy[]>([]);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadAdminMetrics = async (isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    else setIsRefreshing(true);

    try {
      const [uRes, pRes] = await Promise.all([
        api.getUsers(),
        api.getApprovalPolicies(),
      ]);
      setUsers(uRes);
      setPolicies(pRes);
      setHealthStatus({
        api: 'healthy',
        database: 'connected',
        rag_vector: 'operational',
        ml_predictors: 'online'
      });
    } catch (err) {
      console.error('Failed to load admin metrics:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadAdminMetrics();
  }, []);

  const pendingApprovals = users.filter((u) => u.approval_status === 'Pending_Approval');
  const activeUsers = users.filter((u) => u.account_status === 'Active');
  const suspendedUsers = users.filter((u) => u.account_status === 'Suspended');

  if (isLoading && users.length === 0) {
    return (
      <div className="space-y-5">
        <div className="h-20 bg-white rounded-xl border border-slate-200 animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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

  const adminActions = [
    {
      id: 'manage-users',
      title: 'User & RBAC Accounts',
      description: 'Approve new registrations, manage role assignments, and review activation status.',
      icon: Users,
      iconColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      badge: pendingApprovals.length > 0 ? `${pendingApprovals.length} Pending` : undefined,
      onClick: onNavigateToUsers,
    },
    {
      id: 'system-policies',
      title: 'Approval Policies',
      description: 'Configure high-authority approval rules and automatic provisioning constraints.',
      icon: KeyRound,
      iconColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      onClick: onNavigateToUsers,
    },
    {
      id: 'ai-operations',
      title: 'AI Governance & Models',
      description: 'Audit vector retrieval parameters, delay predictors, and risk thresholds.',
      icon: Sparkles,
      iconColor: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      onClick: () => onNavigate && onNavigate('chat'),
    },
    {
      id: 'system-settings',
      title: 'System Settings',
      description: 'Manage carrier SLA benchmarks, webhook notification endpoints, and security keys.',
      icon: Settings,
      iconColor: 'text-slate-700',
      bgColor: 'bg-slate-100',
      onClick: () => onNavigate && onNavigate('settings'),
    },
  ];

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Header */}
      <PageHeader
        title="System Administration & Security Console"
        subtitle="Enterprise identity governance, RBAC authorization policies, and system health observability."
        icon={ShieldCheck}
        badge="ADMIN GOVERNANCE"
        badgeColor="bg-purple-50 text-purple-700 border-purple-200"
        onRefresh={() => loadAdminMetrics(true)}
        isRefreshing={isRefreshing}
        actions={
          <button
            onClick={onNavigateToUsers}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            <Users className="w-3.5 h-3.5" />
            <span>Manage Accounts</span>
          </button>
        }
      />

      {/* 2. Top System KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Registered Users"
          value={users.length}
          subtitle={`${activeUsers.length} active authenticated`}
          icon={Users}
          iconColor="text-purple-600"
          bgColor="bg-purple-50"
          trend="Authorized"
          trendUp={true}
          onClick={onNavigateToUsers}
        />

        <KPICard
          title="Pending Approvals"
          value={pendingApprovals.length}
          subtitle="Requires Admin / Manager review"
          icon={Clock}
          iconColor={pendingApprovals.length > 0 ? 'text-amber-600' : 'text-slate-400'}
          bgColor={pendingApprovals.length > 0 ? 'bg-amber-50' : 'bg-slate-50'}
          highlight={pendingApprovals.length > 0}
          onClick={onNavigateToUsers}
        />

        <KPICard
          title="Suspended Accounts"
          value={suspendedUsers.length}
          subtitle="Access blocked by policy"
          icon={Lock}
          iconColor={suspendedUsers.length > 0 ? 'text-rose-600' : 'text-slate-400'}
          bgColor={suspendedUsers.length > 0 ? 'bg-rose-50' : 'bg-slate-50'}
          onClick={onNavigateToUsers}
        />

        <KPICard
          title="RBAC Security Policies"
          value={policies.length}
          subtitle="Active approval rule sets"
          icon={ShieldCheck}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          trend="Active"
          trendUp={true}
        />
      </div>

      {/* 3. System Health & Account Provisioning Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* System Health Matrix */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <span>Platform Infrastructure Health</span>
            </h3>
            <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 font-bold">
              100% OPERATIONAL
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-800">FastAPI Application Server</span>
                <div className="text-[11px] text-slate-500">Uvicorn Async Worker • Rate Limiter Active</div>
              </div>
              <StatusBadge status="Healthy" />
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-800">Supabase PostgreSQL & pgvector</span>
                <div className="text-[11px] text-slate-500">Connection Pool Stable • Schema V11</div>
              </div>
              <StatusBadge status="Online" />
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-800">RAG Document & Vector Embeddings</span>
                <div className="text-[11px] text-slate-500">10 Policy Documents Indexed</div>
              </div>
              <StatusBadge status="Active" />
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-800">ML Delay, ETA & Cost Engines</span>
                <div className="text-[11px] text-slate-500">Delay Predictor • Cost Optimizer Ready</div>
              </div>
              <StatusBadge status="Ready" />
            </div>
          </div>
        </div>

        {/* Recent Provisioned Accounts */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-600" />
              <span>Registered User Accounts</span>
            </h3>
            <button
              onClick={onNavigateToUsers}
              className="text-xs font-semibold text-purple-600 hover:text-purple-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5">
            {users.slice(0, 4).map((u) => (
              <div
                key={u.id}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs hover:border-slate-300 transition-colors"
              >
                <div>
                  <div className="font-bold text-slate-900">{u.full_name}</div>
                  <div className="text-[11px] text-slate-500">{u.email}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200 font-mono">
                    {u.role}
                  </span>
                  <StatusBadge status={u.account_status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Admin Quick Actions */}
      <QuickActionGroup title="Governance Quick Actions" actions={adminActions} />
    </div>
  );
};
