import React, { useState } from 'react';
import { ActiveTrade } from '../types';
import {
  History,
  ArrowUpRight,
  ArrowDownRight,
  Download,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface TradeHistoryTableProps {
  trades: ActiveTrade[];
}

export const TradeHistoryTable: React.FC<TradeHistoryTableProps> = ({ trades }) => {
  const [filterType, setFilterType] = useState<'ALL' | 'WIN' | 'LOSS' | 'CALL' | 'PUT'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedTradeId, setExpandedTradeId] = useState<string | null>(null);

  // Filter trades
  const filteredTrades = trades.filter((trade) => {
    // Type filter
    if (filterType === 'WIN' && trade.result !== 'WIN') return false;
    if (filterType === 'LOSS' && trade.result !== 'LOSS') return false;
    if (filterType === 'CALL' && trade.direction !== 'CALL') return false;
    if (filterType === 'PUT' && trade.direction !== 'PUT') return false;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        trade.trade_id.toLowerCase().includes(q) ||
        trade.direction.toLowerCase().includes(q) ||
        trade.result.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Export to CSV
  const handleExportCsv = () => {
    if (trades.length === 0) return;

    const headers = [
      'Trade ID',
      'Direction',
      'Entry Time',
      'Entry Price',
      'Exit Time',
      'Exit Price',
      'Duration (s)',
      'Stake (USD)',
      'Result',
      'P&L (USD)',
    ];

    const rows = trades.map((t) => [
      t.trade_id,
      t.direction,
      t.entry_time,
      t.entry_price,
      t.exit_time || '',
      t.exit_price || '',
      t.duration_seconds,
      t.amount,
      t.result,
      t.profit_loss,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `gold_ftt_trades_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const toggleExpand = (id: string) => {
    setExpandedTradeId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2 border-b border-white/5">
        <div className="flex items-center gap-2">
          <History className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <h4 className="text-xs font-black text-white tracking-wide">
            Execution Log
          </h4>
          <span className="text-[10px] font-mono text-slate-400 font-bold bg-[#141b2c] px-2 py-0.5 rounded-full border border-white/5">
            {filteredTrades.length} / {trades.length}
          </span>
        </div>

        {/* Filter Pills & Actions */}
        <div className="flex flex-wrap items-center gap-1.5">
          {/* Filter Pills */}
          <div className="flex items-center gap-0.5 bg-[#0e1320] p-0.5 rounded-lg border border-white/5">
            {(['ALL', 'WIN', 'LOSS', 'CALL', 'PUT'] as const).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setFilterType(type)}
                className={`text-[10px] font-bold px-2 py-0.5 rounded transition-all ${
                  filterType === type
                    ? 'bg-amber-500 text-black font-black shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          {/* Export to CSV */}
          <button
            onClick={handleExportCsv}
            type="button"
            disabled={trades.length === 0}
            title="Export trades to CSV"
            className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold text-slate-300 hover:text-white bg-[#141b2c] hover:bg-[#1d273e] border border-white/10 rounded-lg transition-colors disabled:opacity-40"
          >
            <Download className="w-3 h-3 text-amber-400" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Desktop & Tablet Table View */}
      <div className="overflow-x-auto flex-1 overflow-y-auto rounded-xl border border-white/5">
        <table className="w-full text-left text-xs font-mono min-w-[580px]">
          <thead className="bg-[#0a0e18] text-slate-400 sticky top-0 border-b border-white/5 z-10 select-none">
            <tr>
              <th className="py-2.5 px-3">Time</th>
              <th className="py-2.5 px-3">Order ID</th>
              <th className="py-2.5 px-3">Contract</th>
              <th className="py-2.5 px-3 text-right">Entry</th>
              <th className="py-2.5 px-3 text-right">Exit</th>
              <th className="py-2.5 px-3 text-center">Outcome</th>
              <th className="py-2.5 px-3 text-right">Net P&L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#151d2f]">
            {filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-500 font-sans">
                  No trade executions matching filter criteria. Awaiting unanimous 7/7 signals.
                </td>
              </tr>
            ) : (
              filteredTrades.map((trade) => {
                const isWin = trade.result === 'WIN';
                const isLoss = trade.result === 'LOSS';
                const isCall = trade.direction === 'CALL';
                const formattedTime = new Date(trade.entry_time).toLocaleTimeString();
                const isExpanded = expandedTradeId === trade.trade_id;

                return (
                  <React.Fragment key={trade.trade_id}>
                    <tr
                      onClick={() => toggleExpand(trade.trade_id)}
                      className="hover:bg-[#121929] transition-colors cursor-pointer"
                    >
                      <td className="py-2.5 px-3 text-slate-400">{formattedTime}</td>
                      <td className="py-2.5 px-3 text-slate-400 font-semibold">
                        #{trade.trade_id.slice(0, 8)}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-flex items-center gap-1 font-bold ${
                            isCall ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {isCall ? (
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          ) : (
                            <ArrowDownRight className="w-3.5 h-3.5" />
                          )}
                          <span>
                            {trade.duration_seconds}s {trade.direction}
                          </span>
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300 font-bold">
                        ${trade.entry_price.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-300 font-bold">
                        {trade.exit_price !== null ? `$${trade.exit_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-black ${
                            isWin
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : isLoss
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}
                        >
                          {trade.result}
                        </span>
                      </td>
                      <td
                        className={`py-2.5 px-3 text-right font-black ${
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

                    {/* Expandable row for audit metadata */}
                    {isExpanded && (
                      <tr className="bg-[#090d16] text-[11px] text-slate-400">
                        <td colSpan={7} className="px-4 py-2.5 border-t border-[#162033]">
                          <div className="flex flex-wrap items-center justify-between gap-4 font-mono">
                            <div>
                              <span className="text-slate-500">Stake Amount:</span>{' '}
                              <span className="text-white font-bold">${trade.amount.toFixed(2)}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Payout Multiplier:</span>{' '}
                              <span className="text-emerald-400 font-bold">82%</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Exit Timestamp:</span>{' '}
                              <span className="text-slate-300">
                                {trade.exit_time
                                  ? new Date(trade.exit_time).toLocaleTimeString()
                                  : 'In Progress'}
                              </span>
                            </div>
                            <div className="text-amber-400">
                              Validated via 7/7 Unanimous Engine
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
