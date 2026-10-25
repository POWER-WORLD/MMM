import React from 'react';
import { Keyboard, X } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SHORTCUTS = [
  { key: 'C', description: 'Instant 1-Click CALL ▲ Order' },
  { key: 'P', description: 'Instant 1-Click PUT ▼ Order' },
  { key: 'M', description: 'Toggle Sound Effects (Mute / Unmute)' },
  { key: '1', description: 'Switch to 1-Minute Candle Timeframe' },
  { key: '2', description: 'Switch to 2-Minute Candle Timeframe' },
  { key: '3', description: 'Switch to 3-Minute Candle Timeframe' },
  { key: '5', description: 'Switch to 5-Minute Candle Timeframe' },
  { key: 'R / Space', description: 'Force State Refresh from Backend' },
  { key: 'Esc', description: 'Close any active modal or dialog' },
];

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0e1320] border border-[#232f48] rounded-3xl w-full max-w-md p-5 sm:p-6 shadow-2xl relative my-auto animate-in fade-in zoom-in-95 duration-200">
        <button
          onClick={onClose}
          type="button"
          aria-label="Close shortcuts modal"
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white bg-[#141b2c] hover:bg-[#1d273e] rounded-xl border border-[#222d46] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5 pb-4 border-b border-[#1c263c]">
          <div className="w-10 h-10 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center font-bold">
            <Keyboard className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-black text-white tracking-tight">
              Trading Terminal Hotkeys
            </h3>
            <p className="text-xs text-slate-400">High-speed keyboard execution</p>
          </div>
        </div>

        <div className="space-y-2 text-xs font-mono">
          {SHORTCUTS.map((sc) => (
            <div
              key={sc.key}
              className="flex items-center justify-between p-2 rounded-xl bg-[#080b12] border border-[#1a2336]"
            >
              <span className="font-sans text-slate-300 font-semibold">{sc.description}</span>
              <kbd className="px-2.5 py-1 rounded-lg bg-[#172033] text-amber-400 font-bold border border-[#273656] shadow-sm">
                {sc.key}
              </kbd>
            </div>
          ))}
        </div>

        <div className="mt-5 pt-3 border-t border-[#1c263c] text-center">
          <button
            onClick={onClose}
            type="button"
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl text-xs transition-colors"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
};
