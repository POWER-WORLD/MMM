import React from 'react';
import {
  Wifi,
  WifiOff,
  RefreshCw,
  SlidersHorizontal,
  Volume2,
  VolumeX,
  Keyboard,
  TrendingUp,
  Activity,
  Bot,
  Zap,
} from 'lucide-react';

interface HeaderProps {
  currentPrice: number | null;
  previousPrice: number | null;
  sessionHigh?: number;
  sessionLow?: number;
  priceFlash: 'up' | 'down' | null;
  isConnected: boolean;
  pingMs?: number;
  isAudioMuted?: boolean;
  onToggleAudio?: () => void;
  onRefresh: () => void;
  balance: number;
  tradeDurationSeconds: number;
  onDurationChange: (seconds: number) => void;
  tradeAmountUsd: number;
  onAmountChange: (amount: number) => void;
  onOpenBrokerConfig?: () => void;
  onOpenKeyboardShortcuts?: () => void;
  agreeingAgentCount?: number;
  totalAgents?: number;
  consensusReached?: boolean;
  consensusDirection?: 'CALL' | 'PUT' | null;
  onToggleAiPanel?: () => void;
  isAiPanelOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPrice,
  previousPrice,
  sessionHigh,
  sessionLow,
  priceFlash,
  isConnected,
  pingMs = 18,
  isAudioMuted = false,
  onToggleAudio,
  onRefresh,
  balance,
  tradeDurationSeconds,
  onDurationChange,
  tradeAmountUsd,
  onAmountChange,
  onOpenBrokerConfig,
  onOpenKeyboardShortcuts,
  agreeingAgentCount = 0,
  totalAgents = 7,
  consensusReached = false,
  consensusDirection = null,
  onToggleAiPanel,
  isAiPanelOpen = true,
}) => {
  const isUp = currentPrice && previousPrice ? currentPrice >= previousPrice : true;
  const priceDelta = currentPrice && previousPrice ? currentPrice - previousPrice : 0;

  return (
    <header className="h-14 border-b border-[rgba(255,255,255,0.07)] bg-[#080b12] px-3 sm:px-4 flex items-center justify-between shrink-0 select-none z-30">
      {/* Left: Brand Identity & Live Spot Gold Price */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Gold Bullion Badge */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-amber-400 via-amber-500 to-amber-600 flex items-center justify-center font-black text-black text-sm shadow-md shadow-amber-500/20">
            Au
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-white text-sm tracking-tight">XAU / USD</span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                SPOT
              </span>
            </div>
            <span className="text-[10px] text-slate-400 hidden sm:inline-block leading-none">
              Gold 1-Min FTT Desk
            </span>
          </div>
        </div>

        {/* Vertical divider */}
        <div className="h-6 w-px bg-white/10 hidden sm:block" />

        {/* Live Spot Price HUD */}
        <div className="flex items-center gap-2">
          <div
            className={`text-base sm:text-xl font-black font-mono tracking-tight transition-all duration-150 ${
              priceFlash === 'up'
                ? 'text-emerald-400 scale-105'
                : priceFlash === 'down'
                ? 'text-rose-400 scale-105'
                : 'text-white'
            }`}
          >
            {currentPrice !== null && !isNaN(currentPrice)
              ? `$${currentPrice.toFixed(2)}`
              : 'Connecting...'}
          </div>

          <div
            className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-black shrink-0 ${
              isUp
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}
          >
            {isUp ? '▲' : '▼'}
          </div>

          {sessionHigh && sessionLow ? (
            <div className="hidden xl:flex items-center gap-2 text-[10px] font-mono text-slate-400 ml-1">
              <span>
                H: <strong className="text-emerald-400">${sessionHigh.toFixed(2)}</strong>
              </span>
              <span>
                L: <strong className="text-rose-400">${sessionLow.toFixed(2)}</strong>
              </span>
            </div>
          ) : null}
        </div>
      </div>

      {/* Center: AI Consensus Quick Capsule */}
      <div className="hidden md:flex items-center gap-2">
        <button
          type="button"
          onClick={onToggleAiPanel}
          className={`px-3 py-1.5 rounded-full border flex items-center gap-2 text-xs transition-all ${
            consensusReached
              ? consensusDirection === 'CALL'
                ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/20 animate-pulse'
                : 'bg-rose-950/60 border-rose-500/50 text-rose-300 shadow-md shadow-rose-500/20 animate-pulse'
              : 'bg-[#0f1422] border-white/10 text-slate-300 hover:border-amber-400/40'
          }`}
          title="7-Agent Technical Analysis Consensus Protocol"
        >
          <Bot className={`w-3.5 h-3.5 ${consensusReached ? 'text-amber-400' : 'text-slate-400'}`} />
          <span className="font-bold text-[11px]">
            {consensusReached ? (
              <span className="text-white font-mono font-black">
                ⚡ 7/7 UNANIMOUS {consensusDirection}
              </span>
            ) : (
              <span>
                7 AI Agents: <strong className="text-amber-400 font-mono">{agreeingAgentCount} / {totalAgents}</strong> Agree
              </span>
            )}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${
              consensusReached
                ? 'bg-emerald-400 animate-ping'
                : isConnected
                ? 'bg-amber-400'
                : 'bg-slate-600'
            }`}
          />
        </button>
      </div>

      {/* Right: Demo Balance & Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Demo Balance Capsule */}
        <div className="bg-[#0f1422] border border-white/10 rounded-xl px-2.5 sm:px-3 py-1 flex items-center gap-2">
          <div className="text-right">
            <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block leading-none">
              Olymp Demo
            </span>
            <span className="text-xs sm:text-sm font-black font-mono text-amber-400 leading-tight">
              ${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        {/* Audio FX Toggle */}
        {onToggleAudio && (
          <button
            onClick={onToggleAudio}
            type="button"
            title={isAudioMuted ? 'Sound Alerts: Muted' : 'Sound Alerts: Active'}
            className={`p-1.5 rounded-lg border transition-colors ${
              isAudioMuted
                ? 'bg-[#121827] text-slate-500 border-white/5'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/25'
            }`}
          >
            {isAudioMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
        )}

        {/* Telemetry Ping */}
        <div
          className={`hidden sm:flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded-lg border ${
            isConnected
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
          }`}
          title={`Network Roundtrip: ${pingMs}ms`}
        >
          {isConnected ? (
            <>
              <Wifi className="w-3 h-3" />
              <span className="font-bold">{pingMs}ms</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3" />
              <span>Offline</span>
            </>
          )}
        </div>

        {/* Broker API Settings */}
        {onOpenBrokerConfig && (
          <button
            onClick={onOpenBrokerConfig}
            type="button"
            title="Configure Olymp Trade Demo Account"
            className="p-1.5 sm:px-2.5 sm:py-1 rounded-lg bg-[#141b2c] hover:bg-[#1c263c] text-slate-300 hover:text-white border border-white/10 transition-colors flex items-center gap-1.5 text-xs font-semibold"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden xl:inline text-[11px]">Broker</span>
          </button>
        )}

        {/* Hotkeys */}
        {onOpenKeyboardShortcuts && (
          <button
            onClick={onOpenKeyboardShortcuts}
            type="button"
            title="Terminal Hotkeys"
            className="hidden sm:flex p-1.5 rounded-lg bg-[#141b2c] hover:bg-[#1c263c] text-slate-400 hover:text-white border border-white/10 transition-colors"
          >
            <Keyboard className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Force Refresh */}
        <button
          onClick={onRefresh}
          type="button"
          title="Refresh State"
          className="p-1.5 rounded-lg bg-[#141b2c] hover:bg-[#1c263c] text-slate-400 hover:text-white border border-white/10 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
