import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogIn, Truck, ShieldCheck, AlertTriangle, KeyRound, Sparkles, UserPlus, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { ActivateAccountModal } from './ActivateAccountModal';

const DEMO_ROLES = [
  { role: 'Admin', email: 'admin@logiagent.io', label: 'Admin', desc: 'Governance & All Access', color: 'blue' },
  { role: 'Logistics Manager', email: 'manager@logiagent.io', label: 'Manager', desc: 'Operations & Routes', color: 'blue' },
  { role: 'Dispatcher', email: 'dispatcher@logiagent.io', label: 'Dispatcher', desc: 'Schedules & Loads', color: 'emerald' },
  { role: 'Fleet Manager', email: 'fleet@logiagent.io', label: 'Fleet Mgr', desc: 'Vehicles & Compliance', color: 'sky' },
  { role: 'Driver', email: 'driver@logiagent.io', label: 'Driver', desc: 'Active Shipments', color: 'amber' },
  { role: 'Analyst', email: 'analyst@logiagent.io', label: 'Analyst', desc: 'KPIs & Cost Analytics', color: 'indigo' },
  { role: 'Operations Team', email: 'ops@logiagent.io', label: 'Ops Team', desc: 'Floor & Exceptions', color: 'slate' },
];

export const LoginView: React.FC = () => {
  const { login, register } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  
  // Form State
  const [email, setEmail] = useState('admin@logiagent.io');
  const [password, setPassword] = useState('LogiAgent2026!');
  const [fullName, setFullName] = useState('');
  const [selectedRole, setSelectedRole] = useState('Admin');
  const [showPassword, setShowPassword] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showActivateModal, setShowActivateModal] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    if (authMode === 'register' && !fullName.trim()) {
      setError('Please provide your full name.');
      return;
    }

    setIsLoading(true);
    try {
      if (authMode === 'login') {
        await login(email.trim(), password.trim());
      } else {
        await register({
          email: email.trim(),
          password: password.trim(),
          full_name: fullName.trim(),
          role: selectedRole,
        });
        setSuccessMsg('Registration completed successfully! Authenticating...');
      }
    } catch (err: any) {
      setError(err.message || (authMode === 'login' ? 'Authentication failed. Please check your credentials.' : 'Registration failed.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = async (fillEmail: string, autoSubmit = false) => {
    setAuthMode('login');
    setEmail(fillEmail);
    setPassword('LogiAgent2026!');
    setError(null);

    if (autoSubmit) {
      setIsLoading(true);
      try {
        await login(fillEmail, 'LogiAgent2026!');
      } catch (err: any) {
        setError(err.message || 'Authentication failed. Please verify the backend is running.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7F9] flex flex-col justify-center py-10 sm:px-6 lg:px-8 relative font-sans text-slate-850">
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center items-center gap-3 mb-2">
          <div className="h-12 w-12 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <Truck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-850">
              LogiAgent
            </h1>
            <span className="text-xs text-blue-600 font-semibold tracking-wider uppercase">AI Logistics Platform</span>
          </div>
        </div>
        <h2 className="mt-3 text-center text-xl font-bold text-slate-850">
          {authMode === 'login' ? 'Sign in to your operational account' : 'Create a new operator account'}
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500">
          Role-Based Access Control & Operations Governance
        </p>

        {/* Tab Switcher */}
        <div className="mt-4 flex p-1 bg-slate-200/70 rounded-xl max-w-xs mx-auto">
          <button
            type="button"
            onClick={() => { setAuthMode('login'); setError(null); }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              authMode === 'login' ? 'bg-white text-slate-850 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setAuthMode('register'); setError(null); }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              authMode === 'register' ? 'bg-white text-slate-850 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Register
          </button>
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
        <div className="bg-white py-7 px-6 shadow-card rounded-2xl border border-slate-200 sm:px-9">
          {error && (
            <div className="mb-5 rounded-xl bg-rose-50 border border-rose-200 p-3.5 flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-rose-800 leading-relaxed">{error}</div>
            </div>
          )}

          {successMsg && (
            <div className="mb-5 rounded-xl bg-emerald-50 border border-emerald-200 p-3.5 flex items-start gap-2.5">
              <ShieldCheck className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-emerald-800">{successMsg}</div>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            {authMode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Sarah Jenkins"
                  className="w-full rounded-lg bg-white border border-slate-300 px-3.5 py-2 text-xs text-slate-850 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Work Email or Role Username
              </label>
              <input
                type="text"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@logiagent.io or admin"
                className="w-full rounded-lg bg-white border border-slate-300 px-3.5 py-2 text-xs text-slate-850 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
            </div>

            {authMode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Operational Role
                </label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full rounded-lg bg-white border border-slate-300 px-3.5 py-2 text-xs text-slate-850 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all cursor-pointer"
                >
                  <option value="Admin">Admin (System Governance & Full Access)</option>
                  <option value="Logistics Manager">Logistics Manager (Operations Management)</option>
                  <option value="Dispatcher">Dispatcher (Load & Route Dispatch)</option>
                  <option value="Fleet Manager">Fleet Manager (Vehicles & Compliance)</option>
                  <option value="Driver">Driver (Commercial Freight Operator)</option>
                  <option value="Analyst">Analyst (Supply Chain & BI)</option>
                  <option value="Operations Team">Operations Team (Terminal Personnel)</option>
                </select>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Password
                </label>
                <span className="text-[10px] text-slate-400">
                  {authMode === 'login' ? 'Demo: LogiAgent2026! or admin123' : 'Min 3 chars'}
                </span>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-lg bg-white border border-slate-300 pl-3.5 pr-10 py-2 text-xs text-slate-850 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
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

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 flex items-center justify-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-all disabled:opacity-50 cursor-pointer"
            >
              {isLoading ? (
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : authMode === 'login' ? (
                <>
                  <LogIn className="h-4 w-4" />
                  <span>Authenticate & Enter System</span>
                </>
              ) : (
                <>
                  <UserPlus className="h-4 w-4" />
                  <span>Create Account & Start Session</span>
                </>
              )}
            </button>
          </form>

          {/* Account Invitation / Activation Option */}
          <div className="mt-4 pt-3 border-t border-slate-200 text-center">
            <button
              type="button"
              onClick={() => setShowActivateModal(true)}
              className="text-[11px] text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <KeyRound className="h-3.5 w-3.5" />
              <span>Received an account invitation? Activate with token</span>
            </button>
          </div>

          {/* Direct Operational Roles for Fast Demo Access */}
          <div className="mt-4 pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-blue-600" />
                <span>1-Click Demo Login Personas</span>
              </div>
              <span className="text-[10px] text-emerald-600 font-medium flex items-center gap-0.5">
                <CheckCircle2 className="h-2.5 w-2.5" />
                Auto-fills & logs in
              </span>
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {DEMO_ROLES.map((r) => (
                <button
                  key={r.email}
                  type="button"
                  disabled={isLoading}
                  onClick={() => handleQuickFill(r.email, true)}
                  className="text-left p-2 rounded-lg bg-slate-50 hover:bg-blue-50/70 border border-slate-200 hover:border-blue-300 text-[11px] transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <div className="font-semibold text-slate-800 group-hover:text-blue-700 flex items-center justify-between">
                    <span>{r.label}</span>
                    <LogIn className="w-3 h-3 text-slate-400 group-hover:text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="text-[9px] text-slate-500 truncate">{r.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          <span>FastAPI + SQLite/PostgreSQL Bearer JWT Authentication</span>
        </div>
      </div>

      {showActivateModal && (
        <ActivateAccountModal onClose={() => setShowActivateModal(false)} />
      )}
    </div>
  );
};
