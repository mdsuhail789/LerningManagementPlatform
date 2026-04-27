import { getTheme } from "../lib/theme";

/**
 * @param {{ percent: number; theme: string; className?: string }} props
 */
export function ProgressBar({ percent, theme, className = "" }) {
  const t = getTheme(theme);
  const w = Math.min(100, Math.max(0, percent));
  return (
    <div className={`h-2 w-full rounded-full bg-slate-100 overflow-hidden ${className}`}>
      <div className={`h-full rounded-full transition-all ${t.bar}`} style={{ width: `${w}%` }} />
    </div>
  );
}
