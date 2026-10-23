import React, { useEffect, useRef } from 'react';
import {
  createChart,
  CandlestickSeries,
  IChartApi,
  CandlestickData,
  Time,
  ColorType,
  LineStyle,
} from 'lightweight-charts';
import { Candle } from '../types';
import { BarChart3, Clock, Zap } from 'lucide-react';

interface CandleChartProps {
  candles: Candle[];
  currentPrice: number | null;
  candleIntervalSeconds: number;
  onIntervalChange: (seconds: number) => void;
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
}) => {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<any>(null);
  const priceLineRef = useRef<any>(null);
  const isFirstLoadRef = useRef<boolean>(true);

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
          background: { type: ColorType.Solid, color: '#0d121c' },
          textColor: '#94a3b8',
          fontSize: 11,
          fontFamily: "'Inter', sans-serif",
        },
        grid: {
          vertLines: { color: '#161e30' },
          horzLines: { color: '#161e30' },
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
          borderColor: '#1e2638',
          timeVisible: true,
          secondsVisible: true,
          rightOffset: 5,
          barSpacing: 8,
          minBarSpacing: 3,
        },
        rightPriceScale: {
          borderColor: '#1e2638',
          autoScale: true,
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
      });

      const seriesOptions = {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      };

      let series: any = null;
      if (typeof (chart as any).addSeries === 'function' && CandlestickSeries) {
        series = (chart as any).addSeries(CandlestickSeries, seriesOptions);
      } else if (typeof (chart as any).addCandlestickSeries === 'function') {
        series = (chart as any).addCandlestickSeries(seriesOptions);
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
      };
    } catch (chartInitErr) {
      console.error('Failed to initialize Lightweight Charts:', chartInitErr);
    }
  }, []);

  // Update chart data whenever candle array changes
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

      // 2. Update the active in-progress candle so user sees real-time price action
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

  const latestCandle = candles && candles.length > 0 ? candles[candles.length - 1] : null;

  return (
    <div className="bg-[#0f1422] border border-[#1e2638] rounded-2xl p-2.5 sm:p-3.5 shadow-xl flex flex-col h-[380px] sm:h-[440px] md:h-[500px] lg:h-[540px] xl:h-[580px] 2xl:h-[640px] w-full min-w-0">
      {/* Chart Top Controls & Timeframe Selector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 pb-2.5 border-b border-[#182030] mb-2">
        {/* Asset & Dynamic Timeframe Controls */}
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <BarChart3 className="w-4 h-4 text-amber-400 shrink-0" />
            <h2 className="text-xs sm:text-sm font-bold text-white tracking-wide truncate">
              Gold (XAU/USD)
            </h2>
          </div>

          {/* Timeframe Selector Pill Group */}
          <div className="flex items-center gap-1 bg-[#121826] p-0.5 rounded-lg border border-[#20293d]">
            <Clock className="w-3 h-3 text-slate-400 ml-1.5 mr-0.5" />
            {TIMEFRAME_OPTIONS.map((opt) => {
              const isActive = candleIntervalSeconds === opt.seconds;
              return (
                <button
                  key={opt.seconds}
                  type="button"
                  onClick={() => onIntervalChange(opt.seconds)}
                  className={`text-[10px] sm:text-[11px] font-bold px-2 py-0.5 rounded-md transition-all duration-150 ${
                    isActive
                      ? 'bg-amber-500 text-black shadow-md shadow-amber-500/30'
                      : 'text-slate-400 hover:text-white hover:bg-[#1a2336]'
                  }`}
                  title={`Switch to ${opt.label} candle timeframe`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>

          <div className="hidden md:flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            <Zap className="w-3 h-3 animate-pulse" />
            <span>1s Streaming</span>
          </div>
        </div>

        {/* Live Candle OHLC Indicators */}
        {latestCandle && (
          <div className="flex items-center gap-2 sm:gap-3.5 text-[11px] sm:text-xs font-mono ml-auto">
            <div>
              <span className="text-slate-500">O:</span>{' '}
              <span className="text-slate-300 font-semibold">${latestCandle.open.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-500">H:</span>{' '}
              <span className="text-emerald-400 font-semibold">${latestCandle.high.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-500">L:</span>{' '}
              <span className="text-rose-400 font-semibold">${latestCandle.low.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-500">C:</span>{' '}
              <span className="text-white font-bold">${latestCandle.close.toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Lightweight Charts Canvas Container */}
      <div ref={chartContainerRef} className="flex-1 w-full min-h-0 relative overflow-hidden" />
    </div>
  );
};
