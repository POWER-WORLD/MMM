import { useEffect, useState, useRef, useCallback } from 'react';
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
import { soundEffects } from '../utils/soundEffects';

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
  auto_trade_enabled: true,
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
  const [pingMs, setPingMs] = useState<number>(18);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(soundEffects.getMuted());

  const socketRef = useRef<Socket | null>(null);
  const previousConsensusRef = useRef<boolean>(false);
  const previousTradeIdRef = useRef<string | null>(null);

  const toggleAudio = useCallback(() => {
    const nextState = !isAudioMuted;
    soundEffects.setMuted(nextState);
    setIsAudioMuted(nextState);
  }, [isAudioMuted]);

  // Update runtime configuration (stake, duration, timeframe, auto-trade)
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

  // Place a 1-click manual demo trade
  const placeManualTrade = async (
    direction: 'CALL' | 'PUT',
    amount?: number,
    duration?: number
  ): Promise<boolean> => {
    const tradeAmount = amount || config.trade_amount_usd;
    const tradeDuration = duration || config.trade_duration_seconds;

    soundEffects.playTradePlaced();

    try {
      // 1. Emit via socket
      if (socketRef.current && socketRef.current.connected) {
        socketRef.current.emit('place_trade', {
          direction,
          amount: tradeAmount,
          duration: tradeDuration,
        });
      }

      // 2. HTTP POST fallback
      const response = await fetch('/api/trades/place', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          direction,
          amount: tradeAmount,
          duration: tradeDuration,
        }),
      });

      if (response.ok) {
        const json = await response.json();
        if (json.trade) {
          setActiveTrade(json.trade);
        }
        return true;
      }
      return false;
    } catch (err) {
      console.warn('Failed to place manual trade:', err);
      return false;
    }
  };

  // Helper to safely parse candle timestamps
  const parseCandle = (c: any): Candle => {
    let t = c.time;
    if (t === undefined || t === null) {
      if (c.timestamp) {
        t =
          typeof c.timestamp === 'number'
            ? c.timestamp > 1e11
              ? Math.floor(c.timestamp / 1000)
              : c.timestamp
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

  // REST API snapshot fetcher
  const fetchRestState = async () => {
    const startTime = performance.now ? window.performance.now() : Date.now();
    try {
      const res = await fetch('/api/state');
      if (!res.ok) return;
      const data: PlatformState = await res.json();

      const elapsed = Math.round(
        (performance.now ? window.performance.now() : Date.now()) - startTime
      );
      setPingMs(Math.max(8, Math.min(elapsed, 999)));

      if (data.current_price !== null && data.current_price !== undefined) {
        setCurrentPrice((prev) => {
          if (prev !== null && prev !== data.current_price) {
            setPreviousPrice(prev);
            const dir = data.current_price > prev ? 'up' : 'down';
            setPriceFlash(dir);
            soundEffects.playPriceTick(dir);
          }
          return data.current_price;
        });
        setPriceTimestamp(data.price_timestamp || new Date().toISOString());
      }

      if (data.config) {
        setConfig((prev) => ({ ...prev, ...data.config }));
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
        if (data.consensus.consensus_reached && !previousConsensusRef.current) {
          soundEffects.playConsensusAlert();
        }
        previousConsensusRef.current = data.consensus.consensus_reached;
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
    // 1. Initial REST fetch
    fetchRestState();

    // 2. Periodic 1.5s fallback poll
    const pollInterval = setInterval(fetchRestState, 1500);

    // 3. Socket.IO connection
    const socket = io({
      transports: ['polling', 'websocket'],
      upgrade: true,
      reconnectionAttempts: 50,
      reconnectionDelay: 1000,
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);
      socket.emit('request_full_state');
    });

    socket.on('price_update', (data: { price: number; timestamp: string }) => {
      if (data && typeof data.price === 'number') {
        setCurrentPrice((prev) => {
          if (prev !== null && prev !== data.price) {
            setPreviousPrice(prev);
            const dir = data.price > prev ? 'up' : 'down';
            setPriceFlash(dir);
            soundEffects.playPriceTick(dir);
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
        if (consensusData.consensus_reached && !previousConsensusRef.current) {
          soundEffects.playConsensusAlert();
        }
        previousConsensusRef.current = consensusData.consensus_reached;
        setConsensus(consensusData);
      }
    });

    socket.on('trade_update', (trade: ActiveTrade) => {
      if (trade) {
        if (trade.result === 'PENDING') {
          setActiveTrade(trade);
          if (trade.trade_id !== previousTradeIdRef.current) {
            previousTradeIdRef.current = trade.trade_id;
            soundEffects.playTradePlaced();
          }
        } else {
          setActiveTrade(null);
          setRecentTrades((prev) => [
            trade,
            ...prev.filter((t) => t.trade_id !== trade.trade_id),
          ]);
          if (trade.result === 'WIN') {
            soundEffects.playTradeWon();
          } else if (trade.result === 'LOSS') {
            soundEffects.playTradeLost();
          }
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
        setConfig((prev) => ({ ...prev, ...newConfig }));
      }
    });

    socket.on('full_state', (state: PlatformState) => {
      if (state) {
        if (state.config) setConfig((prev) => ({ ...prev, ...state.config }));
        if (state.current_price) setCurrentPrice(state.current_price);
        if (state.price_timestamp) setPriceTimestamp(state.price_timestamp);
        if (state.agent_signals) setAgentSignals(state.agent_signals);
        if (state.consensus) {
          if (state.consensus.consensus_reached && !previousConsensusRef.current) {
            soundEffects.playConsensusAlert();
          }
          previousConsensusRef.current = state.consensus.consensus_reached;
          setConsensus(state.consensus);
        }
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

  // Clear flash animation after 500ms
  useEffect(() => {
    if (priceFlash) {
      const timer = setTimeout(() => setPriceFlash(null), 500);
      return () => clearTimeout(timer);
    }
  }, [priceFlash]);

  // Compute 24h High and Low from current candle buffer
  let sessionHigh = currentPrice || 0;
  let sessionLow = currentPrice || 0;
  if (candles.length > 0) {
    sessionHigh = Math.max(...candles.map((c) => c.high));
    sessionLow = Math.min(...candles.map((c) => c.low));
  }

  return {
    currentPrice,
    previousPrice,
    sessionHigh,
    sessionLow,
    priceTimestamp,
    priceFlash,
    candles,
    config,
    updateConfig,
    placeManualTrade,
    agentSignals,
    consensus,
    performance,
    activeTrade,
    recentTrades,
    isConnected,
    lastDataReceived,
    pingMs,
    isAudioMuted,
    toggleAudio,
    refetchState: fetchRestState,
  };
}
