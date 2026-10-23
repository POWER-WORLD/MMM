import React from 'react';
import { Wifi, WifiOff, RefreshCw, Timer, DollarSign, SlidersHorizontal } from 'lucide-react';

interface HeaderProps {
  currentPrice: number | null;
  previousPrice: number | null;
  priceFlash: 'up' | 'down' | null;
  isConnected: boolean;
  onRefresh: () => void;
  balance: number;
  tradeDurationSeconds: number;
  onDurationChange: (seconds: number) => void;
  tradeAmountUsd: number;
  onAmountChange: (amount: number) => void;
  onOpenBrokerConfig?: () => void;
}

const DURATION_OPTIONS = [
  { seconds: 60, label: '1m' },
  { seconds: 120, label: '2m' },
  { seconds: 180, label: '3m' },
  { seconds: 300, label: '5m' },
];

const STAKE_OPTIONS = [1, 5, 10, 25, 50];

export const Header: React.FC<HeaderProps> = ({
  currentPrice,
  previousPrice,
  priceFlash,
  isConnected,
  onRefresh,
  balance,
  tradeDurationSeconds,
  onDurationChange,
  tradeAmountUsd,
  onAmountChange,
  onOpenBrokerConfig,
}) => {
  const isUp = currentPrice && previousPrice ? currentPrice >= previousPrice : true;

  return (
    <header className="border-b border-[#1e2638] bg-[#0d121c]/95 backdrop-blur sticky top-0 z-50 px-2.5 sm:px-4 md:px-5 py-2">
      <div className="w-full flex flex-wrap items-center justify-between gap-2.5 sm:gap-4">
        {/* Brand & Market Asset */}
        <div className="flex items-center gap-2.5 sm:gap-3.5">
          <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20 text-black font-extrabold text-base sm:text-lg shrink-0">
            Au
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm sm:text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                Gold Trading Platform
                <span className="hidden xs:inline-block text-[9px] sm:text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  7 Agents
                </span>
              </h1>
            </div>
            <p className="text-[10px] sm:text-xs text-slate-400">
              Gold (XAU/USD) &bull; Fixed Time Trading (FTT)
            </p>
          </div>
        </div>

        {/* Live Gold Price Box */}
        <div className="bg-[#121826] border border-[#20293d] rounded-xl px-3 sm:px-4 py-1 flex items-center gap-2.5 sm:gap-3 shadow-inner">
          <div className="text-right">
            <div className="text-[9px] sm:text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center justify-end gap-1">
              <span>Gold Spot</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <div
              className={`text-lg sm:text-2xl font-bold font-mono tracking-tight transition-colors duration-200 ${
                priceFlash === 'up'
                  ? 'text-emerald-400'
                  : priceFlash === 'down'
                  ? 'text-rose-400'
                  : 'text-white'
              }`}
            >
              {currentPrice !== null && !isNaN(currentPrice)
                ? `$${currentPrice.toFixed(2)}`
                : 'Fetching...'}
            </div>
          </div>

          <div
            className={`w-6 h-6 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center font-bold text-[10px] sm:text-xs shrink-0 ${
              isUp
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {isUp ? '▲' : '▼'}
          </div>
        </div>

        {/* Fixed Time Duration & Stake Interactive Selectors */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Duration Selector */}
          <div className="flex items-center gap-1 bg-[#121826] border border-[#20293d] rounded-xl px-2 py-1">
            <div className="flex items-center gap-1 text-[10px] font-semibold text-slate-400 mr-1">
              <Timer className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Fixed Time:</span>
            </div>
            <div className="flex items-center gap-0.5">
              {DURATION_OPTIONS.map((opt) => {
                const isActive = tradeDurationSeconds === opt.seconds;
                return (
                  <button
                    key={opt.seconds}
                    type="button"
                    onClick={() => onDurationChange(opt.seconds)}
                    className={`text-[10px] sm:text-xs font-bold px-2 py-0.5 rounded-lg transition-all ${
                      isActive
                        ? 'bg-amber-500 text-black shadow-md shadow-amber-500/20'
                        : 'text-slate-400 hover:text-white hover:bg-[#1a2336]'
                    }`}
                    title={`Set trade expiration to ${opt.label} (${opt.seconds}s)`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Stake Selector */}
          <div className="flex items-center gap-1 bg-[#121826] border border-[#20293d] rounded-xl px-2 py-1">
            <div className="flex items-center gap-1 text-[10px] font-semibold text-slate-400 mr-1">
              <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Stake:</span>
            </div>
            <div className="flex items-center gap-0.5">
              {STAKE_OPTIONS.map((stake) => {
                const isActive = tradeAmountUsd === stake;
                return (
                  <button
                    key={stake}
                    type="button"
                    onClick={() => onAmountChange(stake)}
                    className={`text-[10px] sm:text-xs font-bold px-1.5 py-0.5 rounded-lg transition-all ${
                      isActive
                        ? 'bg-emerald-500 text-black shadow-md shadow-emerald-500/20'
                        : 'text-slate-400 hover:text-white hover:bg-[#1a2336]'
                    }`}
                    title={`Set trade stake to $${stake}`}
                  >
                    ${stake}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Demo Balance & Status */}
        <div className="flex items-center gap-2.5 sm:gap-3.5 ml-auto sm:ml-0">
          {/* Account Demo Balance */}
          <div className="bg-[#121826] border border-[#20293d] rounded-xl px-3 sm:px-4 py-1">
            <div className="text-[9px] sm:text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Olymp Demo
            </div>
            <div className="text-sm sm:text-xl font-bold font-mono text-amber-400">
              ${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          {/* Connection Status Badge */}
          <div
            className={`flex items-center gap-1.5 text-[11px] sm:text-xs px-2.5 py-1 rounded-full border ${
              isConnected
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-emerald-400 animate-pulse" />
                <Wifi className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                <span className="hidden md:inline">Live</span>
              </>
            ) : (
              <>
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-rose-400" />
                <WifiOff className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                <span className="hidden md:inline">Offline</span>
              </>
            )}
          </div>

          {/* Olymp Trade Config Button */}
          {onOpenBrokerConfig && (
            <button
              onClick={onOpenBrokerConfig}
              type="button"
              title="Configure Olymp Trade Demo Account"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 hover:text-amber-300 border border-amber-500/20 transition-colors text-xs font-semibold"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Broker API</span>
            </button>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            type="button"
            title="Refresh platform state"
            className="p-1.5 sm:p-2 rounded-lg bg-[#161c2b] hover:bg-[#1f283d] text-slate-400 hover:text-white border border-[#232c42] transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
