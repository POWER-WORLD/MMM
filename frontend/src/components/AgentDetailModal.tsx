import React from 'react';
import { AgentSignal, AgentMetadata } from '../types';
import { X, Bot, Activity, Brain, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

interface AgentDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  signal: AgentSignal | null;
  metadata: AgentMetadata | null;
}

export const AgentDetailModal: React.FC<AgentDetailModalProps> = ({
  isOpen,
  onClose,
  signal,
  metadata,
}) => {
  if (!isOpen || !signal || !metadata) return null;

  const isCall = signal.direction === 'CALL';
  const isPut = signal.direction === 'PUT';
  const confidencePct = Math.round(signal.confidence * 100);

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 overflow-y-auto">
      <div className="bg-[#0e1320] border border-[#232f48] rounded-3xl w-full max-w-xl p-5 sm:p-6 shadow-2xl relative my-auto animate-in fade-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          type="button"
          aria-label="Close details"
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white bg-[#141b2c] hover:bg-[#1d273e] rounded-xl border border-[#222d46] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 mb-5 pb-4 border-b border-[#1c263c]">
          <div
            className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold shrink-0 ${
              isCall
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : isPut
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-slate-800 text-slate-300 border border-slate-700'
            }`}
          >
            <Bot className="w-6 h-6" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                {metadata.title}
              </h3>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                {metadata.category}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">{metadata.subtitle}</p>
          </div>
        </div>

        {/* Live Recommendation Badge & Confidence */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-[#121827] border border-[#1e283e] rounded-2xl p-3 flex flex-col justify-between">
            <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              Signal Output
            </span>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`text-lg font-black font-mono px-3 py-1 rounded-xl ${
                  isCall
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : isPut
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-slate-800 text-slate-300'
                }`}
              >
                {signal.direction}
              </span>
            </div>
          </div>

          <div className="bg-[#121827] border border-[#1e283e] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              <span>Confidence</span>
              <span
                className={`font-mono font-bold text-sm ${
                  isCall ? 'text-emerald-400' : isPut ? 'text-rose-400' : 'text-slate-300'
                }`}
              >
                {confidencePct}%
              </span>
            </div>
            <div className="w-full bg-[#1b2336] rounded-full h-2 overflow-hidden mt-2">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  isCall ? 'bg-emerald-500' : isPut ? 'bg-rose-500' : 'bg-slate-400'
                }`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Real-time Telemetry & Indicator Metrics */}
        {signal.indicator_values && Object.keys(signal.indicator_values).length > 0 && (
          <div className="bg-[#121827] border border-[#1e283e] rounded-2xl p-3.5 mb-4">
            <div className="flex items-center gap-2 text-xs font-bold text-white mb-2">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>Real-Time Indicator Telemetry</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-xs">
              {Object.entries(signal.indicator_values).map(([k, v]) => (
                <div
                  key={k}
                  className="bg-[#0b0e17] px-2.5 py-1.5 rounded-xl border border-[#1c2438] flex flex-col justify-between"
                >
                  <span className="text-[10px] text-slate-400 uppercase tracking-tight truncate">
                    {k.replace(/_/g, ' ')}
                  </span>
                  <span className="text-white font-bold text-sm mt-0.5 truncate">
                    {typeof v === 'number' ? v.toFixed(2) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agent Reasoning */}
        <div className="bg-[#121827] border border-[#1e283e] rounded-2xl p-3.5 mb-4">
          <div className="flex items-center gap-2 text-xs font-bold text-white mb-1.5">
            <Brain className="w-3.5 h-3.5 text-purple-400" />
            <span>AI Algorithmic Rationale</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {signal.reasoning || 'Analyzing continuous market price series against mathematical indicator parameters.'}
          </p>
        </div>

        {/* Mathematical Model & Thresholds */}
        <div className="bg-[#0b0e17] border border-[#1a2337] rounded-2xl p-3.5 space-y-2 text-xs">
          <div className="flex items-center gap-2 text-amber-400 font-bold">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Mathematical Formula & Parameters</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            {metadata.description}
          </p>
          <div className="bg-[#07090f] p-2 rounded-lg font-mono text-[11px] text-emerald-300 border border-[#172033]">
            {metadata.formula}
          </div>
          <div className="text-[11px] text-slate-400">
            <strong>Decision Boundary:</strong> {metadata.thresholds}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-5 pt-3 border-t border-[#1c263c] flex items-center justify-between text-xs text-slate-400">
          <span>7/7 Unanimous Engine Participant</span>
          <button
            onClick={onClose}
            type="button"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
