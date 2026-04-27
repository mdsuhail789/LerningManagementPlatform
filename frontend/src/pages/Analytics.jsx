import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { ProgressBar } from "../components/ProgressBar";
import { getTheme } from "../lib/theme";

const periods = [
  { key: "month", label: "This Month" },
  { key: "quarter", label: "3 Months" },
  { key: "all", label: "All Time" },
];

const badgeTone = {
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-800",
  info: "bg-blue-100 text-blue-700",
  neutral: "bg-slate-100 text-slate-600",
};

const scoreTone = {
  success: "text-emerald-600",
  warning: "text-amber-600",
  danger: "text-red-600",
};

const statusTone = {
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-800",
  info: "bg-blue-100 text-blue-700",
  neutral: "bg-slate-100 text-slate-600",
};

export function Analytics() {
  const [period, setPeriod] = useState("month");
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    const qs = new URLSearchParams({ period });
    (async () => {
      try {
        const d = await api(`/api/learnflow/analytics?${qs.toString()}`);
        if (!cancelled) setData(d);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [period]);

  if (err) {
    return (
      <div className="p-8">
        <p className="text-red-600">{err}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-500">Loading analytics…</div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10">
      <header className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-display text-3xl text-slate-900">Learning Analytics</h1>
          <p className="mt-1 text-sm text-slate-500">Track your performance &amp; study patterns over time</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {periods.map((p) => (
            <button
              key={p.key}
              type="button"
              onClick={() => setPeriod(p.key)}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                period === p.key ? "bg-blue-600 text-white shadow-md" : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </header>

      <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {data.kpis.map((k) => (
          <div key={k.label} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">{k.label}</p>
            <p className="mt-2 font-display text-2xl text-slate-900">{k.value}</p>
            <span className={`mt-3 inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${badgeTone[k.badge_tone] || badgeTone.neutral}`}>
              {k.badge}
            </span>
          </div>
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="mb-6 font-display text-xl text-slate-900">Monthly Study Hours</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.monthly_hours} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }} />
                <Bar dataKey="hours" radius={[6, 6, 0, 0]} maxBarSize={48}>
                  {data.monthly_hours.map((entry, index) => (
                    <Cell key={index} fill={entry.highlight ? "#2563eb" : "#bfdbfe"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="mb-6 font-display text-xl text-slate-900">Subject Breakdown</h2>
          <ul className="space-y-5">
            {data.subjects.map((s) => (
              <li key={s.name}>
                <div className="mb-1.5 flex justify-between text-sm">
                  <span className="font-medium text-slate-800">{s.name}</span>
                  <span className="text-slate-500">{s.percent}%</span>
                </div>
                <ProgressBar percent={s.percent} theme={s.theme} />
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-2">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="font-display text-xl text-slate-900">Recent Performance</h2>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="pb-3 pr-4">Course</th>
                  <th className="pb-3 pr-4">Tasks Done</th>
                  <th className="pb-3 pr-4">Progress</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3">Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.performance.map((row) => (
                  <tr key={row.course} className="hover:bg-slate-50/80">
                    <td className="py-4 pr-4 font-medium text-slate-900">{row.course}</td>
                    <td className={`py-4 pr-4 font-semibold ${scoreTone[row.score_tone] || "text-slate-700"}`}>
                      {row.last_score}
                    </td>
                    <td className="py-4 pr-4">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${getTheme(row.progress_theme).bar}`}
                            style={{ width: `${row.progress_percent}%` }}
                          />
                        </div>
                        <span className="text-slate-500">{row.progress_percent}%</span>
                      </div>
                    </td>
                    <td className="py-4 pr-4">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusTone[row.status_tone] || statusTone.neutral}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="py-4 font-semibold text-emerald-600">{row.trend}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
