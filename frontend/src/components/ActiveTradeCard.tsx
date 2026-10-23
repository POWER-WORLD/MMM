import React, { useState, useEffect } from 'react';
import { ActiveTrade } from '../types';
import { Timer, ArrowUpRight, ArrowDownRight, DollarSign } from 'lucide-react';

interface ActiveTradeCardProps {
  trade: ActiveTrade | null;
  currentPrice: number | null;
  tradeDurationSeconds?: number;
  tradeAmountUsd?: number;
}

export const ActiveTradeCard: React.FC<ActiveTradeCardProps> = ({
  trade,
  currentPrice,
  tradeDurationSeconds = 60,
  tradeAmountUsd = 1.0,
}) => {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(tradeDurationSeconds);

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

  const durationLabel =
    tradeDurationSeconds >= 60
      ? `${Math.floor(tradeDurationSeconds / 60)}m`
      : `${tradeDurationSeconds}s`;

  if (!trade) {
    return (
      <div className="bg-[#0f1422] border border-[#1e2638] rounded-2xl p-3.5 shadow-xl flex flex-col justify-between min-h-[190px]">
        <div className="flex items-center justify-between pb-2 border-b border-[#182030]">
          <div className="flex items-center gap-2">
            <Timer className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white">
              Live {durationLabel} Fixed Time Execution
            </h3>
          </div>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            Monitoring
          </span>
        </div>

        <div className="text-center py-2 text-slate-400">
          <div className="text-2xl mb-1">⏳</div>
          <div className="text-xs font-semibold text-slate-200">
            Scanning for 7/7 Agent Consensus
          </div>
          <p className="text-[11px] text-slate-400 mt-1 max-w-xs mx-auto">
            Trade will trigger automatically on Olymp Trade demo when all 7 technical agents agree with &ge;55% confidence.
          </p>
        </div>

        <div className="text-[11px] text-slate-400 border-t border-[#182030] pt-2 flex justify-between font-mono">
          <span>Active Stake: <strong className="text-white">${tradeAmountUsd.toFixed(2)}</strong></span>
          <span>Duration: <strong className="text-amber-400">{tradeDurationSeconds}s</strong></span>
          <span>Payout: <strong className="text-emerald-400">82%</strong></span>
        </div>
      </div>
    );
  }

  const isCall = trade.direction === 'CALL';
  const isWinning =
    currentPrice !== null
      ? isCall
        ? currentPrice > trade.entry_price
        : currentPrice < trade.entry_price
      : false;

  const floatingProfit = isWinning
    ? trade.amount * (trade.payout_percentage || 0.82)
    : -trade.amount;

  const activeDurationLabel =
    trade.duration_seconds >= 60
      ? `${Math.floor(trade.duration_seconds / 60)}M`
      : `${trade.duration_seconds}S`;

  return (
    <div
      className={`border rounded-2xl p-3.5 shadow-xl flex flex-col justify-between min-h-[190px] transition-all duration-300 ${
        isWinning
          ? 'bg-gradient-to-br from-[#0d1e19] to-[#0f1422] border-emerald-500/40 shadow-emerald-500/10'
          : 'bg-gradient-to-br from-[#1e1115] to-[#0f1422] border-rose-500/40 shadow-rose-500/10'
      }`}
    >
      <div className="flex items-center justify-between pb-2 border-b border-[#182030]">
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
              isCall ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
            }`}
          >
            {isCall ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
            <span>{activeDurationLabel} {trade.direction}</span>
          </div>
          <span className="text-xs font-semibold text-white">Active Order</span>
        </div>

        {/* Live Countdown */}
        <div className="flex items-center gap-1.5 text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
          <Timer className="w-3.5 h-3.5" />
          <span>{secondsRemaining}s</span>
        </div>
      </div>

      {/* Main Trade Metrics */}
      <div className="grid grid-cols-3 gap-2 my-2 text-center">
        <div className="bg-[#121826]/80 p-2 rounded-xl border border-[#1e2638]">
          <div className="text-[10px] uppercase text-slate-400 font-semibold">Entry Price</div>
          <div className="text-sm font-bold font-mono text-white mt-0.5">
            ${trade.entry_price.toFixed(2)}
          </div>
        </div>

        <div className="bg-[#121826]/80 p-2 rounded-xl border border-[#1e2638]">
          <div className="text-[10px] uppercase text-slate-400 font-semibold">Current Price</div>
          <div className="text-sm font-bold font-mono text-white mt-0.5">
            {currentPrice !== null ? `$${currentPrice.toFixed(2)}` : '—'}
          </div>
        </div>

        <div className="bg-[#121826]/80 p-2 rounded-xl border border-[#1e2638]">
          <div className="text-[10px] uppercase text-slate-400 font-semibold">Expected P&L</div>
          <div
            className={`text-sm font-bold font-mono mt-0.5 ${
              isWinning ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isWinning ? `+$${floatingProfit.toFixed(2)}` : `-$${Math.abs(floatingProfit).toFixed(2)}`}
          </div>
        </div>
      </div>

      <div className="text-[11px] text-slate-400 flex items-center justify-between border-t border-[#182030] pt-2">
        <span>Order ID: <span className="font-mono text-slate-300">{trade.trade_id.slice(0, 8)}</span></span>
        <span className={isWinning ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
          {isWinning ? '✓ Status: In The Money' : '✗ Status: Out of The Money'}
        </span>
      </div>
    </div>
  );
};
