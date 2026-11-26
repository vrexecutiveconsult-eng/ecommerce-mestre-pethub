import { useState } from 'react';
import { HourlyPoint } from '../utils/ecommerceLogic';

interface HourlyBattleChartProps {
  data: HourlyPoint[];
}

function buildSmoothPath(points: { x: number; y: number }[]): string {
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

export function HourlyBattleChart({ data }: HourlyBattleChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const width = 880;
  const height = 270;
  const padL = 42;
  const padR = 18;
  const padT = 20;
  const padB = 34;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;

  const rawMax = Math.max(
    4,
    ...data.map((d) => Math.max(d.meuAnuncio, d.concorrente))
  );
  const maxVal = Math.ceil(rawMax / 4) * 4;

  const toCoords = (vals: number[]) =>
    vals.map((val, idx) => ({
      x: padL + (idx / Math.max(1, vals.length - 1)) * innerW,
      y: padT + innerH - (val / maxVal) * innerH,
    }));

  const meuCoords = toCoords(data.map((d) => d.meuAnuncio));
  const concCoords = toCoords(data.map((d) => d.concorrente));

  const meuLine = buildSmoothPath(meuCoords);
  const concLine = buildSmoothPath(concCoords);
  const baseLineY = (padT + innerH).toFixed(1);

  const meuArea = `${meuLine} L ${meuCoords[meuCoords.length - 1].x.toFixed(1)} ${baseLineY} L ${meuCoords[0].x.toFixed(1)} ${baseLineY} Z`;
  const concArea = `${concLine} L ${concCoords[concCoords.length - 1].x.toFixed(1)} ${baseLineY} L ${concCoords[0].x.toFixed(1)} ${baseLineY} Z`;

  const gridTicks = [0, 0.25, 0.5, 0.75, 1];
  const activePoint = hoveredIdx !== null ? data[hoveredIdx] : null;

  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-lg font-semibold text-slate-100">
            Batalha de Horário de Pico (00h–23h)
          </h2>
          <p className="text-sm text-slate-400">
            Comparativo horário de unidades convertidas entre seus anúncios e a concorrência
          </p>
        </div>
        <div className="flex items-center gap-6 text-xs font-medium text-slate-300">
          <span className="flex items-center gap-2 whitespace-nowrap">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-sky-400" />
            Meu Anúncio
          </span>
          <span className="flex items-center gap-2 whitespace-nowrap">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-amber-400" />
            Concorrente
          </span>
        </div>
      </div>

      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full min-w-[580px]"
          role="img"
          aria-label="Gráfico de vendas por hora entre Meu Anúncio e Concorrente"
        >
          <defs>
            <linearGradient id="meuGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.34" />
              <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.02" />
            </linearGradient>
            <linearGradient id="concGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.26" />
              <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {gridTicks.map((ratio) => {
            const y = padT + innerH * (1 - ratio);
            const label = Math.round(maxVal * ratio);
            return (
              <g key={ratio}>
                <line
                  x1={padL}
                  y1={y}
                  x2={width - padR}
                  y2={y}
                  stroke="#334155"
                  strokeOpacity="0.45"
                  strokeDasharray="3 4"
                />
                <text
                  x={padL - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-slate-400 text-[11px] font-tabular"
                >
                  {label}
                </text>
              </g>
            );
          })}

          <path d={concArea} fill="url(#concGrad)" />
          <path d={meuArea} fill="url(#meuGrad)" />

          <path
            d={concLine}
            fill="none"
            stroke="#F59E0B"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <path
            d={meuLine}
            fill="none"
            stroke="#38BDF8"
            strokeWidth="2.75"
            strokeLinecap="round"
          />

          {data.map((point, idx) => {
            const x = meuCoords[idx].x;
            const isActive = hoveredIdx === idx;
            return (
              <g key={point.hora}>
                {idx % 3 === 0 && (
                  <text
                    x={x}
                    y={height - 10}
                    textAnchor="middle"
                    className="fill-slate-400 text-[11px] font-tabular"
                  >
                    {point.hora}
                  </text>
                )}
                {isActive && (
                  <>
                    <line
                      x1={x}
                      y1={padT}
                      x2={x}
                      y2={padT + innerH}
                      stroke="#64748B"
                      strokeDasharray="2 3"
                    />
                    <circle
                      cx={x}
                      cy={concCoords[idx].y}
                      r="4.5"
                      fill="#F59E0B"
                      stroke="#0B0F19"
                      strokeWidth="1.5"
                    />
                    <circle
                      cx={x}
                      cy={meuCoords[idx].y}
                      r="5"
                      fill="#38BDF8"
                      stroke="#0B0F19"
                      strokeWidth="1.5"
                    />
                  </>
                )}
                <rect
                  x={x - innerW / 48}
                  y={padT}
                  width={innerW / 24}
                  height={innerH}
                  fill="transparent"
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
              </g>
            );
          })}
        </svg>
      </div>

      <div className="mt-3 flex min-h-[24px] items-center justify-between border-t border-[#334155]/70 pt-3 text-xs text-slate-400">
        {activePoint ? (
          <div className="flex flex-wrap items-center gap-4 font-tabular text-slate-200">
            <span>Horário: {activePoint.hora}</span>
            <span aria-hidden="true">·</span>
            <span className="text-sky-300">
              Meu Anúncio: {activePoint.meuAnuncio} un.
            </span>
            <span aria-hidden="true">·</span>
            <span className="text-amber-300">
              Concorrente: {activePoint.concorrente} un.
            </span>
          </div>
        ) : (
          <span>Passe o cursor sobre o gráfico para inspecionar cada hora.</span>
        )}
        <span className="font-tabular">Fuso: Brasília (BRT)</span>
      </div>
    </div>
  );
}
