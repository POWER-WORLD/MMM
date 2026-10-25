import React from 'react';
import { NavigationTab } from '../types';
import {
  BarChart2,
  Bot,
  TrendingUp,
  History,
  SlidersHorizontal,
} from 'lucide-react';

interface MobileNavigationProps {
  currentTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  onOpenBrokerConfig: () => void;
  activeTradeCount?: number;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  currentTab,
  onTabChange,
  onOpenBrokerConfig,
  activeTradeCount = 0,
}) => {
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#090d16]/95 backdrop-blur-md border-t border-[#1b253b] px-3 py-2 flex items-center justify-around shadow-2xl">
      <button
        type="button"
        onClick={() => onTabChange('chart')}
        className={`flex flex-col items-center gap-1 transition-colors relative ${
          currentTab === 'chart' ? 'text-amber-400' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <BarChart2 className="w-5 h-5" />
        <span className="text-[10px] font-bold">Chart & Trade</span>
        {activeTradeCount > 0 && (
          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        )}
      </button>

      <button
        type="button"
        onClick={() => onTabChange('agents')}
        className={`flex flex-col items-center gap-1 transition-colors ${
          currentTab === 'agents' ? 'text-amber-400' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <Bot className="w-5 h-5" />
        <span className="text-[10px] font-bold">7 Agents</span>
      </button>

      <button
        type="button"
        onClick={() => onTabChange('analytics')}
        className={`flex flex-col items-center gap-1 transition-colors ${
          currentTab === 'analytics' ? 'text-amber-400' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <TrendingUp className="w-5 h-5" />
        <span className="text-[10px] font-bold">Analytics</span>
      </button>

      <button
        type="button"
        onClick={() => onTabChange('history')}
        className={`flex flex-col items-center gap-1 transition-colors ${
          currentTab === 'history' ? 'text-amber-400' : 'text-slate-400 hover:text-slate-200'
        }`}
      >
        <History className="w-5 h-5" />
        <span className="text-[10px] font-bold">History</span>
      </button>

      <button
        type="button"
        onClick={onOpenBrokerConfig}
        className="flex flex-col items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors"
      >
        <SlidersHorizontal className="w-5 h-5" />
        <span className="text-[10px] font-bold">Broker</span>
      </button>
    </nav>
  );
};
