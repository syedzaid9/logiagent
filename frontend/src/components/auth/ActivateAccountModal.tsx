import React, { useState, useEffect } from 'react';
import { api } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { X, KeyRound, CheckCircle2, AlertCircle, ShieldCheck, Eye, EyeOff, UserCheck } from 'lucide-react';

interface ActivateAccountModalProps {
  initialToken?: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ActivateAccountModal: React.FC<ActivateAccountModalProps> = ({
  initialToken = '',
  onClose,
  onSuccess,
}) => {
  const { login } = useAuth();
  const [token, setToken] = useState(initialToken);
  const [invitationInfo, setInvitationInfo] = useState<{
    valid: boolean;
    email?: string;
    full_name?: string;
    role?: string;
    message?: string;
  } | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
      if (info.valid) {
        setInvitationInfo(info);
      } else {
        setError(info.message || 'Invalid or expired activation token.');
        setInvitationInfo(null);
      }
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
    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters long.');
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
        password: password.trim(),
        full_name: invitationInfo?.full_name,
      });
      setSuccess(true);

      // Automatic sign in after credential setup
      setTimeout(async () => {
        try {
          if (invitationInfo?.email) {
            await login(invitationInfo.email, password.trim());
          }
          if (onSuccess) onSuccess();
          onClose();
        } catch {
          if (onSuccess) onSuccess();
          onClose();
        }
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Account activation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl shadow-modal overflow-hidden relative">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <KeyRound className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Activate Account</h3>
              <p className="text-xs text-slate-500">Set your secure personal password to activate access</p>
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
            <div className="mb-5 rounded-xl bg-rose-50 border border-rose-200 p-3.5 flex items-start gap-3 text-xs text-rose-800">
              <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {success ? (
            <div className="py-8 text-center space-y-3">
              <div className="h-14 w-14 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto border border-emerald-200">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h4 className="text-lg font-bold text-slate-900">Account Successfully Activated!</h4>
              <p className="text-xs text-slate-500">
                Your credentials are now configured. Authenticating and logging into LogiAgent...
              </p>
            </div>
          ) : !invitationInfo ? (
            /* Step 1: Input & Verify Token */
            <form onSubmit={handleVerify} className="space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed">
                Paste your invitation token below to verify and establish your login password.
              </p>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Activation Token
                </label>
                <input
                  type="text"
                  required
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste your activation token..."
                  className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono transition-all"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2 rounded-xl border border-slate-300 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isVerifyingToken || !token.trim()}
                  className="flex-2 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-2xs cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {isVerifyingToken ? (
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <span>Verify Token</span>
                  )}
                </button>
              </div>
            </form>
          ) : (
            /* Step 2: Set Password & Activate */
            <form onSubmit={handleActivate} className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Email:</span>
                  <span className="font-bold text-slate-900">{invitationInfo.email}</span>
                </div>
                {invitationInfo.full_name && (
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Name:</span>
                    <span className="font-semibold text-slate-800">{invitationInfo.full_name}</span>
                  </div>
                )}
                {invitationInfo.role && (
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Assigned Role:</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      {invitationInfo.role}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  New Password (Min 6 Characters)
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2 pr-10 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full rounded-lg bg-white border border-slate-300 px-4 py-2 pr-10 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setInvitationInfo(null)}
                  className="flex-1 py-2 rounded-xl border border-slate-300 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-2 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-2xs cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5"
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
