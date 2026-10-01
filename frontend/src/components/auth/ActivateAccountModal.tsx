import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { X, KeyRound, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';

interface ActivateAccountModalProps {
  initialToken?: string;
  onClose: () => void;
}

export const ActivateAccountModal: React.FC<ActivateAccountModalProps> = ({ initialToken = '', onClose }) => {
  const { login } = useAuth();
  const [token, setToken] = useState(initialToken);
  const [invitationInfo, setInvitationInfo] = useState<any | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifyingToken, setIsVerifyingToken] = useState(false);

  const fetchInvitation = async (tokenVal: string) => {
    if (!tokenVal.trim()) return;
    setIsVerifyingToken(true);
    setError(null);
    try {
      const info = await api.getInvitation(tokenVal.trim());
      setInvitationInfo(info);
      setFullName(info.full_name || '');
    } catch (err: any) {
      setError(err.message || 'Invalid or expired activation token.');
      setInvitationInfo(null);
    } finally {
      setIsVerifyingToken(false);
    }
  };

  useEffect(() => {
    if (initialToken) {
      fetchInvitation(initialToken);
    }
  }, [initialToken]);

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    fetchInvitation(token);
  };

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      await api.acceptInvitation(token.trim(), {
        full_name: fullName.trim(),
        password: password,
      });
      setSuccess(true);

      // Auto login
      setTimeout(async () => {
        try {
          await login(invitationInfo.email, password);
          onClose();
        } catch {
          // If auto login fails, user can log in manually
        }
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Account activation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl shadow-modal overflow-hidden relative">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <KeyRound className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-850">Activate LogiAgent Account</h3>
              <p className="text-xs text-slate-500">Complete invitation workflow & set initial password</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-5 rounded-xl bg-rose-50 border border-rose-200 p-3.5 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-rose-800">{error}</div>
            </div>
          )}

          {success ? (
            <div className="py-8 text-center space-y-3">
              <div className="h-14 w-14 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto border border-emerald-200">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h4 className="text-lg font-bold text-slate-850">Account Successfully Activated!</h4>
              <p className="text-xs text-slate-500">
                Your account is now active in Supabase. Authenticating and redirecting to your role dashboard...
              </p>
            </div>
          ) : !invitationInfo ? (
            /* Step 1: Input & Verify Token */
            <form onSubmit={handleVerify} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Activation Token
                </label>
                <input
                  type="text"
                  required
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste your secure activation token here..."
                  className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2.5 text-xs text-slate-850 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={isVerifyingToken || !token.trim()}
                className="w-full btn-primary py-2.5 cursor-pointer"
              >
                {isVerifyingToken ? (
                  <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <span>Verify Invitation Token</span>
                )}
              </button>
            </form>
          ) : (
            /* Step 2: Set Password & Activate */
            <form onSubmit={handleActivate} className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Target Email:</span>
                  <span className="text-xs font-semibold text-slate-850">{invitationInfo.email}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Assigned Role:</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                    {invitationInfo.role}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Approval Status:</span>
                  <span className="text-xs text-emerald-600 font-semibold">{invitationInfo.approval_status}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Confirm Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2 text-xs text-slate-850 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Set Password (Min 8 Characters)
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2 text-xs text-slate-850 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Confirm Password
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2 text-xs text-slate-850 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setInvitationInfo(null)}
                  className="flex-1 btn-secondary cursor-pointer"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-2 btn-primary py-2.5 cursor-pointer"
                >
                  {isLoading ? (
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <ShieldCheck className="h-4 w-4" />
                      <span>Set Password & Activate</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
