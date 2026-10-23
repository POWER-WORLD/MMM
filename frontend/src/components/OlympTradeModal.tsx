import React, { useState } from 'react';
import { KeyRound, Shield, Check, ExternalLink, X } from 'lucide-react';

interface OlympTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OlympTradeModal: React.FC<OlympTradeModalProps> = ({ isOpen, onClose }) => {
  const [token, setToken] = useState<string>('');
  const [accountId, setAccountId] = useState<string>('');
  const [isSaved, setIsSaved] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem('olymptrade_token', token);
    localStorage.setItem('olymptrade_account_id', accountId);
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#101522] border border-[#20293d] rounded-2xl w-full max-w-md p-5 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center">
            <KeyRound className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Olymp Trade Account Config</h3>
            <p className="text-xs text-slate-400">Fixed Time Trading (FTT) Demo Sync</p>
          </div>
        </div>

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
              className="w-full bg-[#0a0d14] border border-[#1e2638] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-amber-500"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              Found in browser developer tools (Network tab &gt; Headers &gt; Authorization).
            </p>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Demo Account ID (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g., demo_12345678"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full bg-[#0a0d14] border border-[#1e2638] rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="bg-[#151c2d] border border-[#222d45] rounded-xl p-3 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 text-amber-400 font-semibold">
              <Shield className="w-3.5 h-3.5" />
              <span>Safety Guarantee</span>
            </div>
            <p>
              This platform defaults to the internal <strong>Demo Simulation Engine</strong> with exact 82% FTT payouts.
              Once your demo token is provided, orders can dispatch to your real Olymp Trade demo account.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2.5 mt-5">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-400 text-black flex items-center gap-1.5 transition-colors font-bold"
          >
            {isSaved ? (
              <>
                <Check className="w-4 h-4" />
                <span>Saved!</span>
              </>
            ) : (
              <span>Save & Connect</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
