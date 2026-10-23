import React, { useState } from 'react';
import { useTradingData } from './hooks/useTradingData';
import { Header } from './components/Header';
import { CandleChart } from './components/CandleChart';
import { ConsensusBar } from './components/ConsensusBar';
import { AgentsGrid } from './components/AgentsGrid';
import { ActiveTradeCard } from './components/ActiveTradeCard';
import { PerformanceStats } from './components/PerformanceStats';
import { TradeHistoryTable } from './components/TradeHistoryTable';
import { OlympTradeModal } from './components/OlympTradeModal';
import { Settings, ShieldCheck, Zap } from 'lucide-react';

export const App: React.FC = () => {
  const {
    currentPrice,
    previousPrice,
    priceFlash,
    candles,
    config,
    updateConfig,
    agentSignals,
    consensus,
    performance,
    activeTrade,
    recentTrades,
    isConnected,
    refetchState,
  } = useTradingData();

  const [isOlympModalOpen, setIsOlympModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col antialiased selection:bg-amber-500/20 selection:text-amber-300">
      {/* Top Navigation & Controls */}
      <Header
        currentPrice={currentPrice}
        previousPrice={previousPrice}
        priceFlash={priceFlash}
        isConnected={isConnected}
        onRefresh={refetchState}
        balance={performance.current_balance}
        tradeDurationSeconds={config.trade_duration_seconds}
        onDurationChange={(secs) => updateConfig({ trade_duration_seconds: secs })}
        tradeAmountUsd={config.trade_amount_usd}
        onAmountChange={(amt) => updateConfig({ trade_amount_usd: amt })}
        onOpenBrokerConfig={() => setIsOlympModalOpen(true)}
      />

      {/* Main Responsive Trading Platform Container - Edge-to-Edge Full Screen Coverage */}
      <main className="flex-1 w-full max-w-none px-2.5 sm:px-4 md:px-5 py-3 space-y-3 min-w-0">
        {/* Consensus Engine Banner (7/7 Unanimous Rule) */}
        <ConsensusBar
          consensus={consensus}
          agentCount={agentSignals.length || 7}
        />

        {/* 7 Specialized Technical Analysis Agents Matrix */}
        <AgentsGrid signals={agentSignals} />

        {/* Core Trading & Chart Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 min-w-0">
          {/* Primary Workspace (Left Column): Candlestick Chart + Trade History */}
          <div className="lg:col-span-8 xl:col-span-8 2xl:col-span-9 space-y-3 min-w-0">
            <CandleChart
              candles={candles}
              currentPrice={currentPrice}
              candleIntervalSeconds={config.candle_interval_seconds}
              onIntervalChange={(secs) => updateConfig({ candle_interval_seconds: secs })}
            />
            <TradeHistoryTable trades={recentTrades} />
          </div>

          {/* Right Column: Live FTT Trade Card + Performance Overview + Broker Widget */}
          <div className="lg:col-span-4 xl:col-span-4 2xl:col-span-3 space-y-3 min-w-0">
            {/* Live Trade Execution Monitor */}
            <ActiveTradeCard
              trade={activeTrade}
              currentPrice={currentPrice}
              tradeDurationSeconds={config.trade_duration_seconds}
              tradeAmountUsd={config.trade_amount_usd}
            />

            {/* Performance Statistics Overview */}
            <PerformanceStats stats={performance} />

            {/* Broker Status & Dynamic Settings Card */}
            <div className="bg-[#0f1422] border border-[#1e2638] rounded-2xl p-3 sm:p-4 shadow-xl">
              <div className="flex items-center justify-between pb-2 border-b border-[#182030] mb-2.5">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Broker Execution Link
                  </h4>
                </div>
                <button
                  onClick={() => setIsOlympModalOpen(true)}
                  className="flex items-center gap-1 text-[11px] font-semibold text-amber-400 hover:text-amber-300 transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" />
                  <span>Configure</span>
                </button>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-[#182030]/60">
                  <span className="text-slate-400">Trading Asset:</span>
                  <span className="font-mono font-semibold text-white">Gold (XAU/USD)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#182030]/60">
                  <span className="text-slate-400">Account Type:</span>
                  <span className="font-semibold text-emerald-400">Olymp Trade Demo</span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#182030]/60">
                  <span className="text-slate-400">Candle Interval:</span>
                  <span className="font-mono font-semibold text-amber-400">
                    {config.candle_interval_seconds}s (Dynamic)
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#182030]/60">
                  <span className="text-slate-400">Contract Duration:</span>
                  <span className="font-mono font-semibold text-amber-400">
                    {config.trade_duration_seconds}s ({Math.floor(config.trade_duration_seconds / 60)}m)
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#182030]/60">
                  <span className="text-slate-400">Order Stake:</span>
                  <span className="font-mono font-semibold text-emerald-400">
                    ${config.trade_amount_usd.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Consensus Engine:</span>
                  <span className="font-bold text-amber-400">7 / 7 Unanimous</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Olymp Trade Account Config Modal */}
      <OlympTradeModal
        isOpen={isOlympModalOpen}
        onClose={() => setIsOlympModalOpen(false)}
      />
    </div>
  );
};

export default App;
