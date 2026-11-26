interface MarginGaugeProps {
  marginPct: number;
}

export function MarginGauge({ marginPct }: MarginGaugeProps) {
  const clamped = Math.max(-20, Math.min(50, marginPct));
  const normalized = (clamped + 20) / 70; // 0..1 across -20%..50%
  const angleDeg = -90 + normalized * 180;

  const statusColor =
    marginPct >= 20 ? '#34D399' : marginPct >= 10 ? '#FBBF24' : '#F87171';
  const statusLabel =
    marginPct >= 20
      ? 'Margem Saudável'
      : marginPct >= 10
        ? 'Margem de Atenção'
        : 'Margem Crítica';

  const r = 82;
  const cx = 120;
  const cy = 108;
  const circumference = Math.PI * r;
  const filledLen = circumference * normalized;

  return (
    <div className="glass-card flex flex-col items-center justify-center rounded-2xl p-6">
      <div className="mb-1 text-xs font-medium text-slate-400">
        Velocímetro de Margem Líquida
      </div>

      <svg
        viewBox="0 0 240 138"
        className="w-full max-w-[260px]"
        role="img"
        aria-label={`Margem líquida estimada de ${marginPct.toFixed(1)}%`}
      >
        {/* Background track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#1E293B"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Active arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={statusColor}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={`${filledLen.toFixed(1)} ${circumference.toFixed(1)}`}
        />
        {/* Needle */}
        <g transform={`translate(${cx}, ${cy}) rotate(${angleDeg})`}>
          <line
            x1="0"
            y1="0"
            x2="0"
            y2={-(r - 18)}
            stroke="#F8FAFC"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          <circle cx="0" cy="0" r="5" fill="#F8FAFC" />
        </g>

        <text
          x="30"
          y="128"
          className="fill-slate-500 text-[10px] font-tabular"
        >
          -20%
        </text>
        <text
          x="120"
          y="16"
          textAnchor="middle"
          className="fill-slate-400 text-[10px] font-tabular"
        >
          15%
        </text>
        <text
          x="210"
          y="128"
          textAnchor="end"
          className="fill-slate-500 text-[10px] font-tabular"
        >
          50%
        </text>
      </svg>

      <div
        className="font-tabular mt-1 text-3xl font-bold"
        style={{ color: statusColor }}
      >
        {marginPct.toFixed(1)}%
      </div>
      <div className="mt-1 text-xs font-medium text-slate-300">
        {statusLabel}
      </div>
    </div>
  );
}
