import React, { useState } from 'react';
import { AgentSignal, ConsensusData, AgentMetadata } from '../types';
import {
  Bot,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Scale,
  Sparkles,
  Info,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { AgentDetailModal } from './AgentDetailModal';
import { AGENT_REGISTRY } from './AgentsGrid';

interface AiConsensusPanelProps {
  consensus: ConsensusData | null;
  signals: AgentSignal[];
  isOpen: boolean;
  onToggle: () => void;
}

const CATEGORIES = ['All', 'Momentum', 'Trend', 'Volatility', 'Structural'] as const;

export const AiConsensusPanel: React.FC<AiConsensusPanelProps> = ({
  consensus,
  signals,
  isOpen,
  onToggle,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [activeModalAgent, setActiveModalAgent] = useState<{
    signal: AgentSignal;
    meta: AgentMetadata;
  } | null>(null);

  const agreeingCount = consensus?.agreeing_agent_count || 0;
  const totalAgents = consensus?.total_agents || 7;
  const isReached = consensus?.consensus_reached || false;
  const direction = consensus?.direction;
  const confidence = consensus ? Math.round(consensus.average_confidence * 100) : 0;
  const progressPercent = Math.min(Math.round((agreeingCount / totalAgents) * 100), 100);

  const filteredSignals = signals.filter((signal) => {
    if (selectedCategory === 'All') return true;
    const meta = AGENT_REGISTRY[signal.agent_name];
    return meta ? meta.category === selectedCategory : true;
  });

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        type="button"
        className="hidden lg:flex w-9 h-full border-r border-[rgba(255,255,255,0.07)] bg-[#080b12] hover:bg-[#0d121c] flex-col items-center justify-between py-4 text-slate-400 hover:text-white transition-colors select-none z-20 shrink-0"
        title="Expand 7-Agent AI Consensus Radar"
      >
        <div className="flex flex-col items-center gap-2">
          <Bot className="w-4 h-4 text-amber-400" />
          <span className="[writing-mode:vertical-rl] rotate-180 text-[10px] font-black uppercase tracking-wider text-slate-300">
            7 AI AGENTS RADAR
          </span>
        </div>
        <div className="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center font-mono text-[10px] font-bold text-amber-400 border border-white/10">
          {agreeingCount}
        </div>
        <ChevronRight className="w-4 h-4 text-slate-400" />
      </button>
    );
  }

  return (
    <aside className="w-full lg:w-[310px] xl:w-[330px] border-r border-[rgba(255,255,255,0.07)] bg-[#080c14] flex flex-col h-full overflow-hidden select-none shrink-0 z-20">
      {/* Panel Header */}
      <div className="p-3 border-b border-[rgba(255,255,255,0.07)] flex items-center justify-between bg-[#0a0e18]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-400">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-black text-white tracking-wide leading-tight">
              AI Consensus Radar
            </h3>
            <span className="text-[9px] text-slate-400 font-mono">
              7-Agent Unanimous Protocol
            </span>
          </div>
        </div>

        <button
          onClick={onToggle}
          type="button"
          title="Collapse Panel"
          className="hidden lg:flex p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Consensus Engine Gauge Card */}
      <div className="p-3 border-b border-[rgba(255,255,255,0.07)] bg-[#0b101c]/80">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            Agreement Consensus
          </span>
          {isReached ? (
            <span className="text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500 text-black shadow-md shadow-emerald-500/30 animate-pulse font-mono">
              TRIGGERED
            </span>
          ) : (
            <span className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/5 text-slate-400 border border-white/10 font-mono">
              SCANNING
            </span>
          )}
        </div>

        {/* Big Agreement Meter */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-baseline gap-1">
            <span
              className={`text-2xl font-black font-mono leading-none ${
                agreeingCount === 7
                  ? 'text-emerald-400'
                  : agreeingCount >= 4
                  ? 'text-amber-400'
                  : 'text-white'
              }`}
            >
              {agreeingCount}
            </span>
            <span className="text-slate-500 text-xs font-mono font-bold">/ {totalAgents} Agents</span>
          </div>

          <div className="text-right">
            <span className="text-[9px] uppercase font-bold text-slate-400 block leading-none">
              Confidence
            </span>
            <span className="text-sm font-black font-mono text-white leading-tight">
              {confidence}%
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-[#121826] rounded-full h-2 overflow-hidden border border-white/5">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              agreeingCount === 7
                ? 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-md shadow-emerald-500/50'
                : agreeingCount >= 4
                ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                : 'bg-slate-600'
            }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* 7 Interactive Node Bullets */}
        <div className="flex items-center justify-between gap-1 mt-2.5 pt-2 border-t border-white/5">
          {Array.from({ length: totalAgents }).map((_, idx) => {
            const sig = signals[idx];
            const isCall = sig?.direction === 'CALL';
            const isPut = sig?.direction === 'PUT';
            return (
              <div
                key={idx}
                title={
                  sig
                    ? `${sig.agent_name.replace('Agent', '')}: ${sig.direction}`
                    : `Agent #${idx + 1}`
                }
                className={`w-6 h-6 rounded-lg flex items-center justify-center font-mono text-[10px] font-bold border transition-all ${
                  isCall
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : isPut
                    ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                    : 'bg-[#121826] text-slate-500 border-white/5'
                }`}
              >
                {isCall ? '▲' : isPut ? '▼' : '—'}
              </div>
            );
          })}
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div className="p-2 border-b border-[rgba(255,255,255,0.07)] flex items-center gap-1 overflow-x-auto bg-[#090d16]">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setSelectedCategory(cat)}
            className={`text-[10px] font-bold px-2 py-0.5 rounded-md transition-all whitespace-nowrap ${
              selectedCategory === cat
                ? 'bg-amber-500 text-black shadow-sm font-black'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Stream of 7 Technical Agents */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {filteredSignals.map((signal) => {
          const meta = AGENT_REGISTRY[signal.agent_name] || {
            title: signal.agent_name.replace('Agent', ''),
            subtitle: 'Indicator',
            tag: 'Signal',
            category: 'Trend',
            description: '',
            formula: '',
            thresholds: '',
            id: signal.agent_name,
          };

          const isCall = signal.direction === 'CALL';
          const isPut = signal.direction === 'PUT';
          const confidencePct = Math.round(signal.confidence * 100);

          let winRateDisplay = '—';
          if (signal.success_rate !== undefined && signal.success_rate !== null) {
            const rawRate = Number(signal.success_rate);
            const normalizedRate = rawRate > 1.0 ? rawRate : rawRate * 100;
            winRateDisplay = `${normalizedRate.toFixed(0)}%`;
          }

          return (
            <div
              key={signal.agent_name}
              onClick={() => setActiveModalAgent({ signal, meta: meta as AgentMetadata })}
              className={`p-2.5 rounded-xl border transition-all cursor-pointer hover:border-amber-400/40 select-none ${
                isCall
                  ? 'bg-gradient-to-r from-emerald-950/20 to-[#0e1422] border-emerald-500/25 hover:border-emerald-400'
                  : isPut
                  ? 'bg-gradient-to-r from-rose-950/20 to-[#0e1422] border-rose-500/25 hover:border-rose-400'
                  : 'bg-[#0d121e] border-white/5'
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[8px] font-mono uppercase font-bold px-1.5 py-0.2 rounded bg-white/5 text-slate-400 border border-white/5">
                  {meta.tag}
                </span>

                <div
                  className={`flex items-center gap-0.5 text-[9px] font-mono font-black px-1.5 py-0.5 rounded ${
                    isCall
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : isPut
                      ? 'bg-rose-500/20 text-rose-400'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isCall && <ArrowUpRight className="w-2.5 h-2.5" />}
                  {isPut && <ArrowDownRight className="w-2.5 h-2.5" />}
                  <span>{signal.direction}</span>
                </div>
              </div>

              <div className="flex items-baseline justify-between">
                <h4 className="text-xs font-black text-white truncate">{meta.title}</h4>
                <span className="text-[10px] font-mono font-bold text-amber-400">
                  {winRateDisplay} WR
                </span>
              </div>

              {/* Confidence Micro-Bar */}
              <div className="mt-1.5">
                <div className="flex items-center justify-between text-[9px] font-mono text-slate-400 mb-0.5">
                  <span>Confidence</span>
                  <span
                    className={
                      isCall ? 'text-emerald-400 font-bold' : isPut ? 'text-rose-400 font-bold' : 'text-slate-300'
                    }
                  >
                    {confidencePct}%
                  </span>
                </div>
                <div className="w-full bg-[#141b2c] rounded-full h-1 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isCall ? 'bg-emerald-400' : isPut ? 'bg-rose-400' : 'bg-slate-500'
                    }`}
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Agent Detail Modal */}
      <AgentDetailModal
        isOpen={activeModalAgent !== null}
        onClose={() => setActiveModalAgent(null)}
        signal={activeModalAgent?.signal || null}
        metadata={activeModalAgent?.meta || null}
      />
    </aside>
  );
};
