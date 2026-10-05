/** Paired horizontal bars: control vs loop median unhealthy seconds out of 40 (recorded data). */
export function ControlLoopBars({ control, loop, max = 40, label }: { control: number; loop: number; max?: number; label: string }) {
  const w = (x: number) => `${Math.max(0.6, (x / max) * 100)}%`;
  return (
    <figure className="m-0" aria-label={`${label}: control ${control.toFixed(1)} s, loop ${loop.toFixed(1)} s of ${max} s`}>
      <div className="space-y-1.5 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-16 shrink-0 text-muted">Control</span>
          <div className="h-3 flex-1 rounded bg-surface-2">
            <div className="h-3 rounded bg-danger" style={{ width: w(control) }} />
          </div>
          <span className="num w-14 text-right font-semibold">{control.toFixed(1)} s</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-16 shrink-0 text-muted">Loop</span>
          <div className="h-3 flex-1 rounded bg-surface-2">
            <div className="h-3 rounded bg-accent" style={{ width: w(loop) }} />
          </div>
          <span className="num w-14 text-right font-semibold">{loop.toFixed(1)} s</span>
        </div>
      </div>
    </figure>
  );
}
