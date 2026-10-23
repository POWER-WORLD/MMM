export type TradeDirection = 'CALL' | 'PUT' | 'NEUTRAL';

export interface Candle {
  time: number;
  timestamp?: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface AgentSignal {
  agent_name: string;
  direction: TradeDirection;
  confidence: number;
  reasoning: string;
  indicator_values?: Record<string, any>;
  success_rate?: number;
}

export interface AgentStatistics {
  agent_name: string;
  agent_description?: string;
  total_predictions: number;
  correct_predictions: number;
  success_rate: number;
  total_call_predictions?: number;
  correct_call_predictions?: number;
  total_put_predictions?: number;
  correct_put_predictions?: number;
}

export interface ConsensusData {
  consensus_reached: boolean;
  direction: 'CALL' | 'PUT' | null;
  average_confidence: number;
  agreeing_agent_count: number;
  total_agents: number;
  timestamp: string;
}

export interface ActiveTrade {
  trade_id: string;
  direction: 'CALL' | 'PUT';
  entry_price: number;
  entry_time: string;
  exit_price: number | null;
  exit_time: string | null;
  duration_seconds: number;
  amount: number;
  result: 'PENDING' | 'WIN' | 'LOSS';
  profit_loss: number;
  payout_percentage: number;
}

export interface PerformanceStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  success_rate: number;
  total_profit_loss: number;
  current_balance: number;
  initial_balance: number;
  return_percentage: number;
  longest_win_streak: number;
  longest_loss_streak: number;
  current_streak?: {
    type: 'WIN' | 'LOSS' | 'NONE';
    count: number;
  };
  average_profit_per_trade?: number;
}

export interface RuntimeConfig {
  candle_interval_seconds: number;
  trade_duration_seconds: number;
  trade_amount_usd: number;
  payout_percentage: number;
  asset_symbol?: string;
}

export interface PlatformState {
  current_price: number | null;
  price_timestamp: string | null;
  candles: Candle[];
  config?: RuntimeConfig;
  agent_signals: AgentSignal[];
  consensus: ConsensusData | null;
  agent_statistics: AgentStatistics[];
  performance: PerformanceStats;
  recent_trades: ActiveTrade[];
  active_trade: ActiveTrade | null;
  current_balance: number;
}
