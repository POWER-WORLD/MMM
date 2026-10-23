import React, { useState } from 'react';
import { AgentSignal } from '../types';
import { Bot, ArrowUpRight, ArrowDownRight, Minus, ChevronDown, ChevronUp, Info, Eye, EyeOff } from 'lucide-react';

interface AgentsGridProps {
  signals: AgentSignal[];
}

const AGENT_META: Record<string, { title: string; subtitle: string; tag: string }> = {
  RelativeStrengthIndexAgent: {
    title: 'RSI Oscillator',
    subtitle: 'RSI (14) & Overbought/Sold',
    tag: 'Momentum',
  },
  MovingAverageConvergenceDivergenceAgent: {
    title: 'MACD Trend',
    subtitle: '12 / 26 / 9 Crossovers',
    tag: 'Trend',
  },
  BollingerBandsAgent: {
    title: 'Bollinger Bands',
    subtitle: '20 Period & 2.0 StdDev',
    tag: 'Volatility',
  },
  ExponentialMovingAverageCrossoverAgent: {
    title: 'EMA 9 / 21',
    subtitle: 'Fast vs Slow MA Cross',
    tag: 'Trend Shift',
  },
  StochasticOscillatorAgent: {
    title: 'Stochastic',
    subtitle: '%K 14 / %D 3 Extremes',
    tag: 'Momentum',
  },
  AverageDirectionalIndexAgent: {
    title: 'ADX Strength',
    subtitle: 'ADX (14) & DI+/DI-',
    tag: 'Trend Power',
  },
  IchimokuCloudAgent: {
    title: 'Ichimoku Cloud',
    subtitle: 'Tenkan, Kijun, Kumo',
    tag: 'Structural',
  },
};

