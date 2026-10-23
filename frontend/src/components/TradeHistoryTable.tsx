import React from 'react';
import { ActiveTrade } from '../types';
import { History, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface TradeHistoryTableProps {
  trades: ActiveTrade[];
}

export const TradeHistoryTable: React.FC<TradeHistoryTableProps> = ({ trades }) => {
  return (
    <div className="bg-[#0f1422] border border-[#1e2638] rounded-2xl p-3 sm:p-4 shadow-xl">
      <div className="flex items-center justify-between pb-2.5 border-b border-[#182030] mb-3">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-amber-400 shrink-0" />
          <h3 className="text-xs sm:text-sm font-bold text-white tracking-wide">
            1-Minute Trade Execution History
          </h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          {trades.length} Trades
        </span>
      </div>

      <div className="overflow-x-auto max-h-[300px] overflow-y-auto rounded-xl border border-[#182030]">
        <table className="w-full text-left text-[11px] sm:text-xs font-mono min-w-[560px]">
          <thead className="bg-[#121826] text-slate-400 sticky top-0 border-b border-[#1e2638] z-10">
            <tr>
              <th className="py-2 px-3">Time</th>
              <th className="py-2 px-3">Order ID</th>
              <th className="py-2 px-3">Direction</th>
              <th className="py-2 px-3 text-right">Entry</th>
              <th className="py-2 px-3 text-right">Exit</th>
              <th className="py-2 px-3 text-center">Result</th>
              <th className="py-2 px-3 text-right">P&L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182030]">
            {trades.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-slate-500">
                  No trades executed yet. Awaiting unanimous 7/7 agent consensus.
                </td>
              </tr>
            ) : (
              trades.map((trade) => {
                const isWin = trade.result === 'WIN';
                const isLoss = trade.result === 'LOSS';
                const isCall = trade.direction === 'CALL';

                const formattedTime = new Date(trade.entry_time).toLocaleTimeString();

                return (
                  <tr
                    key={trade.trade_id}
                    className="hover:bg-[#141b2a] transition-colors duration-150"
                  >
                    <td className="py-2 px-3 text-slate-400">{formattedTime}</td>
                    <td className="py-2 px-3 text-slate-500">{trade.trade_id.slice(0, 8)}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`inline-flex items-center gap-1 font-bold ${
                          isCall ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {isCall ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {trade.direction}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right text-slate-300">
                      ${trade.entry_price.toFixed(2)}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-300">
                      {trade.exit_price !== null ? `$${trade.exit_price.toFixed(2)}` : '—'}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isWin
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : isLoss
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {trade.result}
                      </span>
                    </td>
                    <td
                      className={`py-2 px-3 text-right font-bold ${
                        isWin ? 'text-emerald-400' : isLoss ? 'text-rose-400' : 'text-slate-400'
                      }`}
                    >
                      {isWin
                        ? `+$${trade.profit_loss.toFixed(2)}`
                        : isLoss
                        ? `-$${Math.abs(trade.profit_loss).toFixed(2)}`
                        : '—'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
