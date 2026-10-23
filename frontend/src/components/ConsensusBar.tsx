import React from 'react';
import { ConsensusData } from '../types';
import { Scale, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';

interface ConsensusBarProps {
  consensus: ConsensusData | null;
  agentCount: number;
}

export const ConsensusBar: React.FC<ConsensusBarProps> = ({ consensus, agentCount }) => {
  const agreeingCount = consensus?.agreeing_agent_count || 0;
  const totalAgents = consensus?.total_agents || agentCount || 7;
  const isReached = consensus?.consensus_reached || false;
  const direction = consensus?.direction;
  const confidence = consensus ? Math.round(consensus.average_confidence * 100) : 0;
  const progressPercent = Math.min(Math.round((agreeingCount / totalAgents) * 100), 100);

  return (
    <div
      className={`border rounded-2xl p-3 sm:p-4 transition-all duration-300 shadow-xl ${
        isReached
          ? direction === 'CALL'
            ? 'bg-gradient-to-r from-emerald-950/40 via-[#0f1422] to-emerald-950/40 border-emerald-500/40 shadow-emerald-500/10'
            : 'bg-gradient-to-r from-rose-950/40 via-[#0f1422] to-rose-950/40 border-rose-500/40 shadow-rose-500/10'
          : 'bg-[#0f1422] border-[#1e2638]'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        {/* Title and Strategy info */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div
            className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center font-bold shrink-0 ${
              isReached
                ? direction === 'CALL'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            {isReached ? (
              direction === 'CALL' ? <ArrowUpCircle className="w-5 h-5 sm:w-6 sm:h-6" /> : <ArrowDownCircle className="w-5 h-5 sm:w-6 sm:h-6" />
            ) : (
              <Scale className="w-4 h-4 sm:w-5 sm:h-5" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-xs sm:text-sm font-bold text-white tracking-wide">
                Consensus Engine (7/7 Unanimous Rule)
              </h3>
              {isReached ? (
                <span className="text-[9px] sm:text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse">
                  TRIGGER ACTIVE
                </span>
              ) : (
                <span className="text-[9px] sm:text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                  SCANNING
                </span>
              )}
            </div>

            <p className="text-[11px] sm:text-xs text-slate-400 mt-0.5">
              {isReached ? (
                <span className="font-semibold text-emerald-400">
                  All 7 agents agreed on {direction}! Automatic 1-Minute trade triggered.
                </span>
              ) : (
                <span>
                  Requires all 7 agents to agree with &ge;55% confidence to execute 1-min trade.
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Meters */}
        <div className="flex items-center gap-4 sm:gap-6 justify-between sm:justify-end border-t sm:border-t-0 border-[#1a2336] pt-2 sm:pt-0">
          <div>
            <div className="text-[9px] sm:text-[10px] uppercase font-semibold text-slate-400">
              Agent Agreement
            </div>
            <div className="text-base sm:text-xl font-bold font-mono text-white">
              <span className={agreeingCount === 7 ? 'text-emerald-400' : 'text-amber-400'}>
                {agreeingCount}
              </span>
              <span className="text-slate-500 text-xs sm:text-sm"> / {totalAgents}</span>
            </div>
          </div>

          <div>
            <div className="text-[9px] sm:text-[10px] uppercase font-semibold text-slate-400">
              Avg Confidence
            </div>
            <div className="text-base sm:text-xl font-bold font-mono text-white">
              {confidence}%
            </div>
          </div>
        </div>
      </div>

      {/* Agreement Progress Bar */}
      <div className="w-full bg-[#161c2b] rounded-full h-2.5 overflow-hidden p-0.5 border border-[#1e2638]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            agreeingCount === 7
              ? 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-lg shadow-emerald-500/50'
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
