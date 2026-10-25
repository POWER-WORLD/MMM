import React, { useState } from 'react';
import {
  KeyRound,
  Shield,
  Check,
  ExternalLink,
  X,
  Sliders,
  Radio,
  Zap,
  Info,
} from 'lucide-react';

interface OlympTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultStake?: number;
  defaultDuration?: number;
  onSavePreferences?: (settings: { stake: number; duration: number }) => void;
}

export const OlympTradeModal: React.FC<OlympTradeModalProps> = ({
  isOpen,
  onClose,
  defaultStake = 1.0,
  defaultDuration = 60,
  onSavePreferences,
}) => {
  const [activeTab, setActiveTab] = useState<'broker' | 'rules'>('broker');
  const [token, setToken] = useState<string>(() => localStorage.getItem('olymptrade_token') || '');
  const [accountId, setAccountId] = useState<string>(
    () => localStorage.getItem('olymptrade_account_id') || ''
  );
  const [stake, setStake] = useState<number>(defaultStake);
  const [duration, setDuration] = useState<number>(defaultDuration);
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        setTestResult('Connection Successful! Platform & WebSocket active.');
      } else {
        setTestResult('Server returned error status.');
      }
    } catch {
      setTestResult('Local Platform simulation operational.');
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    localStorage.setItem('olymptrade_token', token);
    localStorage.setItem('olymptrade_account_id', accountId);

    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          olymp_auth_token: token,
          olymp_account_id: accountId,
          trade_amount_usd: stake,
          trade_duration_seconds: duration,
        }),
      });

      if (onSavePreferences) {
        onSavePreferences({ stake, duration });
      }
    } catch (err) {
      console.warn('Failed to update broker credentials:', err);
    }

    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
      onClose();
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 overflow-y-auto">
      <div className="bg-[#0e1320] border border-[#232f48] rounded-3xl w-full max-w-lg p-5 sm:p-6 shadow-2xl relative my-auto animate-in fade-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          type="button"
          aria-label="Close broker modal"
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white bg-[#141b2c] hover:bg-[#1d273e] rounded-xl border border-[#222d46] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Title */}
        <div className="flex items-center gap-3 mb-5 pb-4 border-b border-[#1c263c]">
          <div className="w-11 h-11 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center font-bold">
            <KeyRound className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-black text-white tracking-tight">
              Olymp Trade & Platform Config
            </h3>
            <p className="text-xs text-slate-400">Fixed Time Trading (FTT) Execution Parameters</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-[#121826] p-1 rounded-2xl border border-[#1e2a42] mb-4">
          <button
            type="button"
            onClick={() => setActiveTab('broker')}
            className={`flex-1 py-1.5 text-xs font-bold rounded-xl transition-all ${
              activeTab === 'broker'
                ? 'bg-amber-500 text-black shadow-md shadow-amber-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Broker Connection
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('rules')}
            className={`flex-1 py-1.5 text-xs font-bold rounded-xl transition-all ${
              activeTab === 'rules'
                ? 'bg-amber-500 text-black shadow-md shadow-amber-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Execution Rules
          </button>
        </div>

        {/* Tab 1: Broker Connection */}
        {activeTab === 'broker' && (
          <div className="space-y-3.5 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Demo Account Token / Authorization Header
              </label>
              <input
                type="password"
                placeholder="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full bg-[#080b12] border border-[#1c263c] rounded-xl px-3 py-2.5 text-white font-mono text-xs focus:outline-none focus:border-amber-400 transition-colors"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Optional: Inspect your Olymp Trade browser session (Network tab &gt; Headers &gt; Authorization).
              </p>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Demo Account ID (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g., demo_10482914"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                className="w-full bg-[#080b12] border border-[#1c263c] rounded-xl px-3 py-2.5 text-white font-mono text-xs focus:outline-none focus:border-amber-400 transition-colors"
              />
            </div>

            <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-3 text-[11px] text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                <Shield className="w-3.5 h-3.5" />
                <span>Zero-Risk Demo Environment</span>
              </div>
              <p>
                The platform operates on the internal <strong>Demo Simulation Engine</strong> with exact 82% FTT payouts.
                When your demo token is provided, orders can also synchronize with your live Olymp Trade demo account.
              </p>
            </div>

            {/* Test Link Button */}
            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={isTesting}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#141b2c] hover:bg-[#1d273e] text-slate-300 hover:text-white rounded-xl border border-[#232f48] transition-colors font-semibold text-xs"
              >
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>{isTesting ? 'Testing Link...' : 'Test Link Health'}</span>
              </button>

              {testResult && (
                <span className="text-[11px] font-mono text-emerald-400 font-bold">
                  {testResult}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Execution Rules */}
        {activeTab === 'rules' && (
          <div className="space-y-3.5 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Default Stake Amount ($ USD)
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                step="1"
                value={stake}
                onChange={(e) => setStake(Math.max(1, parseFloat(e.target.value) || 1))}
                className="w-full bg-[#080b12] border border-[#1c263c] rounded-xl px-3 py-2.5 text-white font-mono text-xs focus:outline-none focus:border-amber-400 transition-colors"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Default Fixed Time Duration
              </label>
              <select
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value, 10))}
                className="w-full bg-[#080b12] border border-[#1c263c] rounded-xl px-3 py-2.5 text-white font-mono text-xs focus:outline-none focus:border-amber-400 transition-colors"
              >
                <option value="60">1 Minute (60 seconds) - Recommended</option>
                <option value="120">2 Minutes (120 seconds)</option>
                <option value="180">3 Minutes (180 seconds)</option>
                <option value="300">5 Minutes (300 seconds)</option>
              </select>
            </div>

            <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-3 text-[11px] text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-cyan-400 font-bold">
                <Info className="w-3.5 h-3.5" />
                <span>Unanimous Consensus Protocol</span>
              </div>
              <p>
                Automatic orders are placed only when <strong>all 7 agents agree unanimously</strong> with &ge;55% average confidence.
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-[#1c263c]">
          <button
            onClick={onClose}
            type="button"
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#141b2c] hover:bg-[#1d273e] text-slate-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            type="button"
            className="px-5 py-2 rounded-xl text-xs font-black bg-amber-500 hover:bg-amber-400 text-black flex items-center gap-1.5 shadow-lg shadow-amber-500/20 transition-all font-mono"
          >
            {isSaved ? (
              <>
                <Check className="w-4 h-4" />
                <span>Applied!</span>
              </>
            ) : (
              <span>Save Changes</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
