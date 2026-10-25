import React, { useState } from 'react';
import { AgentSignal, AgentMetadata } from '../types';
import {
  Bot,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  ChevronDown,
  ChevronUp,
  Info,
  SlidersHorizontal,
  Layers,
  Sparkles,
} from 'lucide-react';
import { AgentDetailModal } from './AgentDetailModal';

interface AgentsGridProps {
  signals: AgentSignal[];
}

export const AGENT_REGISTRY: Record<string, AgentMetadata> = {
  RelativeStrengthIndexAgent: {
    id: 'rsi',
    title: 'RSI Oscillator',
    subtitle: 'RSI (14) Momentum & Bounds',
    tag: 'RSI-14',
    category: 'Momentum',
    description:
      'Evaluates speed and change of price movements to identify overbought (>70) or oversold (<30) market conditions on Gold spot price.',
    formula: 'RSI = 100 - (100 / (1 + RS)), where RS = Avg Gain / Avg Loss',
    thresholds: 'CALL when RSI < 30 (Oversold); PUT when RSI > 70 (Overbought).',
  },
  MovingAverageConvergenceDivergenceAgent: {
    id: 'macd',
    title: 'MACD Trend Cross',
    subtitle: '12 / 26 / 9 Fast-Slow Delta',
    tag: 'MACD',
    category: 'Trend',
    description:
      'Calculates relationship between 12 EMA and 26 EMA with a 9-period signal trigger line to catch immediate trend momentum shifts.',
    formula: 'MACD Line = EMA(12) - EMA(26); Signal = EMA(9, MACD)',
    thresholds: 'CALL on Bullish Histogram / Signal Cross; PUT on Bearish Cross.',
  },
  BollingerBandsAgent: {
    id: 'bb',
    title: 'Bollinger Bands',
    subtitle: '20 Period & 2.0 StdDev',
    tag: 'B-Bands',
    category: 'Volatility',
    description:
      'Measures price volatility relative to 20-period moving average with upper and lower bands set 2 standard deviations away.',
    formula: 'Middle = SMA(20); Upper/Lower = Middle ± (2.0 * σ)',
    thresholds: 'CALL on Lower Band bounce; PUT on Upper Band rejection.',
  },
  ExponentialMovingAverageCrossoverAgent: {
    id: 'ema',
    title: 'EMA 9 / 21 Crossover',
    subtitle: 'Fast vs Slow Moving Averages',
    tag: 'EMA-Cross',
    category: 'Trend',
    description:
      'Captures short-term versus medium-term trend direction. The 9 EMA reacts rapidly to new ticks compared to the smoothing 21 EMA.',
    formula: 'EMA = (Close - PrevEMA) * Multiplier + PrevEMA',
    thresholds: 'CALL when EMA 9 crosses above EMA 21; PUT when 9 crosses below 21.',
  },
  StochasticOscillatorAgent: {
    id: 'stoch',
    title: 'Stochastic Oscillator',
    subtitle: '%K 14 / %D 3 Extremes',
    tag: 'Stochastic',
    category: 'Momentum',
    description:
      'Compares Gold closing price to its recent price range over 14 intervals, pinpointing precise market turning points.',
    formula: '%K = ((Close - Low14) / (High14 - Low14)) * 100; %D = SMA(3, %K)',
    thresholds: 'CALL when %K crosses %D below 20; PUT when %K crosses %D above 80.',
  },
  AverageDirectionalIndexAgent: {
    id: 'adx',
    title: 'ADX Trend Strength',
    subtitle: 'ADX (14) & DI+ / DI-',
    tag: 'ADX-Power',
    category: 'Trend',
    description:
      'Quantifies overall trend strength regardless of direction using Directional Movement indicators (+DI and -DI).',
    formula: 'ADX = 100 * EMA(14, |+DI - -DI| / (|+DI + -DI|))',
    thresholds: 'ADX > 25 confirms strong trend; directional signal guided by +DI vs -DI.',
  },
  IchimokuCloudAgent: {
    id: 'ichimoku',
    title: 'Ichimoku Kinko Hyo',
    subtitle: 'Tenkan, Kijun & Kumo Cloud',
    tag: 'Ichimoku',
    category: 'Structural',
    description:
      'Multi-faceted Japanese charting system assessing market equilibrium, support/resistance zones, and breakout momentum.',
    formula: 'Tenkan = (H9+L9)/2; Kijun = (H26+L26)/2; Senkou Span A & B',
    thresholds: 'CALL when price > Cloud & Tenkan > Kijun; PUT when below Cloud.',
  },
};

