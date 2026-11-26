import { useId } from 'react';
import { getSparklineColor, TrendDirection } from '../utils/ecommerceLogic';

interface SparklineChartProps {
  series: number[];
  trend: TrendDirection;
  trendLabel: string;
}

function buildSmoothSparklinePath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return '';
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

  let path = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const cx = ((p0.x + p1.x) / 2).toFixed(1);
    path += ` C ${cx} ${p0.y.toFixed(1)}, ${cx} ${p1.y.toFixed(1)}, ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
  }
  return path;
}

export function SparklineChart({
  series,
  trend,
  trendLabel,
}: SparklineChartProps) {
  const gradId = useId();
  const strokeColor = getSparklineColor(trend);

  const values =
    series.length >= 2 ? series : [series[0] ?? 0, series[0] ?? 0];

  const width = 148;
  const height = 52;
  const padX = 6;
  const padY = 7;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;

  const minVal = Math.min(...values, 0);
  const maxVal = Math.max(...values, minVal + 1);
  const span = Math.max(1, maxVal - minVal);

  const coords = values.map((val, idx) => ({
    x: padX + (idx / Math.max(1, values.length - 1)) * innerW,
    y: padY + innerH - ((val - minVal) / span) * innerH,
  }));

  const linePath = buildSmoothSparklinePath(coords);
  const baseLine = (padY + innerH).toFixed(1);
  const areaPath = `${linePath} L ${coords[coords.length - 1].x.toFixed(1)} ${baseLine} L ${coords[0].x.toFixed(1)} ${baseLine} Z`;
  const lastPt = coords[coords.length - 1];

  return (
    <div className="sparkline-shell flex flex-col items-center">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[52px] w-[148px]"
        role="img"
        aria-label={`Evolução recente de vendas: ${trendLabel}`}
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.28" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gradId})`} />
        <path
          d={linePath}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.25"
          strokeLinecap="round"
        />
        <circle
          cx={lastPt.x}
          cy={lastPt.y}
          r="3.2"
          fill={strokeColor}
          stroke="#0B0F19"
          strokeWidth="1.2"
        />
      </svg>
      <span
        className="mt-0.5 text-[11px] font-medium"
        style={{ color: strokeColor }}
      >
        {trendLabel}
      </span>
    </div>
  );
}
