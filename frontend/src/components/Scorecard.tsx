"use client";

import { useMemo, useState } from "react";

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <rect x="2" y="2" width="28" height="28" rx="7" fill="#1d1d1f" />
      <path
        d="M10 13.5 L13.5 17 L22 9"
        stroke="#ffffff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M9 22 L23 22"
        stroke="#ffffff"
        strokeOpacity="0.4"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function CircularGauge({
  value,
  label,
}: {
  value: number;
  label: string;
}) {
  const size = 220;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = (value / 100) * c;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id="gauge-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1d1d1f" />
            <stop offset="100%" stopColor="#6e6e73" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="rgba(29, 29, 31, 0.08)"
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="url(#gauge-grad)"
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-[10px] uppercase tracking-[0.18em] text-[color:var(--color-muted)] mb-1">
          {label}
        </div>
        <div className="flex items-baseline">
          <span className="display-tight text-[60px] text-[color:var(--color-ink)] leading-none">
            {value}
          </span>
          <span className="text-[15px] text-[color:var(--color-muted)] ml-1">
            /100
          </span>
        </div>
      </div>
    </div>
  );
}

export function DimensionRadar({
  dimensions,
}: {
  dimensions: { label: string; value: number }[];
}) {
  const size = 230;
  const cx = size / 2;
  const cy = size / 2;
  const radius = 78;
  const n = dimensions.length;

  const points = dimensions.map((d, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    const r = (d.value / 100) * radius;
    return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r] as const;
  });
  const pathD =
    points
      .map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`))
      .join(" ") + " Z";

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id="radar-fill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1d1d1f" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#1d1d1f" stopOpacity="0.06" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75, 1].map((s) => {
          const pts = dimensions
            .map((_, i) => {
              const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
              return `${cx + Math.cos(angle) * radius * s},${cy + Math.sin(angle) * radius * s}`;
            })
            .join(" ");
          return (
            <polygon
              key={s}
              points={pts}
              fill="none"
              stroke="rgba(29, 29, 31, 0.1)"
              strokeWidth={0.8}
            />
          );
        })}
        {dimensions.map((_, i) => {
          const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={cx + Math.cos(angle) * radius}
              y2={cy + Math.sin(angle) * radius}
              stroke="rgba(29, 29, 31, 0.06)"
              strokeWidth={0.8}
            />
          );
        })}
        <path
          d={pathD}
          fill="url(#radar-fill)"
          stroke="#1d1d1f"
          strokeWidth={1.5}
        />
        {points.map((p, i) => (
          <circle key={i} cx={p[0]} cy={p[1]} r={2.2} fill="#1d1d1f" />
        ))}
        {dimensions.map((d, i) => {
          const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
          const lr = radius + 16;
          const x = cx + Math.cos(angle) * lr;
          const y = cy + Math.sin(angle) * lr;
          return (
            <text
              key={i}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="9.5"
              fill="#6e6e73"
              fontWeight="500"
            >
              {d.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

export function SparkLine({
  values,
  color,
}: {
  values: number[];
  color: string;
}) {
  const w = 100;
  const h = 22;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(1, max - min);

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  });
  const linePath = `M${points[0]} L${points.slice(1).join(" L")}`;
  const areaPath = `${linePath} L${w},${h} L0,${h} Z`;
  const id = `spark-${color.replace(/[^a-z0-9]/gi, "")}`;

  return (
    <svg
      width="100%"
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${id})`} />
      <path d={linePath} stroke={color} strokeWidth="1.3" fill="none" />
    </svg>
  );
}