const CATEGORIES = ['All', 'Momentum', 'Trend', 'Volatility', 'Structural'] as const;

export const AgentsGrid: React.FC<AgentsGridProps> = ({ signals }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [isMatrixCollapsed, setIsMatrixCollapsed] = useState<boolean>(false);
  const [activeModalAgent, setActiveModalAgent] = useState<{
    signal: AgentSignal;
    meta: AgentMetadata;
  } | null>(null);

  // Filter signals based on selected category
  const filteredSignals = signals.filter((signal) => {
    if (selectedCategory === 'All') return true;
    const meta = AGENT_REGISTRY[signal.agent_name];
    return meta ? meta.category === selectedCategory : true;
  });

  return (
    <div className="bg-[#0e1320] border border-[#1b253b] rounded-3xl p-3.5 sm:p-4 shadow-xl">
      {/* Top Header & Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#182236] mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs sm:text-sm font-extrabold text-white tracking-wide flex items-center gap-2">
              <span>7 Autonomous Technical Analysis Agents</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                100% Unanimous Rule
              </span>
            </h2>
          </div>
        </div>

        {/* Categories & View Mode */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category Filter Pills */}
          <div className="flex items-center gap-1 bg-[#121826] p-0.5 rounded-xl border border-[#1e2a42]">
            {CATEGORIES.map((cat) => {
              const isActive = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`text-[10px] sm:text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all ${
                    isActive
                      ? 'bg-amber-500 text-black shadow-md shadow-amber-500/20'
                      : 'text-slate-400 hover:text-white hover:bg-[#192338]'
                  }`}
                >
                  {cat}
                </button>
              );
            })}
          </div>

          {/* Toggle Compact / Full Grid */}
          <button
            type="button"
            onClick={() => setIsMatrixCollapsed(!isMatrixCollapsed)}
            className="flex items-center gap-1 text-[11px] font-semibold text-slate-300 hover:text-white bg-[#141b2c] border border-[#202b44] hover:bg-[#1a233a] px-2.5 py-1 rounded-xl transition-colors"
          >
            {isMatrixCollapsed ? (
              <>
                <ChevronDown className="w-3.5 h-3.5 text-amber-400" />
                <span>Expand</span>
              </>
            ) : (
              <>
                <ChevronUp className="w-3.5 h-3.5 text-amber-400" />
                <span>Compact</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* When Collapsed: Super-compact horizontal strip */}
      {isMatrixCollapsed ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 py-1">
          {filteredSignals.map((signal, idx) => {
            const meta = AGENT_REGISTRY[signal.agent_name] || {
              title: signal.agent_name.replace('Agent', ''),
              tag: 'Agent',
              category: 'Trend',
            };
            const isCall = signal.direction === 'CALL';
            const isPut = signal.direction === 'PUT';

            return (
              <div
                key={signal.agent_name || idx}
                onClick={() =>
                  setActiveModalAgent({
                    signal,
                    meta: AGENT_REGISTRY[signal.agent_name] || (meta as AgentMetadata),
                  })
                }
                className={`flex items-center justify-between p-2 rounded-xl border text-xs cursor-pointer hover:scale-[1.02] transition-all select-none ${
                  isCall
                    ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-400 hover:border-emerald-400'
                    : isPut
                    ? 'bg-rose-950/30 border-rose-500/30 text-rose-400 hover:border-rose-400'
                    : 'bg-[#121826] border-[#1e2a42] text-slate-400'
                }`}
              >
                <span className="truncate font-bold text-[11px]">{meta.title}</span>
                <span className="font-mono font-black ml-1 text-xs">
                  {isCall ? '▲ CALL' : isPut ? '▼ PUT' : '—'}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        /* When Expanded: Full responsive cards grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-2.5 sm:gap-3">
          {filteredSignals.map((signal, idx) => {
            const meta = AGENT_REGISTRY[signal.agent_name] || {
              title: signal.agent_name.replace('Agent', ''),
              subtitle: 'Technical Indicator',
              tag: 'Signal',
              category: 'Trend',
              description: '',
              formula: '',
              thresholds: '',
              id: signal.agent_name,
            };

            const isCall = signal.direction === 'CALL';
            const isPut = signal.direction === 'PUT';
            const isNeutral = !isCall && !isPut;
            const confidencePct = Math.round(signal.confidence * 100);

            let winRateDisplay = '—';
            if (signal.success_rate !== undefined && signal.success_rate !== null) {
              const rawRate = Number(signal.success_rate);
              const normalizedRate = rawRate > 1.0 ? rawRate : rawRate * 100;
              winRateDisplay = `${normalizedRate.toFixed(0)}%`;
            }

            return (
              <div
                key={signal.agent_name || idx}
                onClick={() => setActiveModalAgent({ signal, meta: meta as AgentMetadata })}
                className={`rounded-2xl border p-3 flex flex-col justify-between transition-all duration-200 cursor-pointer hover:border-amber-400/50 hover:shadow-lg select-none group ${
                  isCall
                    ? 'bg-gradient-to-b from-[#0b1c18] to-[#0d1422] border-emerald-500/30 shadow-emerald-500/5 hover:border-emerald-400'
                    : isPut
                    ? 'bg-gradient-to-b from-[#201015] to-[#0d1422] border-rose-500/30 shadow-rose-500/5 hover:border-rose-400'
                    : 'bg-[#111726] border-[#1d273e]'
                }`}
              >
                {/* Header: Tag + Output Pill */}
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1.5">
                    <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-md bg-[#161f33] text-slate-400 border border-[#222e48]">
                      {meta.tag}
                    </span>
                    <div
                      className={`flex items-center gap-1 text-[10px] font-black px-2 py-0.5 rounded-full ${
                        isCall
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : isPut
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {isCall && <ArrowUpRight className="w-3 h-3" />}
                      {isPut && <ArrowDownRight className="w-3 h-3" />}
                      {isNeutral && <Minus className="w-3 h-3" />}
                      <span>{signal.direction}</span>
                    </div>
                  </div>

                  <h3 className="text-xs font-black text-white tracking-tight truncate group-hover:text-amber-300 transition-colors">
                    {meta.title}
                  </h3>
                  <p className="text-[9px] text-slate-400 truncate mt-0.5">{meta.subtitle}</p>
                </div>

                {/* Confidence Meter Bar */}
                <div className="my-2 bg-[#090d16] p-2 rounded-xl border border-[#1a243a]">
                  <div className="flex items-center justify-between text-[9px] font-mono mb-1">
                    <span className="text-slate-400 font-semibold">Confidence</span>
                    <span
                      className={`font-black ${
                        isCall
                          ? 'text-emerald-400'
                          : isPut
                          ? 'text-rose-400'
                          : 'text-slate-300'
                      }`}
                    >
                      {confidencePct}%
                    </span>
                  </div>
                  <div className="w-full bg-[#172033] rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isCall
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                          : isPut
                          ? 'bg-gradient-to-r from-rose-500 to-rose-400'
                          : 'bg-slate-500'
                      }`}
                      style={{ width: `${confidencePct}%` }}
                    />
                  </div>
                </div>

                {/* Footer: Win Rate & Explore hint */}
                <div className="pt-2 border-t border-[#182236] flex items-center justify-between text-[10px]">
                  <span className="text-slate-400 font-medium">Win Rate</span>
                  <span className="font-mono font-bold text-amber-400">{winRateDisplay}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Agent Detail Modal */}
      <AgentDetailModal
        isOpen={activeModalAgent !== null}
        onClose={() => setActiveModalAgent(null)}
        signal={activeModalAgent?.signal || null}
        metadata={activeModalAgent?.meta || null}
      />
    </div>
  );
};
