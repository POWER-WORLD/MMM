import React, { useEffect, useRef, useState } from 'react';
import {
  createChart,
  CandlestickSeries,
  IChartApi,
  CandlestickData,
  Time,
  ColorType,
  LineStyle,
} from 'lightweight-charts';
import { Candle, ActiveTrade } from '../types';
import {
  BarChart3,
  Clock,
  Zap,
  Maximize2,
  Minimize2,
  TrendingUp,
  Activity,
  Layers,
} from 'lucide-react';

interface CandleChartProps {
  candles: Candle[];
  currentPrice: number | null;
  candleIntervalSeconds: number;
  onIntervalChange: (seconds: number) => void;
  activeTrade?: ActiveTrade | null;
}

const TIMEFRAME_OPTIONS: Array<{ seconds: number; label: string }> = [
  { seconds: 5, label: '5s' },
  { seconds: 10, label: '10s' },
  { seconds: 15, label: '15s' },
  { seconds: 30, label: '30s' },
  { seconds: 60, label: '1m' },
];

export const CandleChart: React.FC<CandleChartProps> = ({
  candles,
  currentPrice,
  candleIntervalSeconds,
  onIntervalChange,
  activeTrade,
}) => {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartWrapperRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<any>(null);
  const priceLineRef = useRef<any>(null);
  const tradeLineRef = useRef<any>(null);
  const isFirstLoadRef = useRef<boolean>(true);

  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Initialize chart on mount
  useEffect(() => {
    if (!chartContainerRef.current) return;

    try {
      const container = chartContainerRef.current;
      const initialWidth = container.clientWidth || 300;
      const initialHeight = container.clientHeight || 300;

      const chart = createChart(container, {
        width: initialWidth,
        height: initialHeight,
        layout: {
          background: { type: ColorType.Solid, color: '#06080d' },
          textColor: '#8492a6',
          fontSize: 11,
          fontFamily: "'JetBrains Mono', monospace",
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
        },
        crosshair: {
          mode: 1,
          vertLine: {
            color: '#38bdf8',
            width: 1,
            style: LineStyle.Dotted,
            labelBackgroundColor: '#0f172a',
          },
          horzLine: {
            color: '#38bdf8',
            width: 1,
            style: LineStyle.Dotted,
            labelBackgroundColor: '#0f172a',
          },
        },
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.07)',
          timeVisible: true,
          secondsVisible: true,
          rightOffset: 6,
          barSpacing: 9,
          minBarSpacing: 3,
        },
        rightPriceScale: {
          borderColor: 'rgba(255, 255, 255, 0.07)',
          autoScale: true,
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
      });

      const candleOptions = {
        upColor: '#10b981',
        downColor: '#f43f5e',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#f43f5e',
      };

      let series: any = null;
      if (typeof (chart as any).addSeries === 'function' && CandlestickSeries) {
        series = (chart as any).addSeries(CandlestickSeries, candleOptions);
      } else if (typeof (chart as any).addCandlestickSeries === 'function') {
        series = (chart as any).addCandlestickSeries(candleOptions);
      }

      chartRef.current = chart;
      seriesRef.current = series;

      // Responsive ResizeObserver
      const resizeObserver = new ResizeObserver((entries) => {
        if (!entries || entries.length === 0 || !chartRef.current) return;
        const { width, height } = entries[0].contentRect;
        if (width > 0 && height > 0) {
          chartRef.current.applyOptions({ width, height });
        }
      });

      resizeObserver.observe(container);

      const handleWindowResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          const w = chartContainerRef.current.clientWidth;
          const h = chartContainerRef.current.clientHeight;
          if (w > 0 && h > 0) {
            chartRef.current.applyOptions({ width: w, height: h });
          }
        }
      };

      window.addEventListener('resize', handleWindowResize);

      return () => {
        window.removeEventListener('resize', handleWindowResize);
        resizeObserver.disconnect();
        chart.remove();
        chartRef.current = null;
        seriesRef.current = null;
        priceLineRef.current = null;
        tradeLineRef.current = null;
      };
    } catch (chartInitErr) {
      console.error('Failed to initialize Lightweight Charts:', chartInitErr);
    }
  }, []);

  // Update chart data whenever candles array changes
  useEffect(() => {
    if (!seriesRef.current || !candles || candles.length === 0) return;

    try {
      const seenTimes = new Set<number>();
      const formatted: CandlestickData<Time>[] = [];

      candles.forEach((c) => {
        const t = Math.floor(c.time);
        if (!seenTimes.has(t) && !isNaN(c.open) && !isNaN(c.close)) {
          seenTimes.add(t);
          formatted.push({
            time: t as Time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          });
        }
      });

      formatted.sort((a, b) => Number(a.time) - Number(b.time));

      if (formatted.length > 0) {
        seriesRef.current.setData(formatted);

        if (chartRef.current) {
          if (isFirstLoadRef.current) {
            chartRef.current.timeScale().fitContent();
            chartRef.current.timeScale().scrollToRealTime();
            isFirstLoadRef.current = false;
          } else {
            chartRef.current.timeScale().scrollToRealTime();
          }
        }
      }
    } catch (err) {
      console.warn('Chart setData notice:', err);
    }
  }, [candles]);

  // Live real-time tick update to candle & price line
  useEffect(() => {
    if (!seriesRef.current || currentPrice === null || isNaN(currentPrice)) return;

    try {
      // 1. Update or create the live horizontal price line
      if (!priceLineRef.current) {
        priceLineRef.current = seriesRef.current.createPriceLine({
          price: currentPrice,
          color: '#f59e0b',
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: 'SPOT',
        });
      } else {
        priceLineRef.current.applyOptions({ price: currentPrice });
      }

      // 2. Update active in-progress candle
      if (candles && candles.length > 0) {
        const last = candles[candles.length - 1];
        const lastTime = Math.floor(last.time);
        const liveCandle: CandlestickData<Time> = {
          time: lastTime as Time,
          open: last.open,
          high: Math.max(last.high, currentPrice),
          low: Math.min(last.low, currentPrice),
          close: currentPrice,
        };
        seriesRef.current.update(liveCandle);
      }
    } catch (tickErr) {
      console.debug('Chart live tick notice:', tickErr);
    }
  }, [currentPrice, candles]);

  // Active Trade Strike Price Line Overlay
  useEffect(() => {
    if (!seriesRef.current) return;

    try {
      if (activeTrade && activeTrade.result === 'PENDING') {
        const isCall = activeTrade.direction === 'CALL';
        const color = isCall ? '#10b981' : '#f43f5e';
        const label = `${isCall ? '▲ CALL STRIKE' : '▼ PUT STRIKE'}: $${activeTrade.entry_price.toFixed(2)}`;

        if (!tradeLineRef.current) {
          tradeLineRef.current = seriesRef.current.createPriceLine({
            price: activeTrade.entry_price,
            color,
            lineWidth: 2,
            lineStyle: LineStyle.Solid,
            axisLabelVisible: true,
            title: label,
          });
        } else {
          tradeLineRef.current.applyOptions({
            price: activeTrade.entry_price,
            color,
            title: label,
          });
        }
      } else if (tradeLineRef.current) {
        seriesRef.current.removePriceLine(tradeLineRef.current);
        tradeLineRef.current = null;
      }
    } catch (tradeLineErr) {
      console.debug('Trade line overlay notice:', tradeLineErr);
    }
  }, [activeTrade]);

  const toggleFullscreen = () => {
    if (!chartWrapperRef.current) return;
    if (!document.fullscreenElement) {
      chartWrapperRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  const latestCandle = candles && candles.length > 0 ? candles[candles.length - 1] : null;
  const candleDelta = latestCandle ? latestCandle.close - latestCandle.open : 0;
  const candleDeltaPct = latestCandle && latestCandle.open ? (candleDelta / latestCandle.open) * 100 : 0;

  return (
    <div
      ref={chartWrapperRef}
      className={`bg-[#06080d] flex flex-col w-full h-full min-h-0 relative select-none ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none h-screen' : ''
      }`}
    >
      {/* Chart Top Bar (Timeframes & OHLC) */}
      <div className="h-9 px-3 flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] bg-[#070a10] shrink-0">
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Timeframe selector */}
          <div className="flex items-center gap-0.5 bg-[#0e1320] p-0.5 rounded-lg border border-white/5">
            <Clock className="w-3 h-3 text-slate-400 ml-1 mr-0.5" />
            {TIMEFRAME_OPTIONS.map((opt) => {
              const isActive = candleIntervalSeconds === opt.seconds;
              return (
                <button
                  key={opt.seconds}
                  type="button"
                  onClick={() => onIntervalChange(opt.seconds)}
                  className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded transition-all ${
                    isActive
                      ? 'bg-amber-500 text-black shadow-sm'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>

          <div className="hidden sm:flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            <Zap className="w-2.5 h-2.5 animate-pulse" />
            <span>Real-Time Feed</span>
          </div>
        </div>

        {/* OHLC Banner */}
        {latestCandle && (
          <div className="hidden md:flex items-center gap-2.5 text-[11px] font-mono">
            <div>
              <span className="text-slate-500">O:</span>{' '}
              <span className="text-slate-300 font-bold">${latestCandle.open.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-500">H:</span>{' '}
              <span className="text-emerald-400 font-bold">${latestCandle.high.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-500">L:</span>{' '}
              <span className="text-rose-400 font-bold">${latestCandle.low.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-500">C:</span>{' '}
              <span className="text-white font-black">${latestCandle.close.toFixed(2)}</span>
            </div>
            <div
              className={`font-black text-[10px] px-1 rounded ${
                candleDelta >= 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
              }`}
            >
              {candleDelta >= 0 ? '+' : ''}
              {candleDelta.toFixed(2)} ({candleDeltaPct.toFixed(2)}%)
            </div>
          </div>
        )}

        {/* Fullscreen Button */}
        <button
          onClick={toggleFullscreen}
          type="button"
          title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Chart'}
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Lightweight Charts Canvas */}
      <div
        ref={chartContainerRef}
        className="flex-1 w-full h-full min-h-0 relative overflow-hidden"
      />
    </div>
  );
};