export const AgentsGrid: React.FC<AgentsGridProps> = ({ signals }) => {
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [isMatrixCollapsed, setIsMatrixCollapsed] = useState<boolean>(false);

  const toggleExpand = (agentName: string) => {
    setExpandedAgent((prev) => (prev === agentName ? null : agentName));
  };

  return (
    <div className="bg-[#0f1422] border border-[#1e2638] rounded-2xl p-2.5 sm:p-3.5 shadow-xl transition-all">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#182030] mb-2.5">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-amber-400 shrink-0" />
          <h2 className="text-xs sm:text-sm font-bold text-white tracking-wide">
            7 Autonomous Technical Analysis Agents
          </h2>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Unanimous 7/7
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden sm:inline-block text-[10px] text-slate-400 font-mono">
            Whole-Day + 10s Intraday Telemetry
          </span>
          <button
            type="button"
            onClick={() => setIsMatrixCollapsed(!isMatrixCollapsed)}
            className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white transition-colors px-2 py-0.5 rounded-lg bg-[#141b2a] border border-[#20293d]"
          >
            {isMatrixCollapsed ? (
              <>
                <ChevronDown className="w-3.5 h-3.5" />
                <span>Expand Matrix</span>
              </>
            ) : (
              <>
                <ChevronUp className="w-3.5 h-3.5" />
                <span>Compact View</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* When Collapsed: Super-compact horizontal strip */}
      {isMatrixCollapsed ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-1.5 py-1">
          {signals.map((signal, idx) => {
            const meta = AGENT_META[signal.agent_name] || {
              title: signal.agent_name.replace('Agent', ''),
            };
            const isCall = signal.direction === 'CALL';
            const isPut = signal.direction === 'PUT';
            return (
              <div
                key={signal.agent_name || idx}
                onClick={() => {
                  setIsMatrixCollapsed(false);
                  setExpandedAgent(signal.agent_name);
                }}
                className={`flex items-center justify-between px-2 py-1.5 rounded-lg border text-[11px] cursor-pointer hover:border-amber-400/50 transition-all ${
                  isCall
                    ? 'bg-[#0d1b18] border-emerald-500/30 text-emerald-400'
                    : isPut
                    ? 'bg-[#1e1115] border-rose-500/30 text-rose-400'
                    : 'bg-[#121622] border-[#1e2638] text-slate-400'
                }`}
              >
                <span className="truncate font-semibold">{meta.title}</span>
                <span className="font-mono font-bold ml-1">{signal.direction}</span>
              </div>
            );
          })}
        </div>
      ) : (
        /* When Expanded: Full responsive cards grid */
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-7 gap-2 sm:gap-2.5">
          {signals.map((signal, idx) => {
            const meta = AGENT_META[signal.agent_name] || {
              title: signal.agent_name.replace('Agent', ''),
              subtitle: 'Technical Indicator',
              tag: 'Signal',
            };

            const isCall = signal.direction === 'CALL';
            const isPut = signal.direction === 'PUT';
            const isNeutral = !isCall && !isPut;

            const confidencePct = Math.round(signal.confidence * 100);
            const isExpanded = expandedAgent === signal.agent_name;

            let winRateDisplay = '—';
            if (signal.success_rate !== undefined && signal.success_rate !== null) {
              const rawRate = Number(signal.success_rate);
              const normalizedRate = rawRate > 1.0 ? rawRate : rawRate * 100;
              winRateDisplay = `${normalizedRate.toFixed(0)}%`;
            }

            return (
              <div
                key={signal.agent_name || idx}
                onClick={() => toggleExpand(signal.agent_name)}
                className={`rounded-xl border p-2 sm:p-2.5 flex flex-col justify-between transition-all duration-200 cursor-pointer hover:border-amber-500/40 select-none ${
                  isCall
                    ? 'bg-[#0d1b18] border-emerald-500/30 shadow-md shadow-emerald-500/5'
                    : isPut
                    ? 'bg-[#1e1115] border-rose-500/30 shadow-md shadow-rose-500/5'
                    : 'bg-[#121622] border-[#1e2638]'
                }`}
              >
                {/* Header */}
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-[8px] sm:text-[9px] font-semibold uppercase px-1 py-0.5 rounded bg-slate-800 text-slate-400">
                      {meta.tag}
                    </span>
                    <div
                      className={`flex items-center gap-0.5 text-[9px] sm:text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                        isCall
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : isPut
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-slate-700 text-slate-400'
                      }`}
                    >
                      {isCall && <ArrowUpRight className="w-3 h-3" />}
                      {isPut && <ArrowDownRight className="w-3 h-3" />}
                      {isNeutral && <Minus className="w-3 h-3" />}
                      <span>{signal.direction}</span>
                    </div>
                  </div>

                  <h4 className="text-[11px] sm:text-xs font-bold text-white tracking-tight truncate">
                    {meta.title}
                  </h4>
                  <p className="text-[8px] sm:text-[9px] text-slate-400 truncate mb-1">
                    {meta.subtitle}
                  </p>
                </div>

                {/* Confidence Meter */}
                <div className="my-1">
                  <div className="flex items-center justify-between text-[8px] sm:text-[9px] font-mono mb-0.5">
                    <span className="text-slate-400">Confidence</span>
                    <span
                      className={
                        isCall ? 'text-emerald-400 font-bold' : isPut ? 'text-rose-400 font-bold' : 'text-slate-300'
                      }
                    >
                      {confidencePct}%
                    </span>
                  </div>
                  <div className="w-full bg-[#182030] rounded-full h-1 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isCall
                          ? 'bg-emerald-400'
                          : isPut
                          ? 'bg-rose-400'
                          : 'bg-slate-500'
                      }`}
                      style={{ width: `${confidencePct}%` }}
                    />
                  </div>
                </div>

                {/* Footer: Win Rate & Details indicator */}
                <div className="pt-1.5 border-t border-[#1a2336] flex items-center justify-between text-[9px] sm:text-[10px]">
                  <span className="text-slate-400">Win Rate:</span>
                  <span className="font-mono font-semibold text-amber-400">
                    {winRateDisplay}
                  </span>
                </div>

                {/* Expanded Technical Details & Reasoning */}
                {isExpanded && signal.reasoning && (
                  <div className="mt-2 pt-1.5 border-t border-[#222d45] text-[9px] text-slate-300 bg-[#0b0e17] p-1.5 rounded-lg space-y-1">
                    <div className="font-semibold text-amber-300 flex items-center gap-1">
                      <Info className="w-2.5 h-2.5" />
                      <span>Reasoning</span>
                    </div>
                    <p className="text-slate-400 leading-tight">{signal.reasoning}</p>
                    {signal.indicator_values && Object.keys(signal.indicator_values).length > 0 && (
                      <div className="pt-1 font-mono text-[8px] text-slate-400 grid grid-cols-2 gap-1 border-t border-[#1a2336]">
                        {Object.entries(signal.indicator_values).map(([k, v]) => (
                          <div key={k} className="truncate">
                            <span className="text-slate-500">{k}: </span>
                            <span className="text-slate-300 font-semibold">{typeof v === 'number' ? v.toFixed(2) : String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
