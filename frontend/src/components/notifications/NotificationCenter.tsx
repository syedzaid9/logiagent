import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { NotificationItem, AlertItem } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { PageHeader } from '../common/PageHeader';
import { AlertBadge } from '../common/AlertBadge';
import { StatusBadge } from '../common/StatusBadge';
import { KPICard } from '../common/KPICard';
import { EmptyState } from '../common/EmptyState';
import { ErrorState } from '../common/ErrorState';
import { KPISkeleton } from '../common/LoadingSkeleton';
import {
  Bell,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Mail,
  MessageSquare,
  Radio,
  Filter,
  Check,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Layers
} from 'lucide-react';

export const NotificationCenter: React.FC = () => {
  const { setUnreadCount, role } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [aiAlerts, setAiAlerts] = useState<AlertItem[]>([]);
  const [activeTab, setActiveTab] = useState<'notifications' | 'ai_alerts'>('ai_alerts');
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState('All');
  const [error, setError] = useState<string | null>(null);

  const loadData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setIsRefreshing(true);
    setError(null);

    try {
      const [notifsData, alertsData] = await Promise.all([
        api.getNotifications().catch(() => []),
        api.getAiAlerts({ status: 'all', limit: 50 }).catch(() => []),
      ]);
      setNotifications(notifsData);
      setAiAlerts(alertsData);

      const unread = notifsData.filter((n) => n.status === 'unread').length;
      const activeAlertsCount = alertsData.filter((a) => a.status === 'active').length;
      setUnreadCount(unread + activeAlertsCount);
    } catch (err: any) {
      console.error('Error loading notifications/alerts:', err);
      setError(err.message || 'Failed to retrieve notification stream.');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await api.markNotificationAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'read' } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Error marking as read:', err);
    }
  };

  const handleAcknowledgeAlert = async (id: number) => {
    try {
      const updated = await api.acknowledgeAiAlert(id);
      setAiAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'acknowledged' } : a)));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolveAlert = async (id: number) => {
    try {
      const updated = await api.resolveAiAlert(id);
      setAiAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'resolved' } : a)));
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleTriggerScan = async () => {
    try {
      setIsRefreshing(true);
      await api.triggerAnomalyScan();
      await loadData(true);
    } catch (err) {
      console.error('Scan trigger failed:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'Email':
        return <Mail className="w-3.5 h-3.5 text-blue-600" />;
      case 'SMS':
        return <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />;
      case 'Push':
        return <Radio className="w-3.5 h-3.5 text-purple-600" />;
      default:
        return <Bell className="w-3.5 h-3.5 text-amber-600" />;
    }
  };

  const activeAlerts = aiAlerts.filter((a) => a.status === 'active');
  const criticalAlerts = aiAlerts.filter((a) => a.severity === 'CRITICAL' && a.status === 'active');

  const filteredNotifs = notifications.filter((n) => {
    if (filterSeverity === 'All') return true;
    return n.severity.toLowerCase() === filterSeverity.toLowerCase();
  });

  const filteredAlerts = aiAlerts.filter((a) => {
    if (filterSeverity === 'All') return true;
    return a.severity.toUpperCase() === filterSeverity.toUpperCase();
  });

  if (loading && notifications.length === 0 && aiAlerts.length === 0) {
    return (
      <div className="space-y-5">
        <div className="h-20 bg-white rounded-xl border border-slate-200 animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <KPISkeleton />
          <KPISkeleton />
          <KPISkeleton />
          <KPISkeleton />
        </div>
      </div>
    );
  }

  if (error && notifications.length === 0 && aiAlerts.length === 0) {
    return <ErrorState message={error} onRetry={() => loadData()} />;
  }

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* 1. Header */}
      <PageHeader
        title="Operational Alerts & Notification Center"
        subtitle="AI-detected network anomalies, dispatch notifications, and carrier SLA breach advisories."
        icon={Bell}
        badge="ALERT CENTER"
        badgeColor="bg-amber-50 text-amber-700 border-amber-200"
        onRefresh={() => loadData(true)}
        isRefreshing={isRefreshing}
        actions={
          ['Admin', 'Logistics Manager', 'Dispatcher', 'Operations Team'].includes(role) ? (
            <button
              onClick={handleTriggerScan}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Trigger AI Anomaly Scan</span>
            </button>
          ) : undefined
        }
      />

      {/* 2. Alert KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <KPICard
          title="Active AI Alerts"
          value={activeAlerts.length}
          subtitle="Requiring operator resolution"
          icon={AlertTriangle}
          iconColor={activeAlerts.length > 0 ? 'text-amber-600' : 'text-slate-400'}
          bgColor={activeAlerts.length > 0 ? 'bg-amber-50' : 'bg-slate-50'}
          highlight={activeAlerts.length > 0}
        />

        <KPICard
          title="Critical Severity"
          value={criticalAlerts.length}
          subtitle="Immediate action required"
          icon={ShieldAlert}
          iconColor={criticalAlerts.length > 0 ? 'text-rose-600' : 'text-slate-400'}
          bgColor={criticalAlerts.length > 0 ? 'bg-rose-50' : 'bg-slate-50'}
          highlight={criticalAlerts.length > 0}
        />

        <KPICard
          title="Total Event Stream"
          value={notifications.length}
          subtitle="Logged automated dispatches"
          icon={Bell}
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
        />

        <KPICard
          title="Resolved Anomalies"
          value={aiAlerts.filter((a) => a.status === 'resolved').length}
          subtitle="Mitigated and verified"
          icon={CheckCircle2}
          iconColor="text-emerald-600"
          bgColor="bg-emerald-50"
          trend="Audited"
          trendUp={true}
        />
      </div>

      {/* 3. Tab Switcher & Filter Bar */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg">
          <button
            onClick={() => setActiveTab('ai_alerts')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'ai_alerts'
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span>Operational AI Alerts</span>
            <span className="ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] bg-amber-100 text-amber-800">
              {activeAlerts.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('notifications')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'notifications'
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span>System Notifications</span>
            <span className="ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] bg-blue-100 text-blue-800">
              {notifications.length}
            </span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-500 font-medium">Severity:</span>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
          >
            <option value="All">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {/* 4. Content Area */}
      {activeTab === 'ai_alerts' ? (
        <div className="bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-2xs">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              AI Operational Alerts ({filteredAlerts.length})
            </h3>
            <span className="text-[11px] text-slate-500">Deduplicated anomaly pipeline</span>
          </div>

          <div className="divide-y divide-slate-100">
            {filteredAlerts.length === 0 ? (
              <div className="py-12">
                <EmptyState
                  title="No alerts in current view"
                  description="No active operational anomalies or alerts match your selected filters."
                  icon={ShieldAlert}
                />
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div key={alert.id} className="p-4 hover:bg-slate-50/70 transition-colors flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex items-center gap-2 flex-wrap">
                      <AlertBadge severity={alert.severity} />
                      <span className="font-bold text-slate-900 text-sm">{alert.title}</span>
                      <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">
                        {alert.entity_type.toUpperCase()}: {alert.entity_id}
                      </span>
                      <StatusBadge status={alert.status} />
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">{alert.message}</p>

                    {alert.recommended_action && (
                      <div className="text-[11px] text-amber-800 font-medium bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200/80 inline-block mt-1">
                        💡 <strong>Recommended Action:</strong> {alert.recommended_action}
                      </div>
                    )}

                    {alert.evidence && (
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        Evidence: {alert.evidence}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                    {alert.status === 'active' && (
                      <button
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                        className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                      >
                        Acknowledge
                      </button>
                    )}

                    {alert.status !== 'resolved' && (
                      <button
                        onClick={() => handleResolveAlert(alert.id)}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                      >
                        Resolve
                      </button>
                    )}

                    {alert.status === 'resolved' && (
                      <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Resolved</span>
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-2xs">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Automated Event Notifications ({filteredNotifs.length})
            </h3>
          </div>

          <div className="divide-y divide-slate-100">
            {filteredNotifs.length === 0 ? (
              <div className="py-12">
                <EmptyState
                  title="No notifications found"
                  description="Your automated dispatch event log is currently clear."
                  icon={Bell}
                />
              </div>
            ) : (
              filteredNotifs.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-4 hover:bg-slate-50/70 transition-colors flex items-start justify-between gap-4 text-xs ${
                    notif.status === 'unread' ? 'bg-blue-50/30' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 shrink-0 mt-0.5">
                      {getChannelIcon(notif.channel)}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-slate-900">{notif.title}</span>
                        <AlertBadge severity={notif.severity} />
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600">{notif.message}</p>
                      <div className="text-[10px] text-slate-500 font-medium">
                        Dispatched via {notif.channel} to {notif.recipient}
                      </div>
                    </div>
                  </div>

                  {notif.status === 'unread' && (
                    <button
                      onClick={() => handleMarkAsRead(notif.id)}
                      className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer shrink-0"
                    >
                      Mark Read
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
