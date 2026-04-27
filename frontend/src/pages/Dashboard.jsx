import { AlertCircle, Bell, BookOpen, CheckCircle2, Clock, Play, Search, Zap } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { ProgressBar } from "../components/ProgressBar";
import { getTheme } from "../lib/theme";

const dayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function kpiIcon(name) {
  const c = "h-5 w-5";
  switch (name) {
    case "book":
      return <BookOpen className={c} />;
    case "clock":
      return <Clock className={c} />;
    case "check":
      return <CheckCircle2 className={c} />;
    case "bolt":
      return <Zap className={c} />;
    default:
      return null;
  }
}

function planIcon(kind) {
  const c = "h-5 w-5";
  if (kind === "watch") return <Play className={c} />;
  if (kind === "quiz") return <CheckCircle2 className={c} />;
  return <AlertCircle className={c} />;
}

function urgencyClass(u) {
  if (u === "today") return "bg-red-100 text-red-700";
  if (u === "soon") return "bg-amber-100 text-amber-800";
  return "bg-blue-100 text-blue-700";
}

export function Dashboard() {
  const [data, setData] = useState(null);
  const [notifs, setNotifs] = useState(null);
  const [err, setErr] = useState("");
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifs, setShowNotifs] = useState(false);

  const submitDashboardSearch = () => {
    const q = searchQuery.trim();
    if (!q) return;
    navigate(`/search?q=${encodeURIComponent(q)}`);
    setSearchQuery("");
  };

  const handleSearch = (e) => {
    e.preventDefault();
    submitDashboardSearch();
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [d, n] = await Promise.all([
          api("/api/learnflow/dashboard"),
          api("/api/learnflow/notifications")
        ]);
        if (!cancelled) {
          setData(d);
          setNotifs(n);
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const chartData = useMemo(() => {
    if (!data?.weekly_hours?.length) return [];
    const todayIdx = (new Date().getDay() + 6) % 7;
    return data.weekly_hours.map((h, i) => ({
      day: dayLabels[i],
      hours: h,
      highlight: i === todayIdx,
    }));
  }, [data]);

  if (err) {
    return (
      <div className="p-8">
        <p className="text-red-600">{err}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-500">
        Loading dashboard…
      </div>
    );
  }

  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const urgentDeadlineCount = (data.deadlines || []).filter((d) => d.urgency === "today" || d.urgency === "soon").length;

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10 transition-colors duration-300">
      <header className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-display text-3xl text-slate-900">
            {greet}, {data.greeting_name}! 👋
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {data.header_date} · {data.task_summary}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <form className="relative" onSubmit={handleSearch}>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              id="dashboard-search"
              name="dashboard_search"
              aria-label="Search across learnflow"
              placeholder="Search…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === "NumpadEnter") {
                  e.preventDefault();
                  submitDashboardSearch();
                }
              }}
              className="w-56 rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none ring-blue-500/20 focus:ring-2 lg:w-64"
            />
            <button type="submit" className="sr-only">
              Search
            </button>
          </form>
          <div className="relative">
            <button
              type="button"
              className={`relative flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 transition-colors ${showNotifs ? 'bg-slate-50 text-slate-900 border-slate-300' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              aria-label="Notifications"
              onClick={() => setShowNotifs(!showNotifs)}
            >
              <Bell className="h-5 w-5" />
              {notifs?.unread_count > 0 && (
                <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full border-2 border-white bg-red-500 text-[10px] font-bold text-white">
                  {notifs.unread_count}
                </span>
              )}
            </button>
            
            {showNotifs && (
              <div className="absolute right-0 top-12 z-50 w-80 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-xl shadow-slate-200/50">
                <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-4 py-3">
                  <h3 className="font-semibold text-slate-800">Notifications</h3>
                  <button onClick={() => setShowNotifs(false)} className="text-xs font-medium text-slate-500 hover:text-slate-800">Close</button>
                </div>
                <div className="max-h-96 overflow-y-auto p-2">
                  {!notifs?.notifications?.length ? (
                    <div className="p-4 text-center text-sm text-slate-500">You're all caught up!</div>
                  ) : (
                    <ul className="space-y-1">
                      {notifs.notifications.map((n) => (
                        <li key={n.id} className="rounded-xl p-3 transition-colors hover:bg-slate-50">
                          <div className="flex items-start gap-3">
                            <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${n.type === 'alert' ? 'bg-red-100 text-red-600' : n.type === 'warning' ? 'bg-amber-100 text-amber-600' : n.type === 'success' ? 'bg-emerald-100 text-emerald-600' : 'bg-blue-100 text-blue-600'}`}>
                              {n.type === 'alert' || n.type === 'warning' ? <AlertCircle className="h-4 w-4"/> : <CheckCircle2 className="h-4 w-4"/>}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="font-medium text-slate-900 text-sm">{n.title}</p>
                              <p className="mt-0.5 text-xs text-slate-500 leading-relaxed">{n.message}</p>
                              {n.timestamp && <span className="mt-1.5 block text-[10px] font-medium text-slate-400 uppercase tracking-wider">{n.timestamp}</span>}
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {data.kpis.map((k) =>
          k.variant === "primary" ? (
            <div
              key={k.label}
              className="flex items-center justify-between rounded-2xl bg-blue-600 px-5 py-5 text-white shadow-lg shadow-blue-600/25 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl"
            >
              <div>
                <p className="text-sm font-medium text-blue-100">{k.label}</p>
                <p className="mt-1 font-display text-2xl">{k.value}</p>
              </div>
              <div className="rounded-xl bg-white/15 p-3">{kpiIcon(k.icon)}</div>
            </div>
          ) : (
            <div key={k.label} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">{k.label}</p>
                  <p className="mt-2 font-display text-xl text-slate-900">{k.value}</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-2.5 text-slate-600">{kpiIcon(k.icon)}</div>
              </div>
            </div>
          ),
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-md">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="font-display text-xl text-slate-900">Course Progress</h2>
            <Link to="/courses" className="text-sm font-medium text-blue-600 hover:underline">
              View all
            </Link>
          </div>
          <ul className="space-y-5">
            {data.course_progress.map((c) => (
              <li key={c.course_id}>
                <div className="mb-1.5 flex justify-between text-sm">
                  <span className="font-medium text-slate-800">{c.title}</span>
                  <span className="text-slate-500">{Math.round(c.progress_percent)}%</span>
                </div>
                <ProgressBar percent={c.progress_percent} theme={c.theme} />
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-md">
          <h2 className="mb-6 font-display text-xl text-slate-900">Today&apos;s Study Plan</h2>
          <ul className="space-y-3">
            {data.today_plan.map((t) => {
              const accent = getTheme(t.accent === "green" ? "green" : t.accent === "orange" ? "orange" : "blue");
              return (
                <li
                  key={t.id}
                  onClick={() => navigate('/planner')}
                  className={`flex cursor-pointer gap-4 rounded-xl border border-slate-100 p-4 transition-colors hover:shadow-md ${t.status === "completed" ? "bg-slate-50/80" : "bg-white"}`}
                >
                  <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${accent.soft}`}>
                    {planIcon(t.kind)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-900">{t.title}</p>
                    {t.subtitle ? <p className="text-sm text-slate-500">{t.subtitle}</p> : null}
                    <div className="mt-2">
                      {t.status === "completed" && (
                        <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                          Completed
                        </span>
                      )}
                      {t.status === "due_tonight" && (
                        <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                          Due tonight
                        </span>
                      )}
                      {t.status === "in_progress" && (
                        <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                          In progress
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-md">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="font-display text-xl text-slate-900">Upcoming Deadlines</h2>
            <Link to="/deadlines" className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600 hover:bg-red-100 transition-colors">
              {urgentDeadlineCount} urgent
            </Link>
          </div>
          <ul className="space-y-3">
            {data.deadlines.map((d) => (
              <li
                key={d.id}
                onClick={() => navigate('/deadlines')}
                className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-100 px-4 py-3.5 transition-colors hover:bg-slate-50 hover:shadow-sm"
              >
                <span className="font-medium text-slate-800">{d.title}</span>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${urgencyClass(d.urgency)}`}>
                  {d.urgency_label}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-md">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-xl text-slate-900">Weekly Study Hours</h2>
            <span className="text-sm font-semibold text-blue-600">{data.weekly_hours_label}</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip
                  cursor={{ fill: "#f1f5f9" }}
                  contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0" }}
                />
                <Bar dataKey="hours" radius={[6, 6, 0, 0]} maxBarSize={40}>
                  {chartData.map((entry, index) => (
                    <Cell key={index} fill={entry.highlight ? "#2563eb" : "#bfdbfe"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  );
}
