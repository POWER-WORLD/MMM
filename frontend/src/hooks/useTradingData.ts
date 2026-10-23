import { useEffect, useState, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import {
  PlatformState,
  Candle,
  AgentSignal,
  ConsensusData,
  ActiveTrade,
  PerformanceStats,
  RuntimeConfig,
} from '../types';

const INITIAL_PERFORMANCE: PerformanceStats = {
  total_trades: 0,
  winning_trades: 0,
  losing_trades: 0,
  success_rate: 0,
  total_profit_loss: 0,
  current_balance: 10000,
  initial_balance: 10000,
  return_percentage: 0,
  longest_win_streak: 0,
  longest_loss_streak: 0,
};

const DEFAULT_CONFIG: RuntimeConfig = {
  candle_interval_seconds: 10,
  trade_duration_seconds: 60,
  trade_amount_usd: 1.0,
  payout_percentage: 0.82,
  asset_symbol: 'XAU/USD (Spot Gold)',
};

export function useTradingData() {
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [previousPrice, setPreviousPrice] = useState<number | null>(null);
  const [priceTimestamp, setPriceTimestamp] = useState<string | null>(null);
  const [priceFlash, setPriceFlash] = useState<'up' | 'down' | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [config, setConfig] = useState<RuntimeConfig>(DEFAULT_CONFIG);
  const [agentSignals, setAgentSignals] = useState<AgentSignal[]>([]);
  const [consensus, setConsensus] = useState<ConsensusData | null>(null);
  const [performance, setPerformance] = useState<PerformanceStats>(INITIAL_PERFORMANCE);
  const [activeTrade, setActiveTrade] = useState<ActiveTrade | null>(null);
  const [recentTrades, setRecentTrades] = useState<ActiveTrade[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastDataReceived, setLastDataReceived] = useState<Date>(new Date());

  const socketRef = useRef<Socket | null>(null);

  const updateConfig = async (updates: Partial<RuntimeConfig>) => {
    try {
      setConfig((prev) => ({ ...prev, ...updates }));
      if (socketRef.current && socketRef.current.connected) {
        socketRef.current.emit('update_config', updates);
      }
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (response.ok) {
        const json = await response.json();
        if (json.config) {
          setConfig(json.config);
        }
      }
    } catch (err) {
      console.warn('Failed to update config:', err);
    }
  };

  // Helper to safely parse candle timestamps
  const parseCandle = (c: any): Candle => {
    let t = c.time;
    if (t === undefined || t === null) {
      if (c.timestamp) {
        t = typeof c.timestamp === 'number'
          ? (c.timestamp > 1e11 ? Math.floor(c.timestamp / 1000) : c.timestamp)
          : Math.floor(new Date(c.timestamp).getTime() / 1000);
      } else {
        t = Math.floor(Date.now() / 1000);
      }
    }
    return {
      time: Number(t),
      open: Number(c.open || c.close || 0),
      high: Number(c.high || c.close || 0),
      low: Number(c.low || c.close || 0),
      close: Number(c.close || 0),
      volume: Number(c.volume || 0),
    };
  };

  // REST API fetcher
  const fetchRestState = async () => {
    try {
      const res = await fetch('/api/state');
      if (!res.ok) return;
      const data: PlatformState = await res.json();

      if (data.current_price !== null && data.current_price !== undefined) {
        setCurrentPrice((prev) => {
          if (prev !== null && prev !== data.current_price) {
            setPreviousPrice(prev);
            setPriceFlash(data.current_price > prev ? 'up' : 'down');
          }
          return data.current_price;
        });
        setPriceTimestamp(data.price_timestamp || new Date().toISOString());
      }

      if (data.config) {
        setConfig(data.config);
      }

      if (Array.isArray(data.candles) && data.candles.length > 0) {
        setCandles((prevCandles) => {
          const map = new Map<number, Candle>();
          prevCandles.forEach((c) => map.set(c.time, c));
          data.candles.forEach((c) => {
            const parsed = parseCandle(c);
            map.set(parsed.time, parsed);
          });
          return Array.from(map.values()).sort((a, b) => a.time - b.time);
        });
      }

      if (Array.isArray(data.agent_signals) && data.agent_signals.length > 0) {
        setAgentSignals(data.agent_signals);
      }

      if (data.consensus) {
        setConsensus(data.consensus);
      }

      if (data.performance) {
        setPerformance(data.performance);
      }

      if (data.active_trade !== undefined) {
        setActiveTrade(data.active_trade);
      }

      if (Array.isArray(data.recent_trades)) {
        setRecentTrades(data.recent_trades);
      }

      setIsConnected(true);
      setLastDataReceived(new Date());
    } catch (err) {
      console.warn('REST state polling notice:', err);
    }
  };

  useEffect(() => {
    // 1. Initial REST fetch immediately
    fetchRestState();

    // 2. Continuous 1.5s REST fallback poll
    const pollInterval = setInterval(fetchRestState, 1500);

    // 3. Setup Socket.IO connection with polling-first transport
    const socket = io({
      transports: ['polling', 'websocket'],
      upgrade: true,
      reconnectionAttempts: 30,
      reconnectionDelay: 1000,
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);
      socket.emit('request_full_state');
    });

    socket.on('disconnect', () => {
      // Don't set isConnected false immediately if REST is still responding
    });

    socket.on('price_update', (data: { price: number; timestamp: string }) => {
      if (data && typeof data.price === 'number') {
        setCurrentPrice((prev) => {
          if (prev !== null && prev !== data.price) {
            setPreviousPrice(prev);
            setPriceFlash(data.price > prev ? 'up' : 'down');
          }
          return data.price;
        });
        setPriceTimestamp(data.timestamp);
        setLastDataReceived(new Date());
      }
    });

    socket.on('candle_update', (rawCandle: any) => {
      const parsed = parseCandle(rawCandle);
      setCandles((prev) => {
        const next = [...prev];
        const idx = next.findIndex((c) => c.time === parsed.time);
        if (idx >= 0) {
          next[idx] = parsed;
        } else {
          next.push(parsed);
        }
        return next.sort((a, b) => a.time - b.time);
      });
      setLastDataReceived(new Date());
    });

    socket.on('agent_signals', (signals: AgentSignal[]) => {
      if (Array.isArray(signals)) {
        setAgentSignals(signals);
      }
    });

    socket.on('consensus_update', (consensusData: ConsensusData) => {
      if (consensusData) {
        setConsensus(consensusData);
      }
    });

    socket.on('trade_update', (trade: ActiveTrade) => {
      if (trade) {
        if (trade.result === 'PENDING') {
          setActiveTrade(trade);
        } else {
          setActiveTrade(null);
          setRecentTrades((prev) => [trade, ...prev.filter((t) => t.trade_id !== trade.trade_id)]);
        }
      }
    });

    socket.on('performance_update', (stats: PerformanceStats) => {
      if (stats) {
        setPerformance(stats);
      }
    });

    socket.on('config_update', (newConfig: RuntimeConfig) => {
      if (newConfig) {
        setConfig(newConfig);
      }
    });

    socket.on('full_state', (state: PlatformState) => {
      if (state) {
        if (state.config) setConfig(state.config);
        if (state.current_price) setCurrentPrice(state.current_price);
        if (state.price_timestamp) setPriceTimestamp(state.price_timestamp);
        if (state.agent_signals) setAgentSignals(state.agent_signals);
        if (state.consensus) setConsensus(state.consensus);
        if (state.performance) setPerformance(state.performance);
        if (state.recent_trades) setRecentTrades(state.recent_trades);
        if (state.active_trade !== undefined) setActiveTrade(state.active_trade);
        if (Array.isArray(state.candles)) {
          setCandles(state.candles.map(parseCandle).sort((a, b) => a.time - b.time));
        }
      }
    });

    return () => {
      clearInterval(pollInterval);
      socket.disconnect();
    };
  }, []);

  // Clear flash animation after 600ms
  useEffect(() => {
    if (priceFlash) {
      const timer = setTimeout(() => setPriceFlash(null), 600);
      return () => clearTimeout(timer);
    }
  }, [priceFlash]);

  return {
    currentPrice,
    previousPrice,
    priceTimestamp,
    priceFlash,
    candles,
    config,
    updateConfig,
    agentSignals,
    consensus,
    performance,
    activeTrade,
    recentTrades,
    isConnected,
    lastDataReceived,
    refetchState: fetchRestState,
  };
}