export function ScoreDistribution({ value }: { value: number }) {
  const w = 200;
  const h = 100;
  const buckets = 30;

  const bars = useMemo(() => {
    const out: number[] = [];
    for (let i = 0; i < buckets; i++) {
      const x = (i / (buckets - 1)) * 100;
      const yval = Math.exp(-Math.pow((x - 62) / 14, 2));
      out.push(yval);
    }
    return out;
  }, []);

  const bw = w / buckets - 1.5;

  return (
    <div className="relative">
      <svg width={w} height={h + 26} viewBox={`0 0 ${w} ${h + 26}`}>
        <defs>
          <linearGradient id="hist-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1d1d1f" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#1d1d1f" stopOpacity="0.35" />
          </linearGradient>
        </defs>
        {bars.map((v, i) => {
          const bh = v * (h - 10);
          const x = (i / buckets) * w + 1;
          return (
            <rect
              key={i}
              x={x}
              y={h - bh}
              width={bw}
              height={bh}
              fill="url(#hist-grad)"
              rx="1.5"
            />
          );
        })}
        <line
          x1={(value / 100) * w}
          x2={(value / 100) * w}
          y1={0}
          y2={h + 2}
          stroke="#1d1d1f"
          strokeWidth="1.2"
          strokeDasharray="2 2"
        />
        <text
          x={(value / 100) * w}
          y={-2}
          textAnchor="middle"
          fontSize="9.5"
          fill="#1d1d1f"
          dy="10"
          fontWeight="600"
        >
          {value}
        </text>
        <text
          x={(value / 100) * w}
          y={h + 14}
          textAnchor="middle"
          fontSize="9.5"
          fill="#1d1d1f"
          fontWeight="500"
        >
          You
        </text>
        <text x={0} y={h + 22} fontSize="8.5" fill="#86868b">
          0
        </text>
        <text x={w / 2 - 5} y={h + 22} fontSize="8.5" fill="#86868b">
          50
        </text>
        <text x={w - 15} y={h + 22} fontSize="8.5" fill="#86868b">
          100
        </text>
      </svg>
      <p className="text-[10.5px] text-[color:var(--color-muted)] mt-1.5">
        Compared to 1.2M recent hypotheses
      </p>
    </div>
  );
}

