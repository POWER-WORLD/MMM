import React, { useState } from 'react';
import { ActiveTrade, PerformanceStats } from '../types';
import {
  History,
  TrendingUp,
  Download,
  Search,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  ShieldCheck,
} from 'lucide-react';
import { PerformanceStats as PerformanceView } from './PerformanceStats';
import { TradeHistoryTable } from './TradeHistoryTable';

interface BottomDockPanelProps {
  trades: ActiveTrade[];
  performance: PerformanceStats;
}

export const BottomDockPanel: React.FC<BottomDockPanelProps> = ({
  trades,
  performance,
}) => {
  const [activeTab, setActiveTab] = useState<'history' | 'analytics'>('history');
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  return (
    <div className="border-t border-[rgba(255,255,255,0.07)] bg-[#080c14] flex flex-col shrink-0 transition-all select-none z-10">
      {/* Dock Bar Tabs */}
      <div className="h-9 px-3 flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] bg-[#090d16]">
        {/* Left: Tab Switcher */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => {
              setActiveTab('history');
              setIsCollapsed(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-bold transition-all ${
              activeTab === 'history' && !isCollapsed
                ? 'bg-amber-500/15 text-amber-400 border border-amber-500/25'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Execution History ({trades.length})</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('analytics');
              setIsCollapsed(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-bold transition-all ${
              activeTab === 'analytics' && !isCollapsed
                ? 'bg-amber-500/15 text-amber-400 border border-amber-500/25'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Performance & Equity Curve</span>
          </button>
        </div>

        {/* Right: Collapse / Expand Button */}
        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white p-1 rounded-md hover:bg-white/5 transition-colors"
          title={isCollapsed ? 'Expand Bottom Panel' : 'Collapse Bottom Panel'}
        >
          {isCollapsed ? (
            <>
              <ChevronUp className="w-4 h-4 text-amber-400" />
              <span className="text-[10px]">Expand</span>
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4 text-amber-400" />
              <span className="text-[10px]">Collapse</span>
            </>
          )}
        </button>
      </div>

      {/* Dock Content Body */}
      {!isCollapsed && (
        <div className="h-[210px] xl:h-[240px] overflow-y-auto p-2.5">
          {activeTab === 'history' ? (
            <TradeHistoryTable trades={trades} />
          ) : (
            <PerformanceView stats={performance} trades={trades} />
          )}
        </div>
      )}
    </div>
  );
};
