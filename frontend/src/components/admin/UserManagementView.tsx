import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { User, ApprovalPolicy, Driver } from '../../types';
import {
  Users,
  UserPlus,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  KeyRound,
  Copy,
  Check,
  UserX,
  UserCheck,
  FileCheck,
  ChevronRight,
  Truck
} from 'lucide-react';

export const UserManagementView: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [policies, setPolicies] = useState<ApprovalPolicy[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  // Provisioning Modal State
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [provisionEmail, setProvisionEmail] = useState('');
  const [provisionName, setProvisionName] = useState('');
  const [provisionRole, setProvisionRole] = useState<'Logistics Manager' | 'Dispatcher' | 'Driver'>('Driver');
  const [provisionDriverId, setProvisionDriverId] = useState<number | undefined>(undefined);
  const [requireApprovalCheck, setRequireApprovalCheck] = useState(false);
  const [provisionResult, setProvisionResult] = useState<any | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Approval Modal State
  const [selectedUserForApproval, setSelectedUserForApproval] = useState<User | null>(null);
  const [approvalNotes, setApprovalNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isApproving, setIsApproving] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [uRes, pRes, dRes] = await Promise.all([
        api.getUsers(),
        api.getApprovalPolicies(),
        api.getDrivers()
      ]);
      setUsers(uRes);
      setPolicies(pRes);
      setDrivers(dRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load user management data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api.provisionUser({
        email: provisionEmail.trim(),
        full_name: provisionName.trim(),
        role: provisionRole,
        driver_id: provisionRole === 'Driver' ? provisionDriverId : undefined,
        require_approval: requireApprovalCheck,
      });
      setProvisionResult(res);
      loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to provision user account.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async (userId: number) => {
    setIsApproving(true);
    try {
      await api.approveUser(userId, approvalNotes);
      setSelectedUserForApproval(null);
      setApprovalNotes('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to approve user.');
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async (userId: number) => {
    if (!rejectionReason.trim()) {
      alert('Please provide a reason for rejection.');
      return;
    }
    setIsApproving(true);
    try {
      await api.rejectUser(userId, rejectionReason);
      setSelectedUserForApproval(null);
      setRejectionReason('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to reject user.');
    } finally {
      setIsApproving(false);
    }
  };

  const handleSuspend = async (userId: number) => {
    if (!confirm('Are you sure you want to suspend this user account?')) return;
    try {
      await api.suspendUser(userId, 'Administrative action');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to suspend user.');
    }
  };

  const handleActivate = async (userId: number) => {
    try {
      await api.activateUser(userId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to activate user.');
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.driver_code && u.driver_code.toLowerCase().includes(search.toLowerCase()));

    const matchesRole = roleFilter === 'All' || u.role === roleFilter;
    const matchesStatus = statusFilter === 'All' || u.account_status === statusFilter || u.approval_status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  const pendingApprovals = users.filter((u) => u.approval_status === 'Pending_Approval');

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-card">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl border border-blue-200">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">User Accounts & RBAC Management</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Role assignment, operational linking, approval hierarchy & account provisioning
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            className="p-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs transition-colors cursor-pointer"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => {
              setProvisionResult(null);
              setProvisionEmail('');
              setProvisionName('');
              setProvisionDriverId(undefined);
              setShowProvisionModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-2xs transition-all cursor-pointer"
          >
            <UserPlus className="h-4 w-4" />
            <span>Provision Account</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-xs text-rose-800">
          <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Pending Approvals Queue Banner */}
      {pendingApprovals.length > 0 && (
        <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
              <Clock className="h-4 w-4 text-amber-600" />
              <span>Pending Authorization Queue ({pendingApprovals.length})</span>
            </div>
            <span className="text-[11px] text-amber-700 font-medium">Higher-authority approval required</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {pendingApprovals.map((pUser) => (
              <div key={pUser.id} className="bg-white border border-amber-200 rounded-xl p-3.5 flex flex-col justify-between shadow-2xs">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">{pUser.full_name}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      {pUser.role}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">{pUser.email}</div>
                  {pUser.driver_code && (
                    <div className="text-[11px] text-amber-800 font-medium mt-1 flex items-center gap-1">
                      <Truck className="h-3 w-3 text-amber-600" />
                      <span>Linked Profile: {pUser.driver_code}</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
                  <button
                    onClick={() => setSelectedUserForApproval(pUser)}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-1.5 px-3 rounded-lg transition-colors cursor-pointer shadow-2xs"
                  >
                    Review & Authorize
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-card">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, driver code..."
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 cursor-pointer shadow-2xs"
          >
            <option value="All">All Roles</option>
            <option value="Admin">Admin</option>
            <option value="Logistics Manager">Logistics Manager</option>
            <option value="Dispatcher">Dispatcher</option>
            <option value="Fleet Manager">Fleet Manager</option>
            <option value="Driver">Driver</option>
            <option value="Analyst">Analyst</option>
            <option value="Operations Team">Operations Team</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 cursor-pointer shadow-2xs"
          >
            <option value="All">All Statuses</option>
            <option value="Active">Active</option>
            <option value="Suspended">Suspended</option>
            <option value="Deactivated">Deactivated</option>
            <option value="Pending_Approval">Pending Approval</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3.5 px-4">User Details</th>
                <th className="py-3.5 px-4">Assigned Role</th>
                <th className="py-3.5 px-4">Operational Profile Link</th>
                <th className="py-3.5 px-4">Account Status</th>
                <th className="py-3.5 px-4">Approval Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                    No matching user accounts found.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900">{u.full_name}</div>
                      <div className="text-[11px] text-slate-500">{u.email}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                          u.role === 'Admin'
                            ? 'bg-purple-50 text-purple-700 border-purple-200'
                            : u.role === 'Logistics Manager'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : u.role === 'Dispatcher'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : u.role === 'Fleet Manager'
                            ? 'bg-sky-50 text-sky-700 border-sky-200'
                            : 'bg-amber-50 text-amber-800 border-amber-200'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {u.driver_id ? (
                        <div className="flex items-center gap-1.5 text-amber-800 font-medium">
                          <Truck className="h-3.5 w-3.5 text-amber-600" />
                          <span>{u.driver_code || `Driver #${u.driver_id}`}</span>
                          {u.assigned_vehicle_code && (
                            <span className="text-[10px] text-slate-500">({u.assigned_vehicle_code})</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Operational Staff</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                          u.account_status === 'Active'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : u.account_status === 'Suspended'
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}
                      >
                        {u.account_status || 'Active'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                          u.approval_status === 'Approved'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : u.approval_status === 'Pending_Approval'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                        }`}
                      >
                        {u.approval_status || 'Approved'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {u.approval_status === 'Pending_Approval' && (
                          <button
                            onClick={() => setSelectedUserForApproval(u)}
                            className="p-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 transition-colors cursor-pointer"
                            title="Review Approval"
                          >
                            <FileCheck className="h-4 w-4" />
                          </button>
                        )}
                        {u.account_status === 'Active' ? (
                          <button
                            onClick={() => handleSuspend(u.id)}
                            disabled={u.id === currentUser?.id}
                            className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-colors disabled:opacity-30 cursor-pointer"
                            title="Suspend Account"
                          >
                            <UserX className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleActivate(u.id)}
                            className="p-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition-colors cursor-pointer"
                            title="Activate Account"
                          >
                            <UserCheck className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Approval Policies Summary Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card">
        <h3 className="font-bold text-slate-900 text-sm mb-1 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-blue-600" />
          <span>Configurable Organization Approval Policies</span>
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Authority hierarchy and validation policies governing dynamic account provisioning
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {policies.map((pol) => (
            <div key={pol.id} className="bg-slate-50/80 border border-slate-200 rounded-xl p-3.5 shadow-2xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-slate-900 text-xs">{pol.role}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                    pol.requires_approval ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  }`}
                >
                  {pol.requires_approval ? 'Approval Required' : 'Auto-Approved'}
                </span>
              </div>
              <div className="text-[11px] text-slate-600 space-y-1">
                <div>Approver: <span className="text-slate-800 font-semibold">{pol.approver_role}</span></div>
                <div className="text-[10px] text-slate-500">{pol.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Provisioning Modal */}
      {showProvisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl shadow-modal overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm">Provision New User Account</h3>
              <button
                onClick={() => setShowProvisionModal(false)}
                className="text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-6">
              {provisionResult ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
                    <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
                    <h4 className="text-sm font-bold text-slate-900">Account Provisioned!</h4>
                    <p className="text-xs text-emerald-800 mt-1">{provisionResult.message}</p>
                  </div>

                  {provisionResult.activation_token && (
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                      <div className="text-xs font-medium text-slate-600">Secure Activation Token:</div>
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          readOnly
                          value={provisionResult.activation_token}
                          className="w-full font-mono text-xs bg-white border border-slate-300 px-3 py-1.5 rounded-lg text-blue-700 select-all"
                        />
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(provisionResult.activation_token);
                            setCopiedToken(true);
                            setTimeout(() => setCopiedToken(false), 2000);
                          }}
                          className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer"
                        >
                          {copiedToken ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => setShowProvisionModal(false)}
                    className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl cursor-pointer"
                  >
                    Close
                  </button>
                </div>
              ) : (
                <form onSubmit={handleProvision} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      required
                      value={provisionName}
                      onChange={(e) => setProvisionName(e.target.value)}
                      placeholder="e.g. Sarah Jenkins"
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={provisionEmail}
                      onChange={(e) => setProvisionEmail(e.target.value)}
                      placeholder="name@logiagent.io"
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Role
                    </label>
                    <select
                      value={provisionRole}
                      onChange={(e: any) => setProvisionRole(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 cursor-pointer"
                    >
                      <option value="Driver">Driver</option>
                      <option value="Dispatcher">Dispatcher</option>
                      <option value="Fleet Manager">Fleet Manager</option>
                      {currentUser?.role === 'Admin' && <option value="Logistics Manager">Logistics Manager</option>}
                    </select>
                  </div>

                  {provisionRole === 'Driver' && (
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                        Link Driver Operational Profile
                      </label>
                      <select
                        value={provisionDriverId || ''}
                        onChange={(e) => setProvisionDriverId(e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 cursor-pointer"
                      >
                        <option value="">-- Create new operational profile automatically --</option>
                        {drivers.map((d) => (
                          <option key={d.id} value={d.id}>
                            {d.name} ({d.driver_code}) - {d.status}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="checkbox"
                      id="requireAppr"
                      checked={requireApprovalCheck}
                      onChange={(e) => setRequireApprovalCheck(e.target.checked)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    />
                    <label htmlFor="requireAppr" className="text-xs text-slate-600 cursor-pointer">
                      Force higher-authority approval requirement
                    </label>
                  </div>

                  <div className="pt-2 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setShowProvisionModal(false)}
                      className="flex-1 py-2 rounded-xl border border-slate-300 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex-2 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-semibold text-white shadow-2xs disabled:opacity-50 cursor-pointer"
                    >
                      {isSubmitting ? 'Provisioning...' : 'Provision User'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Review Approval Modal */}
      {selectedUserForApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl shadow-modal p-6 space-y-4">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-amber-600" />
              <span>Review Account Authorization</span>
            </h3>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-xs text-slate-700">
              <div>Name: <span className="text-slate-900 font-bold">{selectedUserForApproval.full_name}</span></div>
              <div>Email: <span className="text-slate-900 font-bold">{selectedUserForApproval.email}</span></div>
              <div>Target Role: <span className="text-blue-700 font-bold">{selectedUserForApproval.role}</span></div>
              {selectedUserForApproval.driver_code && (
                <div>Linked Driver: <span className="text-amber-800 font-bold">{selectedUserForApproval.driver_code}</span></div>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Approval Notes (Optional)
              </label>
              <input
                type="text"
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="e.g. Identity verified by operations management"
                className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="pt-2 flex items-center gap-2">
              <button
                type="button"
                onClick={() => setSelectedUserForApproval(null)}
                className="flex-1 py-2 rounded-xl border border-slate-300 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                disabled={isApproving}
                onClick={() => handleApprove(selectedUserForApproval.id)}
                className="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold text-white shadow-2xs disabled:opacity-50 cursor-pointer"
              >
                {isApproving ? 'Authorizing...' : 'Approve & Activate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
