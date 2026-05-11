"use client";

export function Placeholder({ label, height = "100%" }: { label: string; height?: string | number }) {
  return (
    <div
      className="w-full bg-surface border border-divider rounded-sm flex items-center justify-center"
      style={{ height }}
    >
      <span className="smallcaps text-muted">{label}</span>
    </div>
  );
}
