import React, { useState } from 'react';
import { api } from '../../api/services';
import { X, Mail, CheckCircle2, AlertCircle, Copy, Check, ExternalLink, ShieldCheck } from 'lucide-react';

interface ForgotPasswordModalProps {
  onClose: () => void;
  onOpenResetWithToken?: (token: string) => void;
}

export const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({ onClose, onOpenResetWithToken }) => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
    reset_token?: string;
    reset_url?: string;
  } | null>(null);
  const [copiedUrl, setCopiedUrl] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setError(null);
    setIsLoading(true);
    try {
      const res = await api.forgotPassword(email.trim());
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Unable to process password reset request.');
    } finally {
      setIsLoading(false);
    }
  };

  const getFullResetUrl = (token: string) => {
    const origin = window.location.origin;
    return `${origin}/reset-password?token=${encodeURIComponent(token)}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl shadow-modal overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Reset Account Password</h3>
              <p className="text-[11px] text-slate-500">Self-service password recovery</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 rounded-xl bg-rose-50 border border-rose-200 p-3.5 flex items-start gap-2.5 text-xs text-rose-800">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {result ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
                <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-slate-900">Password Reset Requested</h4>
                <p className="text-xs text-emerald-800 mt-1">{result.message}</p>
              </div>

              {result.reset_token && (
                <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                      <Mail className="h-4 w-4 text-blue-600" />
                      <span>Development Reset Link:</span>
                    </span>
                    <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold">
                      24-hour validity
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={getFullResetUrl(result.reset_token)}
                      className="w-full font-mono text-xs bg-white border border-blue-300 px-3 py-1.5 rounded-lg text-blue-900 font-semibold select-all"
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(getFullResetUrl(result.reset_token!));
                        setCopiedUrl(true);
                        setTimeout(() => setCopiedUrl(false), 2000);
                      }}
                      className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer shrink-0"
                      title="Copy Reset URL"
                    >
                      {copiedUrl ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </button>
                  </div>

                  {onOpenResetWithToken && (
                    <button
                      type="button"
                      onClick={() => {
                        onOpenResetWithToken(result.reset_token!);
                      }}
                      className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <span>Proceed to Reset Password Page</span>
                      <ExternalLink className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              )}

              <button
                onClick={onClose}
                className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl cursor-pointer"
              >
                Close
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed">
                Enter your work email address. If an account is associated with this email, a secure single-use password reset link will be generated.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Work Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. rajesh@logiagent.io"
                  className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2 rounded-xl border border-slate-300 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-2 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-semibold text-white shadow-2xs disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5"
                >
                  {isLoading ? (
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <Mail className="h-4 w-4" />
                      <span>Generate Reset Link</span>
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
