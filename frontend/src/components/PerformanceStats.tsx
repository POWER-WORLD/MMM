import React from 'react';
import { PerformanceStats as StatsType, ActiveTrade } from '../types';
import { Trophy, TrendingUp, TrendingDown, Target, Zap, DollarSign, Activity } from 'lucide-react';

interface PerformanceStatsProps {
  stats: StatsType;
  trades?: ActiveTrade[];
}

export const PerformanceStats: React.FC<PerformanceStatsProps> = ({ stats, trades = [] }) => {
  const winRate = stats.success_rate > 1.0 ? stats.success_rate : stats.success_rate * 100;
  const isProfitable = stats.total_profit_loss >= 0;

  // Generate lightweight points for Equity Curve from recent trades
  const balancePoints: number[] = [stats.initial_balance];
  if (trades.length > 0) {
    let running = stats.initial_balance;
    const sortedTrades = [...trades].reverse();
    sortedTrades.forEach((t) => {
      running += t.profit_loss || 0;
      balancePoints.push(running);
    });
  } else {
    balancePoints.push(stats.current_balance);
  }

  // Calculate SVG curve coordinates
  const minBal = Math.min(...balancePoints) * 0.999;
  const maxBal = Math.max(...balancePoints) * 1.001;
  const range = maxBal - minBal || 1;

  const svgWidth = 280;
  const svgHeight = 50;
  const pointsString = balancePoints
    .map((val, idx) => {
      const x = (idx / (balancePoints.length - 1 || 1)) * svgWidth;
      const y = svgHeight - ((val - minBal) / range) * svgHeight;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <div className="flex flex-col h-full">
      {/* Title */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Trophy className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <h4 className="text-xs font-black text-white tracking-wide">
            Portfolio Analytics & Equity Curve
          </h4>
        </div>
        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Olymp Trade Demo
        </span>
      </div>

      {/* Mini Equity Curve Graph */}
      {balancePoints.length > 1 && (
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 mb-3">
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mb-1">
            <span className="flex items-center gap-1 font-bold">
              <Activity className="w-3 h-3 text-cyan-400" />
              <span>Equity Growth Curve</span>
            </span>
            <span className={isProfitable ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
              ${stats.current_balance.toFixed(2)}
            </span>
          </div>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-12 overflow-visible"
            preserveAspectRatio="none"
          >
            <polyline
              fill="none"
              stroke={isProfitable ? '#10b981' : '#f43f5e'}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={pointsString}
            />
          </svg>
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3 gap-2">
        {/* Win Rate */}
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-semibold mb-1">
            <span>Win Rate</span>
            <Target className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div
            className={`text-base sm:text-xl font-black font-mono ${
              winRate >= 55 ? 'text-emerald-400' : winRate > 0 ? 'text-amber-400' : 'text-slate-300'
            }`}
          >
            {winRate.toFixed(1)}%
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">Threshold: &ge;55%</div>
        </div>

        {/* Total Trades */}
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-semibold mb-1">
            <span>Executed</span>
            <Zap className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-base sm:text-xl font-black font-mono text-white">
            {stats.total_trades}
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5 flex gap-1.5 font-mono font-bold">
            <span className="text-emerald-400">{stats.winning_trades}W</span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-rose-400">{stats.losing_trades}L</span>
          </div>
        </div>

        {/* Net P&L */}
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-semibold mb-1">
            <span>Net Realized P&L</span>
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div
            className={`text-base sm:text-xl font-black font-mono ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfitable ? `+$${stats.total_profit_loss.toFixed(2)}` : `-$${Math.abs(stats.total_profit_loss).toFixed(2)}`}
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">82% FTT Multiplier</div>
        </div>

        {/* Current Balance */}
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-semibold mb-1">
            <span>Balance</span>
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-base sm:text-xl font-black font-mono text-amber-400 truncate">
            ${stats.current_balance.toFixed(2)}
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">Base: ${stats.initial_balance.toFixed(0)}</div>
        </div>

        {/* Return % */}
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-semibold mb-1">
            <span>Growth</span>
            {isProfitable ? (
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            )}
          </div>
          <div
            className={`text-base sm:text-xl font-black font-mono ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfitable ? '+' : ''}
            {(stats.return_percentage * 100).toFixed(2)}%
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">ROI</div>
        </div>

        {/* Streaks */}
        <div className="bg-[#090d16] border border-[#1a243a] rounded-2xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-semibold mb-1">
            <span>Max Streaks</span>
            <Trophy className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-base sm:text-xl font-black font-mono text-white">
            <span className="text-emerald-400">{stats.longest_win_streak}W</span>
            <span className="text-slate-600 text-xs"> / </span>
            <span className="text-rose-400">{stats.longest_loss_streak}L</span>
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">Record</div>
        </div>
      </div>
    </div>
  );
};
