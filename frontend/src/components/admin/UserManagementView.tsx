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
  Copy,
  Check,
  UserX,
  UserCheck,
  FileCheck,
  ChevronRight,
  Truck,
  Mail,
  Lock,
  Link,
  Info,
  Key,
  ShieldAlert,
  ExternalLink
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
  const [provisionRole, setProvisionRole] = useState<'Logistics Manager' | 'Dispatcher' | 'Driver' | 'Fleet Manager'>('Driver');
  const [provisionDriverId, setProvisionDriverId] = useState<number | undefined>(undefined);
  const [requireApprovalCheck, setRequireApprovalCheck] = useState(false);
  const [provisionResult, setProvisionResult] = useState<any | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Approval Modal State
  const [selectedUserForApproval, setSelectedUserForApproval] = useState<User | null>(null);
  const [approvalNotes, setApprovalNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isApproving, setIsApproving] = useState(false);

  // Reissue Invitation Modal State
  const [showInvitationModal, setShowInvitationModal] = useState(false);
  const [selectedUserForInvitation, setSelectedUserForInvitation] = useState<User | null>(null);
  const [invitationResult, setInvitationResult] = useState<{
    activation_token: string;
    activation_expires_at?: string;
    development_invitation_url?: string;
    message: string;
  } | null>(null);
  const [isReissuing, setIsReissuing] = useState(false);
  const [copiedInvitationToken, setCopiedInvitationToken] = useState(false);
  const [copiedInvitationUrl, setCopiedInvitationUrl] = useState(false);

  // Link Driver Profile Modal State
  const [showLinkDriverModal, setShowLinkDriverModal] = useState(false);
  const [selectedUserForLinkDriver, setSelectedUserForLinkDriver] = useState<User | null>(null);
  const [linkOption, setLinkOption] = useState<'existing' | 'auto_create'>('auto_create');
  const [linkExistingDriverId, setLinkExistingDriverId] = useState<number | undefined>(undefined);
  const [linkPhone, setLinkPhone] = useState('+1-555-0199');
  const [linkLicense, setLinkLicense] = useState('');
  const [isLinkingDriver, setIsLinkingDriver] = useState(false);

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
      const payload: any = {
        email: provisionEmail.trim(),
        full_name: provisionName.trim(),
        role: provisionRole,
        driver_id: provisionRole === 'Driver' ? provisionDriverId : undefined,
        require_approval: requireApprovalCheck,
      };

      const res = await api.provisionUser(payload);
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

  const handleReissueInvitation = async (userId: number) => {
    setIsReissuing(true);
    try {
      const res = await api.reissueInvitation(userId);
      setInvitationResult(res);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to reissue invitation.');
    } finally {
      setIsReissuing(false);
    }
  };

  const handleLinkDriver = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserForLinkDriver) return;
    setIsLinkingDriver(true);
    try {
      await api.linkDriverProfile(selectedUserForLinkDriver.id, {
        driver_id: linkOption === 'existing' ? linkExistingDriverId : undefined,
        auto_create: linkOption === 'auto_create',
        phone: linkPhone.trim(),
        license_number: linkLicense.trim() || undefined,
      });
      setShowLinkDriverModal(false);
      setSelectedUserForLinkDriver(null);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to link driver profile.');
    } finally {
      setIsLinkingDriver(false);
    }
  };

  const getFullInvitationUrl = (token: string) => {
    const origin = window.location.origin;
    return `${origin}/activate-account?token=${encodeURIComponent(token)}`;
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
            <h1 className="text-xl font-bold text-slate-900">User Accounts & RBAC Governance</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Role assignment, operational linking, approval hierarchy, invitation issuance & governance
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
                  {pUser.driver_code ? (
                    <div className="text-[11px] text-amber-800 font-medium mt-1 flex items-center gap-1">
                      <Truck className="h-3 w-3 text-amber-600" />
                      <span>Linked Profile: {pUser.driver_code}</span>
                    </div>
                  ) : pUser.role === 'Driver' ? (
                    <div className="text-[11px] text-rose-600 font-medium mt-1 flex items-center gap-1">
                      <ShieldAlert className="h-3 w-3 text-rose-500" />
                      <span>Profile: Will auto-link on approval</span>
                    </div>
                  ) : null}
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
            <option value="Pending_Activation">Pending Activation</option>
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
                <th className="py-3.5 px-4">Role</th>
                <th className="py-3.5 px-4">Account Status</th>
                <th className="py-3.5 px-4">Approval Status</th>
                <th className="py-3.5 px-4">Operational Profile</th>
                <th className="py-3.5 px-4">Authentication</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
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
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${
                          u.account_status === 'Active'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : u.account_status === 'Pending_Activation'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
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
                    <td className="py-3.5 px-4">
                      {u.driver_id ? (
                        <div className="flex items-center gap-1.5 text-amber-800 font-medium">
                          <Truck className="h-3.5 w-3.5 text-amber-600 flex-shrink-0" />
                          <span>{u.driver_code || `Driver #${u.driver_id}`}</span>
                          {u.assigned_vehicle_code && (
                            <span className="text-[10px] text-slate-500">({u.assigned_vehicle_code})</span>
                          )}
                        </div>
                      ) : u.role === 'Driver' ? (
                        <div className="flex items-center gap-1.5">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            Not Linked
                          </span>
                          <button
                            onClick={() => {
                              setSelectedUserForLinkDriver(u);
                              setLinkOption('auto_create');
                              setLinkExistingDriverId(undefined);
                              setShowLinkDriverModal(true);
                            }}
                            className="text-[10px] text-blue-600 hover:text-blue-800 underline font-semibold cursor-pointer"
                          >
                            Link Profile
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Operational Staff</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {u.has_usable_password ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3" />
                          Configured
                        </span>
                      ) : u.has_activation_token ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          <Mail className="h-3 w-3" />
                          Invitation Pending
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                          <Lock className="h-3 w-3" />
                          Not Configured
                        </span>
                      )}
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

                        {/* Reissue / Copy Invitation Token Button */}
                        <button
                          onClick={() => {
                            setSelectedUserForInvitation(u);
                            setInvitationResult(null);
                            setShowInvitationModal(true);
                            handleReissueInvitation(u.id);
                          }}
                          className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors cursor-pointer"
                          title="Reissue Account Invitation Link"
                        >
                          <Mail className="h-4 w-4" />
                        </button>

                        {/* Link Driver Profile Button (Driver Role) */}
                        {u.role === 'Driver' && (
                          <button
                            onClick={() => {
                              setSelectedUserForLinkDriver(u);
                              setLinkOption(u.driver_id ? 'existing' : 'auto_create');
                              setLinkExistingDriverId(u.driver_id || undefined);
                              setShowLinkDriverModal(true);
                            }}
                            className="p-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 transition-colors cursor-pointer"
                            title="Configure Driver Operational Profile"
                          >
                            <Truck className="h-4 w-4" />
                          </button>
                        )}

                        {/* Suspend / Activate Button */}
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
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl shadow-modal overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <UserPlus className="h-4 w-4 text-blue-600" />
                <span>Provision New User Account</span>
              </h3>
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
                    <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                          <Mail className="h-4 w-4 text-blue-600" />
                          <span>Development Invitation Link:</span>
                        </span>
                        <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold">
                          7-day validity
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          readOnly
                          value={getFullInvitationUrl(provisionResult.activation_token)}
                          className="w-full font-mono text-xs bg-white border border-blue-300 px-3 py-2 rounded-lg text-blue-900 font-semibold select-all"
                        />
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(getFullInvitationUrl(provisionResult.activation_token));
                            setCopiedUrl(true);
                            setTimeout(() => setCopiedUrl(false), 2000);
                          }}
                          className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer shrink-0"
                          title="Copy Full Activation URL"
                        >
                          {copiedUrl ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </button>
                      </div>

                      <div className="flex items-center justify-between pt-1 text-[11px] text-blue-700">
                        <span>Admins never set user passwords. The recipient creates their own password.</span>
                        <a
                          href={getFullInvitationUrl(provisionResult.activation_token)}
                          target="_blank"
                          rel="noreferrer"
                          className="font-semibold text-blue-800 hover:underline flex items-center gap-1"
                        >
                          <span>Open Link</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
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
                      placeholder="e.g. Rajesh Kumar"
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
                      placeholder="rajesh@logiagent.io"
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
                      <option value="Driver">Driver (Freight Operator)</option>
                      <option value="Dispatcher">Dispatcher (Load & Route Dispatch)</option>
                      <option value="Fleet Manager">Fleet Manager (Vehicles & Compliance)</option>
                      {currentUser?.role === 'Admin' && <option value="Logistics Manager">Logistics Manager</option>}
                    </select>
                  </div>

                  {provisionRole === 'Driver' && (
                    <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-3.5 space-y-2">
                      <label className="block text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                        <Truck className="h-3.5 w-3.5 text-amber-700" />
                        <span>Driver Operational Profile</span>
                      </label>
                      <select
                        value={provisionDriverId || ''}
                        onChange={(e) => setProvisionDriverId(e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full bg-white border border-amber-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                      >
                        <option value="">-- Automatically create new Driver operational profile --</option>
                        {drivers.map((d) => (
                          <option key={d.id} value={d.id}>
                            Link existing: {d.name} ({d.driver_code}) - {d.status}
                          </option>
                        ))}
                      </select>
                      <p className="text-[10px] text-amber-800">
                        Leaving this default creates a dedicated operational profile with license and telemetry linkage.
                      </p>
                    </div>
                  )}

                  <div className="p-3.5 rounded-xl bg-blue-50/60 border border-blue-100 flex items-start gap-2 text-xs text-blue-900">
                    <Info className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span>
                      An invitation token will be created. The user will establish their own secure password upon activation.
                    </span>
                  </div>

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
                      {isSubmitting ? 'Provisioning...' : 'Provision User & Generate Invitation'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Reissue Invitation Modal */}
      {showInvitationModal && selectedUserForInvitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl shadow-modal overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Mail className="h-4 w-4 text-blue-600" />
                <span>Account Invitation Link</span>
              </h3>
              <button
                onClick={() => { setShowInvitationModal(false); setSelectedUserForInvitation(null); }}
                className="text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <div>User: <span className="font-bold text-slate-900">{selectedUserForInvitation.full_name}</span></div>
                <div>Email: <span className="font-bold text-slate-900">{selectedUserForInvitation.email}</span></div>
                <div>Role: <span className="font-bold text-blue-700">{selectedUserForInvitation.role}</span></div>
              </div>

              {isReissuing ? (
                <div className="py-6 text-center text-xs text-slate-500">
                  <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <span>Generating fresh cryptographic invitation token...</span>
                </div>
              ) : invitationResult ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                        <Mail className="h-4 w-4 text-blue-600" />
                        <span>Development Invitation Link:</span>
                      </span>
                      <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold">
                        Expires in 7 days
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        readOnly
                        value={getFullInvitationUrl(invitationResult.activation_token)}
                        className="w-full font-mono text-xs bg-white border border-blue-300 px-3 py-2 rounded-lg text-blue-900 font-semibold select-all"
                      />
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(getFullInvitationUrl(invitationResult.activation_token));
                          setCopiedInvitationUrl(true);
                          setTimeout(() => setCopiedInvitationUrl(false), 2000);
                        }}
                        className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer shrink-0"
                        title="Copy Full Activation URL"
                      >
                        {copiedInvitationUrl ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                      </button>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-[11px] text-blue-700">
                      <span>Admins cannot view or set user passwords. User sets their own password.</span>
                      <a
                        href={getFullInvitationUrl(invitationResult.activation_token)}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-blue-800 hover:underline flex items-center gap-1"
                      >
                        <span>Open Activation Page</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                </div>
              ) : null}

              <button
                onClick={() => { setShowInvitationModal(false); setSelectedUserForInvitation(null); }}
                className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Link Driver Profile Modal */}
      {showLinkDriverModal && selectedUserForLinkDriver && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl shadow-modal overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Truck className="h-4 w-4 text-amber-600" />
                <span>Configure Driver Operational Profile</span>
              </h3>
              <button
                onClick={() => { setShowLinkDriverModal(false); setSelectedUserForLinkDriver(null); }}
                className="text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLinkDriver} className="p-6 space-y-4">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <div>User: <span className="font-bold text-slate-900">{selectedUserForLinkDriver.full_name}</span></div>
                <div>Email: <span className="font-bold text-slate-900">{selectedUserForLinkDriver.email}</span></div>
                <div>
                  Current Linkage:{' '}
                  <span className="font-bold text-amber-700">
                    {selectedUserForLinkDriver.driver_code ? `${selectedUserForLinkDriver.driver_code}` : 'None'}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Profile Linkage Option
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setLinkOption('auto_create')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all cursor-pointer text-center ${
                      linkOption === 'auto_create'
                        ? 'bg-amber-600 text-white border-amber-600 shadow-2xs'
                        : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                    }`}
                  >
                    Auto-Create Profile
                  </button>
                  <button
                    type="button"
                    onClick={() => setLinkOption('existing')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all cursor-pointer text-center ${
                      linkOption === 'existing'
                        ? 'bg-amber-600 text-white border-amber-600 shadow-2xs'
                        : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
                    }`}
                  >
                    Link Existing Driver
                  </button>
                </div>
              </div>

              {linkOption === 'existing' ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Select Driver Entity
                  </label>
                  <select
                    value={linkExistingDriverId || ''}
                    onChange={(e) => setLinkExistingDriverId(e.target.value ? Number(e.target.value) : undefined)}
                    required
                    className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                  >
                    <option value="">-- Choose Existing Driver --</option>
                    {drivers.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.driver_code}) - {d.status}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Driver Phone
                    </label>
                    <input
                      type="text"
                      required
                      value={linkPhone}
                      onChange={(e) => setLinkPhone(e.target.value)}
                      placeholder="+1-555-0199"
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      CDL / Driver License Number (Optional)
                    </label>
                    <input
                      type="text"
                      value={linkLicense}
                      onChange={(e) => setLinkLicense(e.target.value)}
                      placeholder="DL-99281-TX"
                      className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
              )}

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => { setShowLinkDriverModal(false); setSelectedUserForLinkDriver(null); }}
                  className="flex-1 py-2 rounded-xl border border-slate-300 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLinkingDriver}
                  className="flex-2 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-xs font-semibold text-white shadow-2xs disabled:opacity-50 cursor-pointer"
                >
                  {isLinkingDriver ? 'Saving Link...' : 'Confirm Driver Linkage'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Approval Authorization Review Modal */}
      {selectedUserForApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl shadow-modal overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <FileCheck className="h-4 w-4 text-emerald-600" />
                <span>Authorize Account Provisioning</span>
              </h3>
              <button
                onClick={() => setSelectedUserForApproval(null)}
                className="text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <div>Candidate: <span className="font-bold text-slate-900">{selectedUserForApproval.full_name}</span></div>
                <div>Email: <span className="font-bold text-slate-900">{selectedUserForApproval.email}</span></div>
                <div>Requested Role: <span className="font-bold text-blue-700">{selectedUserForApproval.role}</span></div>
                <div>Status: <span className="font-semibold text-amber-700">{selectedUserForApproval.approval_status}</span></div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Authorization / Operational Notes (Optional)
                </label>
                <textarea
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  placeholder="e.g. Identity verified, commercial freight endorsement confirmed."
                  className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-blue-500 h-20"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  disabled={isApproving}
                  onClick={() => handleReject(selectedUserForApproval.id)}
                  className="flex-1 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold cursor-pointer disabled:opacity-50"
                >
                  Reject Account
                </button>
                <button
                  type="button"
                  disabled={isApproving}
                  onClick={() => handleApprove(selectedUserForApproval.id)}
                  className="flex-2 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  {isApproving ? 'Authorizing...' : 'Authorize & Issue Activation'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
