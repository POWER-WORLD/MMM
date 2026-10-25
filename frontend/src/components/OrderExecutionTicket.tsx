import React, { useState, useEffect } from 'react';
import { ActiveTrade, PerformanceStats } from '../types';
import {
  ArrowUpRight,
  ArrowDownRight,
  DollarSign,
  Zap,
  TrendingUp,
  ShieldCheck,
  Timer,
  Sliders,
  CheckCircle2,
  Clock,
} from 'lucide-react';

interface OrderExecutionTicketProps {
  trade: ActiveTrade | null;
  currentPrice: number | null;
  tradeDurationSeconds: number;
  tradeAmountUsd: number;
  onPlaceManualTrade: (direction: 'CALL' | 'PUT', amount?: number, duration?: number) => Promise<boolean>;
  onDurationChange: (seconds: number) => void;
  onAmountChange: (amount: number) => void;
  autoTradeEnabled: boolean;
  onToggleAutoTrade: () => void;
  performance: PerformanceStats;
  onOpenBrokerConfig?: () => void;
}

const STAKE_PRESETS = [1, 5, 10, 25, 50, 100];
const DURATION_PRESETS = [
  { seconds: 60, label: '1m' },
  { seconds: 120, label: '2m' },
  { seconds: 180, label: '3m' },
  { seconds: 300, label: '5m' },
];

