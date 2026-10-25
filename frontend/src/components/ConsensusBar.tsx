import React from 'react';
import { ConsensusData, AgentSignal } from '../types';
import { Scale, ArrowUpCircle, ArrowDownCircle, Zap, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface ConsensusBarProps {
  consensus: ConsensusData | null;
  signals?: AgentSignal[];
  agentCount?: number;
}

export const ConsensusBar: React.FC<ConsensusBarProps> = ({
  consensus,
  signals = [],
  agentCount = 7,
}) => {
  const agreeingCount = consensus?.agreeing_agent_count || 0;
  const totalAgents = consensus?.total_agents || agentCount || 7;
  const isReached = consensus?.consensus_reached || false;
  const direction = consensus?.direction;
  const confidence = consensus ? Math.round(consensus.average_confidence * 100) : 0;
  const progressPercent = Math.min(Math.round((agreeingCount / totalAgents) * 100), 100);

  return (
    <div
      className={`relative overflow-hidden rounded-3xl p-4 sm:p-5 transition-all duration-300 shadow-xl border ${
        isReached
          ? direction === 'CALL'
            ? 'bg-gradient-to-r from-emerald-950/70 via-[#0e1622] to-emerald-950/70 border-emerald-500/60 shadow-emerald-500/20 glow-emerald'
            : 'bg-gradient-to-r from-rose-950/70 via-[#0e1622] to-rose-950/70 border-rose-500/60 shadow-rose-500/20 glow-rose'
          : 'bg-[#0d121e]/90 border-[#1c273e]'
      }`}
    >
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Engine Status & Direction */}
        <div className="flex items-center gap-3.5">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold shrink-0 transition-all ${
              isReached
                ? direction === 'CALL'
                  ? 'bg-emerald-500/25 text-emerald-400 border border-emerald-500/40 shadow-lg shadow-emerald-500/30'
                  : 'bg-rose-500/25 text-rose-400 border border-rose-500/40 shadow-lg shadow-rose-500/30'
                : 'bg-[#151c2d] text-amber-400 border border-[#232f48]'
            }`}
          >
            {isReached ? (
              direction === 'CALL' ? (
                <ArrowUpCircle className="w-7 h-7 animate-bounce" />
              ) : (
                <ArrowDownCircle className="w-7 h-7 animate-bounce" />
              )
            ) : (
              <Scale className="w-6 h-6" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-sm sm:text-base font-extrabold text-white tracking-wide flex items-center gap-2">
                <span>7/7 Unanimous Consensus Engine</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  Fixed Time Trading
                </span>
              </h2>

              {isReached ? (
                <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500 text-black shadow-md shadow-emerald-500/40 animate-pulse">
                  ⚡ EXECUTION TRIGGERED
                </span>
              ) : (
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#172134] text-amber-400 border border-amber-500/20">
                  MONITORING INDICATORS
                </span>
              )}
            </div>

            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              {isReached ? (
                <span className="font-bold text-white">
                  All 7 independent technical agents vote{' '}
                  <strong
                    className={
                      direction === 'CALL' ? 'text-emerald-400' : 'text-rose-400'
                    }
                  >
                    {direction}
                  </strong>{' '}
                  with &ge;55% confidence! Trade placed on Olymp Demo.
                </span>
              ) : (
                <span className="text-slate-400">
                  Requires <strong>100% unanimous agreement (7/7)</strong> with &ge;55%
                  confidence to execute high-probability 1-minute contract.
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Center / Right: 7 Autonomous Agent Node Radar Badges */}
        <div className="flex flex-wrap items-center gap-3 sm:gap-6 justify-between lg:justify-end border-t lg:border-t-0 border-[#1a2438] pt-3 lg:pt-0">
          {/* Visual Node Radar */}
          <div className="flex items-center gap-1.5 sm:gap-2">
            {Array.from({ length: totalAgents }).map((_, idx) => {
              const sig = signals[idx];
              const isCall = sig?.direction === 'CALL';
              const isPut = sig?.direction === 'PUT';
              const isAgreed =
                direction &&
                ((direction === 'CALL' && isCall) || (direction === 'PUT' && isPut));

              return (
                <div
                  key={idx}
                  title={
                    sig
                      ? `${sig.agent_name.replace('Agent', '')}: ${sig.direction} (${Math.round(sig.confidence * 100)}%)`
                      : `Agent #${idx + 1}`
                  }
                  className={`w-7 h-7 sm:w-8 sm:h-8 rounded-xl flex items-center justify-center font-mono text-[11px] font-bold border transition-all duration-300 ${
                    isAgreed
                      ? isCall
                        ? 'bg-emerald-500/25 border-emerald-400 text-emerald-300 shadow-md shadow-emerald-500/30'
                        : 'bg-rose-500/25 border-rose-400 text-rose-300 shadow-md shadow-rose-500/30'
                      : isCall
                      ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
                      : isPut
                      ? 'bg-rose-950/40 border-rose-500/30 text-rose-400'
                      : 'bg-[#121826] border-[#222e46] text-slate-500'
                  }`}
                >
                  {sig ? (
                    isCall ? '▲' : isPut ? '▼' : '—'
                  ) : (
                    idx + 1
                  )}
                </div>
              );
            })}
          </div>

          {/* Agreement Metrics */}
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Unanimous Count
              </div>
              <div className="text-base sm:text-xl font-black font-mono">
                <span
                  className={
                    agreeingCount === 7
                      ? 'text-emerald-400'
                      : agreeingCount >= 4
                      ? 'text-amber-400'
                      : 'text-slate-300'
                  }
                >
                  {agreeingCount}
                </span>
                <span className="text-slate-500 text-xs sm:text-sm"> / {totalAgents}</span>
              </div>
            </div>

            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Avg Confidence
              </div>
              <div className="text-base sm:text-xl font-black font-mono text-white">
                {confidence}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Segmented Unanimous Agreement Progress Bar */}
      <div className="w-full bg-[#121827] rounded-full h-3 overflow-hidden p-0.5 border border-[#1e2a42] mt-3.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            agreeingCount === 7
              ? 'bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-400 shadow-lg shadow-emerald-500/50'
              : agreeingCount >= 4
              ? 'bg-gradient-to-r from-amber-500 to-amber-400'
              : 'bg-gradient-to-r from-slate-600 to-slate-500'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
};
