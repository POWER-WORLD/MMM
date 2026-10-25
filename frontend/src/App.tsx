import React, { useState, useEffect } from 'react';
import { useTradingData } from './hooks/useTradingData';
import { Header } from './components/Header';
import { CandleChart } from './components/CandleChart';
import { AiConsensusPanel } from './components/AiConsensusPanel';
import { OrderExecutionTicket } from './components/OrderExecutionTicket';
import { BottomDockPanel } from './components/BottomDockPanel';
import { OlympTradeModal } from './components/OlympTradeModal';
import { KeyboardShortcutsModal } from './components/KeyboardShortcutsModal';
import { BarChart2, Bot, Zap, History, SlidersHorizontal } from 'lucide-react';

export const App: React.FC = () => {
  const {
    currentPrice,
    previousPrice,
    sessionHigh,
    sessionLow,
    priceFlash,
    candles,
    config,
    updateConfig,
    placeManualTrade,
    agentSignals,
    consensus,
    performance,
    activeTrade,
    recentTrades,
    isConnected,
    pingMs,
    isAudioMuted,
    toggleAudio,
    refetchState,
  } = useTradingData();

  const [isOlympModalOpen, setIsOlympModalOpen] = useState<boolean>(false);
  const [isShortcutsOpen, setIsShortcutsOpen] = useState<boolean>(false);
  const [isAiPanelOpen, setIsAiPanelOpen] = useState<boolean>(true);
  const [activeMobileView, setActiveMobileView] = useState<'chart' | 'radar' | 'order' | 'history'>('chart');

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT' ||
          target.isContentEditable)
      ) {
        return;
      }

      const key = e.key.toLowerCase();
      if (key === 'c') {
        e.preventDefault();
        placeManualTrade('CALL');
      } else if (key === 'p') {
        e.preventDefault();
        placeManualTrade('PUT');
      } else if (key === 'm') {
        e.preventDefault();
        toggleAudio();
      } else if (key === 'r') {
        e.preventDefault();
        refetchState();
      } else if (key === '1') {
        e.preventDefault();
        updateConfig({ candle_interval_seconds: 60 });
      } else if (key === '2') {
        e.preventDefault();
        updateConfig({ candle_interval_seconds: 120 });
      } else if (key === '3') {
        e.preventDefault();
        updateConfig({ candle_interval_seconds: 180 });
      } else if (key === '5') {
        e.preventDefault();
        updateConfig({ candle_interval_seconds: 300 });
      } else if (key === '?' || key === '/') {
        e.preventDefault();
        setIsShortcutsOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [placeManualTrade, toggleAudio, refetchState, updateConfig]);

  return (
    <div className="h-screen w-screen bg-[#06080d] text-slate-100 flex flex-col overflow-hidden antialiased select-none font-['Inter',sans-serif]">
      {/* Top Pro Terminal HUD Bar */}
      <Header
        currentPrice={currentPrice}
        previousPrice={previousPrice}
        sessionHigh={sessionHigh}
        sessionLow={sessionLow}
        priceFlash={priceFlash}
        isConnected={isConnected}
        pingMs={pingMs}
        isAudioMuted={isAudioMuted}
        onToggleAudio={toggleAudio}
        onRefresh={refetchState}
        balance={performance.current_balance}
        tradeDurationSeconds={config.trade_duration_seconds}
        onDurationChange={(secs) => updateConfig({ trade_duration_seconds: secs })}
        tradeAmountUsd={config.trade_amount_usd}
        onAmountChange={(amt) => updateConfig({ trade_amount_usd: amt })}
        onOpenBrokerConfig={() => setIsOlympModalOpen(true)}
        onOpenKeyboardShortcuts={() => setIsShortcutsOpen(true)}
        agreeingAgentCount={consensus?.agreeing_agent_count || 0}
        totalAgents={consensus?.total_agents || 7}
        consensusReached={consensus?.consensus_reached || false}
        consensusDirection={consensus?.direction || null}
        onToggleAiPanel={() => setIsAiPanelOpen(!isAiPanelOpen)}
        isAiPanelOpen={isAiPanelOpen}
      />

      {/* Main 3-Column Trading Terminal Workspace */}
      <div className="flex-1 min-h-0 flex w-full overflow-hidden relative">
        {/* Left Column: AI Consensus & 7 Agents Radar Panel */}
        <div
          className={`${
            activeMobileView === 'radar' ? 'block fixed inset-0 top-14 bottom-12 z-30' : 'hidden lg:flex'
          }`}
        >
          <AiConsensusPanel
            consensus={consensus}
            signals={agentSignals}
            isOpen={isAiPanelOpen}
            onToggle={() => setIsAiPanelOpen(!isAiPanelOpen)}
          />
        </div>

        {/* Center Column: Interactive Chart + Collapsible Bottom History/Analytics Dock */}
        <div
          className={`flex-1 min-w-0 flex flex-col h-full overflow-hidden ${
            activeMobileView === 'chart' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {/* Real-time Candlestick Chart */}
          <div className="flex-1 min-h-0 w-full relative">
            <CandleChart
              candles={candles}
              currentPrice={currentPrice}
              candleIntervalSeconds={config.candle_interval_seconds}
              onIntervalChange={(secs) => updateConfig({ candle_interval_seconds: secs })}
              activeTrade={activeTrade}
            />
          </div>

          {/* Bottom Dockable Journal & Performance Panel */}
          <div className="hidden lg:block">
            <BottomDockPanel trades={recentTrades} performance={performance} />
          </div>
        </div>

        {/* Right Column: FTT High-Frequency Order Execution Terminal */}
        <div
          className={`${
            activeMobileView === 'order' ? 'block fixed inset-0 top-14 bottom-12 z-30' : 'hidden lg:flex'
          }`}
        >
          <OrderExecutionTicket
            trade={activeTrade}
            currentPrice={currentPrice}
            tradeDurationSeconds={config.trade_duration_seconds}
            tradeAmountUsd={config.trade_amount_usd}
            onPlaceManualTrade={placeManualTrade}
            onDurationChange={(secs) => updateConfig({ trade_duration_seconds: secs })}
            onAmountChange={(amt) => updateConfig({ trade_amount_usd: amt })}
            autoTradeEnabled={config.auto_trade_enabled !== false}
            onToggleAutoTrade={() =>
              updateConfig({ auto_trade_enabled: config.auto_trade_enabled === false })
            }
            performance={performance}
            onOpenBrokerConfig={() => setIsOlympModalOpen(true)}
          />
        </div>

        {/* Mobile-Only History View */}
        {activeMobileView === 'history' && (
          <div className="lg:hidden fixed inset-0 top-14 bottom-12 z-30 bg-[#080c14] overflow-y-auto p-3">
            <BottomDockPanel trades={recentTrades} performance={performance} />
          </div>
        )}
      </div>

      {/* Mobile-Only Sticky Bottom Switcher */}
      <nav className="lg:hidden h-12 bg-[#090d16] border-t border-[rgba(255,255,255,0.07)] flex items-center justify-around px-2 z-40 shrink-0 select-none">
        <button
          type="button"
          onClick={() => setActiveMobileView('chart')}
          className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
            activeMobileView === 'chart' ? 'text-amber-400' : 'text-slate-400'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          <span>Chart</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveMobileView('radar')}
          className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
            activeMobileView === 'radar' ? 'text-amber-400' : 'text-slate-400'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span>7 Agents</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveMobileView('order')}
          className={`flex flex-col items-center gap-0.5 text-[10px] font-bold relative ${
            activeMobileView === 'order' ? 'text-amber-400' : 'text-slate-400'
          }`}
        >
          <Zap className="w-4 h-4 text-emerald-400" />
          <span>Trade</span>
          {activeTrade && (
            <span className="absolute -top-1 right-1 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveMobileView('history')}
          className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
            activeMobileView === 'history' ? 'text-amber-400' : 'text-slate-400'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Journal</span>
        </button>

        <button
          type="button"
          onClick={() => setIsOlympModalOpen(true)}
          className="flex flex-col items-center gap-0.5 text-[10px] font-bold text-slate-400 hover:text-white"
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span>Config</span>
        </button>
      </nav>

      {/* Olymp Trade Broker Config Modal */}
      <OlympTradeModal
        isOpen={isOlympModalOpen}
        onClose={() => setIsOlympModalOpen(false)}
        defaultStake={config.trade_amount_usd}
        defaultDuration={config.trade_duration_seconds}
        onSavePreferences={({ stake, duration }) =>
          updateConfig({ trade_amount_usd: stake, trade_duration_seconds: duration })
        }
      />

      {/* Terminal Hotkeys Guide Modal */}
      <KeyboardShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />
    </div>
  );
};

export default App;