export const OrderExecutionTicket: React.FC<OrderExecutionTicketProps> = ({
  trade,
  currentPrice,
  tradeDurationSeconds = 60,
  tradeAmountUsd = 1.0,
  onPlaceManualTrade,
  onDurationChange,
  onAmountChange,
  autoTradeEnabled,
  onToggleAutoTrade,
  performance,
  onOpenBrokerConfig,
}) => {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(tradeDurationSeconds);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Active trade countdown
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

  const handleOrder = async (direction: 'CALL' | 'PUT') => {
    if (isSubmitting) return;
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
  const winRate = performance.success_rate > 1.0 ? performance.success_rate : performance.success_rate * 100;
  const isProfitable = performance.total_profit_loss >= 0;

  return (
    <aside className="w-full lg:w-[310px] xl:w-[330px] border-l border-[rgba(255,255,255,0.07)] bg-[#080c14] flex flex-col h-full overflow-y-auto select-none shrink-0 z-20">
      {/* Panel Header */}
      <div className="p-3 border-b border-[rgba(255,255,255,0.07)] flex items-center justify-between bg-[#0a0e18]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center text-emerald-400">
            <Zap className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-black text-white tracking-wide leading-tight">
              FTT Execution Desk
            </h3>
            <span className="text-[9px] text-slate-400 font-mono">Olymp Trade Demo Link</span>
          </div>
        </div>

        {/* Auto-Trade Switch */}
        <button
          type="button"
          onClick={onToggleAutoTrade}
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-mono font-bold transition-all ${
            autoTradeEnabled
              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
              : 'bg-white/5 border-white/10 text-slate-400'
          }`}
          title="Toggle automated execution when 7/7 unanimous consensus is reached"
        >
          <span className={`w-1.5 h-1.5 rounded-full ${autoTradeEnabled ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
          <span>Auto 7/7: {autoTradeEnabled ? 'ON' : 'OFF'}</span>
        </button>
      </div>

      <div className="p-3 space-y-3 flex-1 flex flex-col justify-between">
        {/* Active Trade Banner (Shown when trade is in progress) */}
        {trade && trade.result === 'PENDING' ? (
          <div
            className={`p-3.5 rounded-2xl border transition-all ${
              currentPrice !== null &&
              (trade.direction === 'CALL'
                ? currentPrice > trade.entry_price
                : currentPrice < trade.entry_price)
                ? 'bg-gradient-to-b from-emerald-950/40 to-[#0e1622] border-emerald-500/50 glow-emerald'
                : 'bg-gradient-to-b from-rose-950/40 to-[#0e1622] border-rose-500/50 glow-rose'
            }`}
          >
            {/* Live Header */}
            <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
              <span
                className={`flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-black font-mono ${
                  trade.direction === 'CALL'
                    ? 'bg-emerald-500 text-black'
                    : 'bg-rose-500 text-white'
                }`}
              >
                {trade.direction === 'CALL' ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                <span>{trade.duration_seconds}s {trade.direction}</span>
              </span>

              <div className="flex items-center gap-1 font-mono text-xs font-black text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-lg border border-amber-500/20">
                <Clock className="w-3 h-3 animate-spin" />
                <span>{secondsRemaining}s</span>
              </div>
            </div>

            {/* Price Delta & Floating P&L */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono my-2">
              <div className="bg-[#090d16] p-2 rounded-xl border border-white/5">
                <span className="text-[9px] uppercase text-slate-400 font-bold block">Strike</span>
                <span className="font-bold text-white">${trade.entry_price.toFixed(2)}</span>
              </div>
              <div className="bg-[#090d16] p-2 rounded-xl border border-white/5">
                <span className="text-[9px] uppercase text-slate-400 font-bold block">Current</span>
                <span className="font-bold text-white">
                  {currentPrice ? `$${currentPrice.toFixed(2)}` : '—'}
                </span>
              </div>
            </div>

            {/* Expected P&L */}
            <div className="bg-[#090d16] p-2 rounded-xl border border-white/5 text-center">
              <span className="text-[9px] uppercase text-slate-400 font-bold block">Expected P&L</span>
              <span
                className={`text-lg font-black font-mono ${
                  currentPrice !== null &&
                  (trade.direction === 'CALL'
                    ? currentPrice > trade.entry_price
                    : currentPrice < trade.entry_price)
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                }`}
              >
                {currentPrice !== null &&
                (trade.direction === 'CALL'
                  ? currentPrice > trade.entry_price
                  : currentPrice < trade.entry_price)
                  ? `+$${(trade.amount * payoutRate).toFixed(2)} (ITM)`
                  : `-$${trade.amount.toFixed(2)} (OTM)`}
              </span>
            </div>
          </div>
        ) : null}

        {/* 1-Click Order Form */}
        <div className="space-y-3">
          {/* Stake Input with Preset Chips */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                Order Stake
              </span>
              <span className="text-white font-mono font-black text-sm">
                ${tradeAmountUsd.toFixed(2)}
              </span>
            </div>

            <div className="grid grid-cols-6 gap-1 mb-2">
              {STAKE_PRESETS.map((stake) => (
                <button
                  key={stake}
                  type="button"
                  onClick={() => onAmountChange(stake)}
                  className={`text-[10px] font-bold py-1.5 rounded-lg border font-mono transition-all ${
                    tradeAmountUsd === stake
                      ? 'bg-amber-500 text-black border-amber-400 font-black shadow-md shadow-amber-500/20'
                      : 'bg-[#0f1422] text-slate-300 border-white/5 hover:border-white/10'
                  }`}
                >
                  ${stake}
                </button>
              ))}
            </div>
          </div>

          {/* Contract Duration Selector */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                Contract Duration
              </span>
              <span className="text-amber-400 font-mono font-bold text-xs">
                {tradeDurationSeconds}s ({Math.floor(tradeDurationSeconds / 60)}m)
              </span>
            </div>

            <div className="grid grid-cols-4 gap-1">
              {DURATION_PRESETS.map((opt) => (
                <button
                  key={opt.seconds}
                  type="button"
                  onClick={() => onDurationChange(opt.seconds)}
                  className={`text-xs font-bold py-1.5 rounded-xl border font-mono transition-all ${
                    tradeDurationSeconds === opt.seconds
                      ? 'bg-amber-500 text-black border-amber-400 font-black shadow-md shadow-amber-500/20'
                      : 'bg-[#0f1422] text-slate-300 border-white/5 hover:border-white/10'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Payout Calculation Preview Card */}
          <div className="bg-[#090d16] border border-white/5 rounded-2xl p-2.5 text-xs font-mono">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span>Payout Rate:</span>
              <span className="text-emerald-400 font-bold">82.00%</span>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-white/5 text-white">
              <span>Potential Return:</span>
              <span className="text-emerald-400 font-black">
                +${potentialProfit.toFixed(2)} (${potentialTotalReturn.toFixed(2)})
              </span>
            </div>
          </div>

          {/* 1-Click Fast Action Buttons: CALL ▲ & PUT ▼ */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              onClick={() => handleOrder('CALL')}
              disabled={isSubmitting}
              type="button"
              className="bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-black py-3.5 px-3 rounded-2xl shadow-lg shadow-emerald-600/25 transition-all transform active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2 group"
            >
              <ArrowUpRight className="w-5 h-5 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
              <div className="text-left leading-tight">
                <div className="text-xs uppercase tracking-wider font-extrabold">CALL</div>
                <div className="text-[10px] opacity-80 font-mono">HIGHER ▲</div>
              </div>
            </button>

            <button
              onClick={() => handleOrder('PUT')}
              disabled={isSubmitting}
              type="button"
              className="bg-gradient-to-r from-rose-600 to-red-500 hover:from-rose-500 hover:to-red-400 text-white font-black py-3.5 px-3 rounded-2xl shadow-lg shadow-rose-600/25 transition-all transform active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2 group"
            >
              <ArrowDownRight className="w-5 h-5 group-hover:translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
              <div className="text-left leading-tight">
                <div className="text-xs uppercase tracking-wider font-extrabold">PUT</div>
                <div className="text-[10px] opacity-80 font-mono">LOWER ▼</div>
              </div>
            </button>
          </div>
        </div>

        {/* Mini Performance Summary at Bottom */}
        <div className="bg-[#090d16] border border-white/5 rounded-2xl p-2.5 mt-auto">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase text-slate-400 mb-2">
            <span>Session Stats</span>
            <span className="text-amber-400 font-mono">Demo Record</span>
          </div>

          <div className="grid grid-cols-3 gap-1.5 text-center font-mono">
            <div className="bg-[#0e1422] p-1.5 rounded-xl border border-white/5">
              <span className="text-[8px] text-slate-500 block uppercase">Win Rate</span>
              <span className="text-xs font-black text-emerald-400">{winRate.toFixed(0)}%</span>
            </div>
            <div className="bg-[#0e1422] p-1.5 rounded-xl border border-white/5">
              <span className="text-[8px] text-slate-500 block uppercase">Trades</span>
              <span className="text-xs font-black text-white">{performance.total_trades}</span>
            </div>
            <div className="bg-[#0e1422] p-1.5 rounded-xl border border-white/5">
              <span className="text-[8px] text-slate-500 block uppercase">Net P&L</span>
              <span className={`text-xs font-black ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isProfitable ? '+' : ''}${performance.total_profit_loss.toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
