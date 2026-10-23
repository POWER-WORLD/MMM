import React from 'react';
import { PerformanceStats as StatsType } from '../types';
import { Trophy, TrendingUp, TrendingDown, Target, Zap, DollarSign } from 'lucide-react';

interface PerformanceStatsProps {
  stats: StatsType;
}

export const PerformanceStats: React.FC<PerformanceStatsProps> = ({ stats }) => {
  const winRate = stats.success_rate > 1.0 ? stats.success_rate : stats.success_rate * 100;
  const isProfitable = stats.total_profit_loss >= 0;

  return (
    <div className="bg-[#0f1422] border border-[#1e2638] rounded-2xl p-3 sm:p-4 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-[#182030] mb-3">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-400 shrink-0" />
          <h3 className="text-xs sm:text-sm font-bold text-white tracking-wide">
            Trading Performance & Profit/Loss Overview
          </h3>
        </div>
        <span className="text-[9px] sm:text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Olymp Trade Demo
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3 gap-2">
        {/* Win Rate */}
        <div className="bg-[#121826] border border-[#1e2638] rounded-xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
            <span>Win Rate</span>
            <Target className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div
            className={`text-base sm:text-xl font-bold font-mono ${
              winRate >= 55 ? 'text-emerald-400' : winRate > 0 ? 'text-amber-400' : 'text-slate-300'
            }`}
          >
            {winRate.toFixed(1)}%
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">
            Target: &gt;55%
          </div>
        </div>

        {/* Total Trades */}
        <div className="bg-[#121826] border border-[#1e2638] rounded-xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
            <span>Total Trades</span>
            <Zap className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-base sm:text-xl font-bold font-mono text-white">
            {stats.total_trades}
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5 flex gap-1.5 font-mono">
            <span className="text-emerald-400">{stats.winning_trades}W</span>
            <span className="text-rose-400">{stats.losing_trades}L</span>
          </div>
        </div>

        {/* Net P&L */}
        <div className="bg-[#121826] border border-[#1e2638] rounded-xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
            <span>Net P&L</span>
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div
            className={`text-base sm:text-xl font-bold font-mono ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfitable ? `+$${stats.total_profit_loss.toFixed(2)}` : `-$${Math.abs(stats.total_profit_loss).toFixed(2)}`}
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">
            Stake $1 &bull; 82%
          </div>
        </div>

        {/* Current Balance */}
        <div className="bg-[#121826] border border-[#1e2638] rounded-xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
            <span>Balance</span>
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-base sm:text-xl font-bold font-mono text-amber-400 truncate">
            ${stats.current_balance.toFixed(2)}
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">
            Base: ${stats.initial_balance.toFixed(0)}
          </div>
        </div>

        {/* Return % */}
        <div className="bg-[#121826] border border-[#1e2638] rounded-xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
            <span>Net Return</span>
            {isProfitable ? <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> : <TrendingDown className="w-3.5 h-3.5 text-rose-400" />}
          </div>
          <div
            className={`text-base sm:text-xl font-bold font-mono ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfitable ? '+' : ''}{(stats.return_percentage * 100).toFixed(2)}%
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">
            Growth
          </div>
        </div>

        {/* Streaks */}
        <div className="bg-[#121826] border border-[#1e2638] rounded-xl p-2.5 sm:p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
            <span>Streaks</span>
            <Trophy className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-base sm:text-xl font-bold font-mono text-white">
            <span className="text-emerald-400">{stats.longest_win_streak}W</span>
            <span className="text-slate-500 text-xs"> / </span>
            <span className="text-rose-400">{stats.longest_loss_streak}L</span>
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">
            Max Streak
          </div>
        </div>
      </div>
    </div>
  );
};