export function EvidenceQualityCard({
  score,
  tier,
  submetrics,
}: {
  score: number;
  tier: string;
  submetrics: { label: string; value: number }[];
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[13px] font-semibold text-[color:var(--color-ink)] tracking-tight">
          Evidence Quality
        </h3>
        <span className="text-[color:var(--color-muted)]">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4M12 8h.01" />
          </svg>
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-[color:var(--color-canvas-2)] flex items-center justify-center text-[color:var(--color-ink)]">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>
        <div>
          <div className="flex items-baseline">
            <span className="display-tight text-[28px] text-[color:var(--color-ink)] leading-none">
              {score}
            </span>
            <span className="text-[12px] text-[color:var(--color-muted)] ml-1">
              /100
            </span>
          </div>
          <div className="text-[11.5px] text-[color:var(--color-green)] font-medium">
            {tier}
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-2 mt-1">
        {submetrics.map((s) => (
          <div key={s.label} className="flex items-center justify-between gap-2">
            <span className="text-[11.5px] text-[color:var(--color-muted)] flex-1 truncate">
              {s.label}
            </span>
            <div className="w-16 h-1 bg-[color:var(--color-hairline)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-[color:var(--color-ink)]"
                style={{ width: `${s.value}%` }}
              />
            </div>
            <span className="text-[11px] text-mono text-[color:var(--color-ink)] w-6 text-right">
              {s.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ImpactProjections({
  data,
}: {
  data: { year: number; total: number; vel: number; baseline: number }[];
}) {
  const w = 360;
  const h = 180;
  const padX = 30;
  const padY = 20;
  const innerW = w - padX * 2;
  const innerH = h - padY * 2;

  const all = data.flatMap((d) => [d.total, d.vel, d.baseline]);
  const max = Math.max(...all, 100);
  const min = 0;

  const xFor = (i: number) => padX + (i / (data.length - 1)) * innerW;
  const yFor = (v: number) =>
    padY + innerH - ((v - min) / (max - min)) * innerH;

  const lineFor = (key: "total" | "vel" | "baseline") =>
    data
      .map((d, i) => `${i === 0 ? "M" : "L"}${xFor(i)},${yFor(d[key])}`)
      .join(" ");

  const totalEnd = data[data.length - 1].total;
  const velEnd = data[data.length - 1].vel;

  return (
    <div className="flex gap-3">
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="flex-1">
        <defs>
          <linearGradient id="total-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1d1d1f" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#1d1d1f" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 50, 100].map((v) => (
          <g key={v}>
            <line
              x1={padX}
              x2={padX + innerW}
              y1={yFor(v)}
              y2={yFor(v)}
              stroke="rgba(29, 29, 31, 0.06)"
            />
            <text x={4} y={yFor(v) + 3} fontSize="9" fill="#86868b">
              {v}
            </text>
          </g>
        ))}
        <path
          d={lineFor("baseline")}
          stroke="#86868b"
          strokeWidth="1.2"
          strokeDasharray="3 3"
          fill="none"
        />
        <path
          d={lineFor("vel")}
          stroke="#9ca3af"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d={`${lineFor("total")} L${xFor(data.length - 1)},${yFor(0)} L${xFor(0)},${yFor(0)} Z`}
          fill="url(#total-grad)"
        />
        <path
          d={lineFor("total")}
          stroke="#1d1d1f"
          strokeWidth="1.8"
          fill="none"
        />
        {data.map((d, i) => (
          <text
            key={i}
            x={xFor(i)}
            y={h - 4}
            textAnchor="middle"
            fontSize="9"
            fill="#86868b"
          >
            Year {d.year}
          </text>
        ))}
      </svg>
      <div className="flex flex-col gap-2 justify-center text-[11.5px] min-w-[110px]">
        <div>
          <div className="flex items-center gap-1.5 text-[color:var(--color-ink)]">
            <span className="w-2 h-2 rounded-full bg-[color:var(--color-ink)]" />
            Total (5Y)
          </div>
          <div className="text-[color:var(--color-green)] text-[11px] ml-3.5">
            High{" "}
            <span className="text-mono text-[color:var(--color-ink)] ml-1">
              {totalEnd}
            </span>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-[color:var(--color-muted)]">
            <span className="w-2 h-2 rounded-full bg-[color:var(--color-muted)]" />
            Velocity (24m)
          </div>
          <div className="text-[color:var(--color-green)] text-[11px] ml-3.5">
            High{" "}
            <span className="text-mono text-[color:var(--color-ink)] ml-1">
              {velEnd}
            </span>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-[color:var(--color-muted)]">
            <span className="w-2 h-2 rounded-full bg-[color:var(--color-muted)]" />
            Baseline median
          </div>
          <div className="text-mono text-[color:var(--color-ink)] text-[11px] ml-3.5">
            50
          </div>
        </div>
      </div>
    </div>
  );
}

export function ConceptSpread({
  clusters,
}: {
  clusters: { name: string; color: string; count: number }[];
}) {
  const w = 280;
  const h = 200;

  const nodes = useMemo(() => {
    const out: { x: number; y: number; r: number; color: string }[] = [];
    clusters.forEach((c, ci) => {
      const angle = (ci / clusters.length) * Math.PI * 2;
      const ringX = w / 2 + Math.cos(angle) * 60;
      const ringY = h / 2 + Math.sin(angle) * 50;
      for (let i = 0; i < c.count; i++) {
        const a = Math.random() * Math.PI * 2;
        const r = Math.sqrt(Math.random()) * 28;
        out.push({
          x: ringX + Math.cos(a) * r,
          y: ringY + Math.sin(a) * r,
          r: 1.5 + Math.random() * 2.5,
          color: c.color,
        });
      }
    });
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clusters.length]);

  return (
    <div className="flex gap-3">
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="flex-1">
        {nodes.map((n, i) => (
          <circle key={i} cx={n.x} cy={n.y} r={n.r} fill={n.color} opacity={0.75} />
        ))}
        {nodes.slice(0, 24).map((n, i) => {
          const m = nodes[(i + 7) % nodes.length];
          return (
            <line
              key={`e-${i}`}
              x1={n.x}
              y1={n.y}
              x2={m.x}
              y2={m.y}
              stroke={n.color}
              strokeOpacity="0.12"
              strokeWidth="0.6"
            />
          );
        })}
      </svg>
      <div className="flex flex-col gap-1.5 text-[11.5px] min-w-[110px] pt-1">
        {clusters.map((c) => (
          <div key={c.name} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: c.color }}
            />
            <span className="text-[color:var(--color-body)]">{c.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SimilarLandscape({
  items,
  total,
}: {
  items: { title: string; similarity: number; url?: string }[];
  total: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const collapsedCount = 3;
  const visible = expanded ? items : items.slice(0, collapsedCount);

  return (
    <div className="flex flex-col gap-2.5">
      {visible.map((it, i) => {
        const inner = (
          <>
            <div className="w-1 h-1 rounded-full bg-[color:var(--color-muted)] mt-2 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-[12px] text-[color:var(--color-ink)] leading-snug">
                {it.title}
              </div>
            </div>
            <div className="text-[12px] text-mono text-[color:var(--color-ink)] font-semibold shrink-0">
              {it.similarity}%
            </div>
          </>
        );
        return it.url ? (
          <a
            key={i}
            href={it.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 group hover:bg-white/60 rounded-md -mx-1 px-1 py-0.5 transition-colors"
          >
            {inner}
          </a>
        ) : (
          <div key={i} className="flex items-start gap-2">
            {inner}
          </div>
        );
      })}
      {items.length > collapsedCount && (
        <button
          className="btn-ghost mt-2"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Show less" : `Show all (${total})`}
        </button>
      )}
    </div>
  );
}
