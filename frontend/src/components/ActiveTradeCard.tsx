import React, { useState, useEffect } from 'react';
import { ActiveTrade } from '../types';
import {
  Timer,
  ArrowUpRight,
  ArrowDownRight,
  DollarSign,
  Zap,
  TrendingUp,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
} from 'lucide-react';

interface ActiveTradeCardProps {
  trade: ActiveTrade | null;
  currentPrice: number | null;
  tradeDurationSeconds?: number;
  tradeAmountUsd?: number;
  onPlaceManualTrade?: (direction: 'CALL' | 'PUT', amount?: number, duration?: number) => Promise<boolean>;
  onDurationChange?: (seconds: number) => void;
  onAmountChange?: (amount: number) => void;
  autoTradeEnabled?: boolean;
}

const STAKE_PRESETS = [1, 5, 10, 25, 50, 100];
const DURATION_PRESETS = [
  { seconds: 60, label: '1m' },
  { seconds: 120, label: '2m' },
  { seconds: 180, label: '3m' },
  { seconds: 300, label: '5m' },
];

export const ActiveTradeCard: React.FC<ActiveTradeCardProps> = ({
  trade,
  currentPrice,
  tradeDurationSeconds = 60,
  tradeAmountUsd = 1.0,
  onPlaceManualTrade,
  onDurationChange,
  onAmountChange,
  autoTradeEnabled = true,
}) => {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(tradeDurationSeconds);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (!trade || trade.result !== 'PENDING') return;

    const calculateRemaining = () => {
      const entryTime = new Date(trade.entry_time).getTime();
      const elapsedSeconds = Math.floor((Date.now() - entryTime) / 1000);
      const remaining = Math.max(trade.duration_seconds - elapsedSeconds, 0);
      setSecondsRemaining(remaining);
    };

    calculateRemaining();
    const interval = setInterval(calculateRemaining, 500);
    return () => clearInterval(interval);
  }, [trade]);

  const handleManualOrder = async (direction: 'CALL' | 'PUT') => {
    if (!onPlaceManualTrade || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onPlaceManualTrade(direction, tradeAmountUsd, tradeDurationSeconds);
    } finally {
      setIsSubmitting(false);
    }
  };

  const payoutRate = 0.82;
  const potentialProfit = tradeAmountUsd * payoutRate;
  const potentialTotalReturn = tradeAmountUsd + potentialProfit;

  // Active Trade is Running: Render Active HUD
  if (trade && trade.result === 'PENDING') {
    const isCall = trade.direction === 'CALL';
    const isWinning =
      currentPrice !== null
        ? isCall
          ? currentPrice > trade.entry_price
          : currentPrice < trade.entry_price
        : false;

    const priceDelta = currentPrice !== null ? currentPrice - trade.entry_price : 0;
    const floatingProfit = isWinning
      ? trade.amount * (trade.payout_percentage || payoutRate)
      : -trade.amount;

    const totalDuration = trade.duration_seconds || 60;
    const progressPercent = Math.max(0, Math.min(100, ((totalDuration - secondsRemaining) / totalDuration) * 100));

    // SVG Circular Timer Ring
    const radius = 32;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (progressPercent / 100) * circumference;

    return (
      <div
        className={`rounded-3xl p-4 sm:p-5 shadow-2xl flex flex-col justify-between border transition-all duration-300 relative overflow-hidden ${
          isWinning
            ? 'bg-gradient-to-b from-[#0a1e17] via-[#0d1622] to-[#0a1e17] border-emerald-500/60 shadow-emerald-500/20 glow-emerald'
            : 'bg-gradient-to-b from-[#220d13] via-[#0d1622] to-[#220d13] border-rose-500/60 shadow-rose-500/20 glow-rose'
        }`}
      >
        {/* Top Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#1b273d]">
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black font-mono shadow-md ${
                isCall
                  ? 'bg-emerald-500 text-black shadow-emerald-500/30'
                  : 'bg-rose-500 text-white shadow-rose-500/30'
              }`}
            >
              {isCall ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
              <span>
                {trade.duration_seconds}S {trade.direction}
              </span>
            </span>
            <span className="text-xs font-bold text-white tracking-wide">Active Contract</span>
          </div>

          <span
            className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${
              isWinning
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}
          >
            {isWinning ? '✓ In The Money' : '✗ Out of The Money'}
          </span>
        </div>

        {/* Center: Live Circular Timer + Price Telemetry */}
        <div className="my-4 flex items-center justify-between gap-4">
          {/* Circular Countdown Ring */}
          <div className="relative flex items-center justify-center shrink-0">
            <svg width="78" height="78" className="transform -rotate-90">
              <circle
                cx="39"
                cy="39"
                r={radius}
                stroke="#1b253b"
                strokeWidth="5"
                fill="transparent"
              />
              <circle
                cx="39"
                cy="39"
                r={radius}
                stroke={isWinning ? '#10b981' : '#f43f5e'}
                strokeWidth="5"
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="progress-ring-circle"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-lg font-black font-mono text-white leading-none">
                {secondsRemaining}s
              </span>
              <span className="text-[9px] uppercase font-bold text-slate-400 mt-0.5">
                EXPIRY
              </span>
            </div>
          </div>

          {/* Live Floating P&L Counter */}
          <div className="flex-1 bg-[#090d16] p-3 rounded-2xl border border-[#1b253b] text-right">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Expected P&L (82%)
            </div>
            <div
              className={`text-xl sm:text-2xl font-black font-mono mt-0.5 ${
                isWinning ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isWinning ? `+$${floatingProfit.toFixed(2)}` : `-$${Math.abs(floatingProfit).toFixed(2)}`}
            </div>
            <div className="text-[10px] font-mono text-slate-400 mt-1">
              Delta:{' '}
              <span className={priceDelta >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                {priceDelta >= 0 ? '+' : ''}
                {priceDelta.toFixed(2)} USD
              </span>
            </div>
          </div>
        </div>

        {/* Entry vs Spot Price Tiles */}
        <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono mb-3">
          <div className="bg-[#121929] p-2 rounded-xl border border-[#1e2a42]">
            <div className="text-[9px] uppercase text-slate-400 font-semibold">Strike Price</div>
            <div className="text-white font-bold mt-0.5">${trade.entry_price.toFixed(2)}</div>
          </div>
          <div className="bg-[#121929] p-2 rounded-xl border border-[#1e2a42]">
            <div className="text-[9px] uppercase text-slate-400 font-semibold">Live Price</div>
            <div
              className={`font-bold mt-0.5 ${
                currentPrice ? (isWinning ? 'text-emerald-400' : 'text-rose-400') : 'text-white'
              }`}
            >
              {currentPrice ? `$${currentPrice.toFixed(2)}` : '—'}
            </div>
          </div>
        </div>

        {/* Footer Order Info */}
        <div className="text-[10px] text-slate-400 flex items-center justify-between border-t border-[#182236] pt-2 font-mono">
          <span>Order: #{trade.trade_id.slice(0, 8)}</span>
          <span>Stake: ${trade.amount.toFixed(2)}</span>
        </div>
      </div>
    );
  }

  // Idle: Instant 1-Click Order Execution Ticket
  return (
    <div className="bg-[#0e1320] border border-[#1b253b] rounded-3xl p-4 sm:p-5 shadow-2xl flex flex-col justify-between">
      {/* Title & Auto-Trading Status */}
      <div className="flex items-center justify-between pb-3 border-b border-[#182236] mb-3">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs sm:text-sm font-extrabold text-white tracking-wide">
            Instant 1-Click FTT Ticket
          </h3>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
          Auto 7/7: {autoTradeEnabled ? 'ACTIVE' : 'STANDBY'}
        </span>
      </div>

      {/* Stake & Potential Payout Preview */}
      <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-3 mb-3">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-slate-400 font-semibold">Order Stake:</span>
          <span className="text-white font-mono font-black text-sm">
            ${tradeAmountUsd.toFixed(2)}
          </span>
        </div>

        {/* Preset Amount Pills */}
        {onAmountChange && (
          <div className="grid grid-cols-6 gap-1 mb-2">
            {STAKE_PRESETS.map((stake) => (
              <button
                key={stake}
                type="button"
                onClick={() => onAmountChange(stake)}
                className={`text-[10px] font-bold py-1 rounded-lg border font-mono transition-all ${
                  tradeAmountUsd === stake
                    ? 'bg-amber-500 text-black border-amber-400 shadow-md shadow-amber-500/20'
                    : 'bg-[#121826] text-slate-300 border-[#1f2b42] hover:bg-[#182236]'
                }`}
              >
                ${stake}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-[#161f32]">
          <span className="text-slate-400">Potential Return (82%):</span>
          <span className="text-emerald-400 font-mono font-bold">
            +${potentialProfit.toFixed(2)} (${potentialTotalReturn.toFixed(2)})
          </span>
        </div>
      </div>

      {/* Contract Duration Selector */}
      {onDurationChange && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold mb-1">
            <span>Contract Duration:</span>
            <span className="text-amber-400 font-mono font-bold">
              {tradeDurationSeconds}s ({Math.floor(tradeDurationSeconds / 60)}m)
            </span>
          </div>
          <div className="grid grid-cols-4 gap-1.5">
            {DURATION_PRESETS.map((opt) => (
              <button
                key={opt.seconds}
                type="button"
                onClick={() => onDurationChange(opt.seconds)}
                className={`text-[11px] font-bold py-1 rounded-xl border font-mono transition-all ${
                  tradeDurationSeconds === opt.seconds
                    ? 'bg-amber-500 text-black border-amber-400 shadow-md shadow-amber-500/20'
                    : 'bg-[#121826] text-slate-300 border-[#1f2b42] hover:bg-[#182236]'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Fast Action Buttons: HIGHER / CALL ▲ & LOWER / PUT ▼ */}
      <div className="grid grid-cols-2 gap-3 mb-2">
        <button
          onClick={() => handleManualOrder('CALL')}
          disabled={isSubmitting}
          type="button"
          className="group relative overflow-hidden bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-black py-3 px-3 rounded-2xl shadow-lg shadow-emerald-600/30 transition-all duration-150 transform active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <ArrowUpRight className="w-5 h-5 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
          <div className="text-left leading-tight">
            <div className="text-xs uppercase tracking-wider font-extrabold">CALL</div>
            <div className="text-[10px] opacity-80 font-mono">HIGHER ▲</div>
          </div>
        </button>

        <button
          onClick={() => handleManualOrder('PUT')}
          disabled={isSubmitting}
          type="button"
          className="group relative overflow-hidden bg-gradient-to-r from-rose-600 to-red-500 hover:from-rose-500 hover:to-red-400 text-white font-black py-3 px-3 rounded-2xl shadow-lg shadow-rose-600/30 transition-all duration-150 transform active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <ArrowDownRight className="w-5 h-5 group-hover:translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
          <div className="text-left leading-tight">
            <div className="text-xs uppercase tracking-wider font-extrabold">PUT</div>
            <div className="text-[10px] opacity-80 font-mono">LOWER ▼</div>
          </div>
        </button>
      </div>

      <p className="text-[10px] text-slate-500 text-center">
        Unanimous consensus engine executes trades automatically, or click above for manual entry.
      </p>
    </div>
  );
};
