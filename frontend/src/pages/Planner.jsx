import { ArrowRight, CheckCircle2, ChevronLeft, ChevronRight, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { AddTaskModal } from "../components/AddTaskModal";

const statusStyles = {
  done: { bar: "bg-emerald-500", pill: "bg-emerald-100 text-emerald-700" },
  now: { bar: "bg-blue-600", pill: "bg-blue-100 text-blue-700" },
  pending: { bar: "bg-violet-500", pill: "bg-violet-100 text-violet-800" },
  scheduled: { bar: "bg-amber-500", pill: "bg-amber-100 text-amber-800" },
};

function toISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function parseISODate(value) {
  if (!value || typeof value !== "string") return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  if (!Number.isFinite(y) || !Number.isFinite(mo) || !Number.isFinite(d)) return null;
  const dt = new Date(y, mo - 1, d);
  // Guard against invalid rollovers (e.g. 2026-02-31).
  if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return null;
  return dt;
}

/** Avoid JS Date rollover (e.g. Jan 31 + 1 month → March). */
function addCalendarMonths(date, delta) {
  const y = date.getFullYear();
  const m = date.getMonth() + delta;
  const lastDay = new Date(y, m + 1, 0).getDate();
  const day = Math.min(date.getDate(), lastDay);
  return new Date(y, m, day);
}

export function Planner() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [view, setView] = useState(() => {
    const v = (searchParams.get("view") || "").toLowerCase();
    return v === "day" || v === "week" || v === "month" ? v : "day";
  });

  const [selectedDay, setSelectedDay] = useState(() => {
    const fromUrl = parseISODate(searchParams.get("day"));
    return fromUrl ?? new Date();
  });
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [showAddTask, setShowAddTask] = useState(false);

  // Persist current planner state in the URL so refresh/share keeps it.
  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    next.set("view", view);
    next.set("day", toISODate(selectedDay));
    const nextStr = next.toString();
    const curStr = searchParams.toString();
    if (nextStr !== curStr) setSearchParams(next, { replace: true });
  }, [view, selectedDay, searchParams, setSearchParams]);

  const fetchData = useCallback(async () => {
    try {
      const qs = new URLSearchParams({ view, day: toISODate(selectedDay) });
      const d = await api(`/api/learnflow/planner?${qs.toString()}`);
      setData(d);
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load");
    }
  }, [view, selectedDay]);

  const autoSchedule = useCallback(async () => {
    try {
      const qs = new URLSearchParams({ day: toISODate(selectedDay) });
      const d = await api(`/api/learnflow/planner/auto-schedule?${qs.toString()}`, { method: "POST" });
      setData(d);
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not auto-schedule");
    }
  }, [selectedDay]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (err) {
    return (
      <div className="p-8">
        <p className="text-red-600">{err}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-500">Loading planner…</div>
    );
  }

  const calendarDays = data?.calendar?.days || data.calendar_days || [];
  const calendarTitle = data?.calendar?.title || data.calendar_title || "";
  const calendarWeekdayLabels = data?.calendar?.weekday_labels || data.calendar_weekday_labels || [];

  const weeks = [];
  for (let i = 0; i < calendarDays.length; i += 7) {
    weeks.push(calendarDays.slice(i, i + 7));
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10">
      <header className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="font-display text-3xl text-slate-900">Smart Study Planner</h1>
          <p className="mt-1 text-sm text-slate-500">Organize your study sessions and stay ahead of your learning goals</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={async () => {
              await autoSchedule();
            }}
            className="rounded-xl border-2 border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50 transition-colors"
          >
            Auto-Schedule
          </button>
          <button
            type="button"
            onClick={() => setShowAddTask(true)}
            className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-colors"
          >
            + Add Task
          </button>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-4">
          <section className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-lg text-slate-900">{calendarTitle}</h2>
              <div className="flex gap-1">
                <button 
                  type="button" 
                  onClick={() => {
                    setSelectedDay(addCalendarMonths(selectedDay, -1));
                  }}
                  className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 transition-colors"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button 
                  type="button" 
                  onClick={() => {
                    setSelectedDay(addCalendarMonths(selectedDay, 1));
                  }}
                  className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 transition-colors"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-slate-400">
              {calendarWeekdayLabels.map((w) => (
                <div key={w} className="py-2">
                  {w}
                </div>
              ))}
            </div>
            <div className="mt-1 space-y-1">
              {weeks.map((row, ri) => (
                <div key={ri} className="grid grid-cols-7 gap-1">
                  {row.map((cell, ci) => (
                    <div
                      key={ci}
                      className={`flex h-9 items-center justify-center rounded-lg text-sm font-medium transition-colors cursor-pointer hover:bg-slate-100 ${
                        !cell.is_current_month ? "text-slate-300" : "text-slate-700"
                      } ${cell.is_today ? "bg-blue-600 text-white shadow-md hover:bg-blue-700" : ""} ${
                        cell.is_deadline && cell.is_current_month && !cell.is_today ? "bg-red-100 text-red-700 hover:bg-red-200" : ""
                      }`}
                      onClick={() => {
                        if (cell.is_current_month) {
                          const d = new Date(selectedDay);
                          d.setDate(cell.day);
                          setSelectedDay(d);
                        }
                      }}
                    >
                      {cell.day}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl bg-gradient-to-br from-blue-600 to-blue-700 p-5 text-white shadow-xl shadow-blue-600/20">
            <div className="mb-3 flex items-center gap-2 text-blue-100">
              <Sparkles className="h-5 w-5" />
              <span className="text-sm font-semibold uppercase tracking-wide">AI recommendation</span>
            </div>
            <p className="text-sm leading-relaxed text-blue-50">{data.ai_recommendation}</p>
            <button
              type="button"
              onClick={async () => {
                try {
                  const qs = new URLSearchParams({ day: toISODate(selectedDay) });
                  const d = await api(`/api/learnflow/planner/apply-recommendation?${qs.toString()}`, { method: "POST" });
                  setData(d);
                } catch (e) {
                  alert(e instanceof Error ? e.message : "Could not update schedule");
                }
              }}
              className="mt-4 flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 text-sm font-semibold backdrop-blur hover:bg-white/25 transition-colors"
            >
              Generate AI Tasks
              <ArrowRight className="h-4 w-4" />
            </button>
          </section>
        </div>

        <div className="xl:col-span-8">
          <div className="mb-4 flex flex-wrap gap-2">
            {["day", "week", "month"].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setView(v)}
                className={`rounded-full px-4 py-2 text-sm font-semibold capitalize transition ${
                  view === v ? "bg-blue-600 text-white shadow-md" : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {v === "day" ? "Day View" : v === "week" ? "Week View" : "Month"}
              </button>
            ))}
          </div>

          <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="font-display text-xl text-slate-900">{data.timeline_title}</h2>
              <p className="mt-1 font-mono text-sm text-slate-500">{data.timeline_subtitle}</p>
            </div>
            <ul className="space-y-4">
              {data.blocks.map((b, i) => {
                const st = statusStyles[b.status] || statusStyles.scheduled;
                const label =
                  b.status === "done"
                    ? "Done"
                    : b.status === "now"
                      ? "Now"
                      : b.status === "pending"
                        ? "Pending"
                        : "Scheduled";
                
                const toggleStatus = async () => {
                  if (!b.id) return;
                  if (b.status === "done") return;
                  try {
                    const nextSt = "completed";
                    await api(`/api/tasks/${b.id}`, {
                      method: "PUT",
                      body: JSON.stringify({ status: nextSt }),
                    });
                    await fetchData();
                  } catch (e) {
                    alert("Failed to update status: " + (e instanceof Error ? e.message : String(e)));
                  }
                };

                const deleteTask = async (e) => {
                  e.stopPropagation();
                  if (!b.id) return;
                  try {
                    await api(`/api/tasks/${b.id}`, { method: "DELETE" });
                    await fetchData();
                  } catch (e) {
                    alert("Failed to delete task: " + (e instanceof Error ? e.message : String(e)));
                  }
                };

                return (
                  <li
                    key={b.id || `${i}-${b.time}`}
                    onClick={b.id ? toggleStatus : undefined}
                    className={`flex gap-4 rounded-xl border border-slate-100 bg-slate-50/50 p-4 hover:bg-white hover:shadow-sm transition-all ${
                      b.id ? "cursor-pointer" : "cursor-default"
                    }`}
                  >
                    <span className="w-14 shrink-0 text-sm font-semibold text-slate-500">{b.time}</span>
                    <div className={`w-1 shrink-0 rounded-full ${st.bar}`} />
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-slate-900">{b.title}</p>
                      <p className="text-sm text-slate-500">
                        {b.subtitle}
                        {b.duration_minutes ? (
                          <span className="ml-2 font-mono text-xs text-slate-400">· {b.duration_label || `${b.duration_minutes} min`}</span>
                        ) : null}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {b.id ? (
                        <button
                          type="button"
                          onClick={deleteTask}
                          className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                          title="Delete task"
                          aria-label="Delete task"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      ) : null}
                      {b.status === "done" ? (
                        <span
                          className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
                          title="Completed"
                          aria-label="Completed"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                        </span>
                      ) : (
                        <span className={`h-fit rounded-full px-2.5 py-1 text-xs font-semibold ${st.pill}`}>
                          {label}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        </div>
      </div>
      
      <AddTaskModal 
        isOpen={showAddTask} 
        onClose={() => setShowAddTask(false)} 
        onTaskAdded={(newDateStr) => {
          if (newDateStr) {
            const [y, m, d] = newDateStr.split('-');
            setSelectedDay(new Date(y, m - 1, d));
          } else {
            fetchData();
          }
        }} 
      />
    </div>
  );
}
