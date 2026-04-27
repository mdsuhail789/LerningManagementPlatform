import { Play, Search, SlidersHorizontal, X, Loader2, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { getTheme } from "../lib/theme";
import { EnrollCourseModal } from "../components/EnrollCourseModal";
import { useAuth } from "../context/AuthContext";

const tabs = [
  { key: "all", label: "All Courses" },
  { key: "in_progress", label: "In Progress" },
  { key: "completed", label: "Completed" },
];

export function Courses() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = String(user?.role ?? "").toLowerCase() === "admin";
  const [tab, setTab] = useState("all");
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const [refreshPulse, setRefreshPulse] = useState(0);
  const [deletingCourseId, setDeletingCourseId] = useState("");

  useEffect(() => {
    let cancelled = false;
    const qs = new URLSearchParams({ status: tab });
    (async () => {
      try {
        const d = await api(`/api/learnflow/courses?${qs.toString()}`);
        if (!cancelled) setData(d);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tab, refreshPulse]);

  const filtered = useMemo(() => {
    if (!data?.courses) return [];
    const s = q.trim().toLowerCase();
    if (!s) return data.courses;
    return data.courses.filter(
      (c) => c.title.toLowerCase().includes(s) || c.author.toLowerCase().includes(s) || c.category.toLowerCase().includes(s),
    );
  }, [data, q]);

  async function handleDeleteCourse(courseId) {
    setErr("");
    setDeletingCourseId(courseId);
    try {
      await api(`/api/courses/${courseId}`, { method: "DELETE" });
      setRefreshPulse((r) => r + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to delete course");
    } finally {
      setDeletingCourseId("");
    }
  }

  if (err) {
    return (
      <div className="p-8">
        <p className="text-red-600">{err}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-500">Loading courses…</div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10">
      <header className="mb-8 rounded-[28px] border border-slate-100 bg-white/80 p-5 shadow-sm backdrop-blur-sm lg:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="font-display text-3xl text-slate-900">My Courses</h1>
          <p className="mt-1 text-sm text-slate-500">{data.summary}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative group lg:w-80">
            <form onSubmit={(e) => e.preventDefault()} className="relative">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-blue-500 group-hover:text-slate-500" />
              <input
                type="text"
                id="courses-search"
                name="courses_search"
                aria-label="Search courses"
                placeholder="Search courses..."
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="w-full min-w-[200px] rounded-full border border-slate-200 bg-white/80 backdrop-blur-sm py-2.5 pl-11 pr-10 text-sm shadow-sm outline-none ring-blue-500/20 transition-all duration-300 hover:bg-white hover:border-slate-300 hover:shadow-md focus:bg-white focus:border-blue-500 focus:ring-4 focus:shadow-md sm:w-72 lg:w-full"
              />
              {q && (
                <button
                  type="button"
                  onClick={() => setQ("")}
                  className="absolute right-3 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition-all hover:bg-slate-200 hover:text-slate-700 hover:scale-105 focus:outline-none opacity-100 scale-100"
                  title="Clear search"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </form>
          </div>
          {isAdmin ? (
            <button
              type="button"
              onClick={() => setIsEnrollModalOpen(true)}
              className="whitespace-nowrap rounded-2xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition-all duration-300 hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-blue-600/30"
            >
              + Enroll Course
            </button>
          ) : null}
        </div>
        </div>
      </header>

      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2 rounded-2xl bg-slate-100/80 p-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-300 ${
                tab === t.key ? "bg-blue-600 text-white shadow-md shadow-blue-600/20" : "bg-transparent text-slate-600 hover:bg-white hover:text-slate-900"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] opacity-100 scale-100 blur-0">
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((c) => {
          const th = getTheme(c.category_theme);
          const btn = getTheme(c.cta_theme);
          return (
            <article
              key={c.id}
              className="flex flex-col overflow-hidden rounded-[24px] border border-slate-100 bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-200/60"
            >
              <div className="relative aspect-[16/10] overflow-hidden">
                <img src={c.image_url} alt="" className="h-full w-full object-cover" />
              </div>
              <div className="flex flex-1 flex-col p-5">
                <div className="mb-3 flex items-start justify-between gap-2">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${th.soft}`}>{c.category}</span>
                  {c.hours_remaining_label ? (
                    <span className="flex items-center gap-1 text-xs font-medium text-slate-500">{c.hours_remaining_label}</span>
                  ) : null}
                </div>
                <h2 className="font-display text-lg leading-snug text-slate-900">{c.title}</h2>
                <p className="mt-2 text-sm text-slate-500">
                  {c.author}
                  {c.certificate_eligible ? " · Certificate" : ""}
                </p>
                {isAdmin ? (
                  <div className="mt-3 space-y-1 text-xs text-slate-500">
                    <p>
                      <span className="font-semibold text-emerald-700">{c.learner_completed_count}</span> completed
                      {c.learner_completed_names?.length ? `: ${c.learner_completed_names.join(", ")}` : ""}
                    </p>
                    <p>
                      <span className="font-semibold text-blue-700">{c.learner_in_progress_count}</span> in progress
                      {c.learner_in_progress_names?.length ? `: ${c.learner_in_progress_names.join(", ")}` : ""}
                    </p>
                  </div>
                ) : null}
                <div className="mt-4">
                  <div className="mb-1 flex justify-between text-xs font-medium text-slate-500">
                    <span>{isAdmin ? "Learner Status" : "Progress"}</span>
                    <span>{isAdmin ? c.status.replace("_", " ") : `${c.progress_percent}%`}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <div className={`h-full rounded-full ${th.bar}`} style={{ width: `${c.progress_percent}%` }} />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => navigate(`/courses/${c.id}`)}
                  className={`mt-5 flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold ${btn.btn}`}
                >
                  <Play className="h-4 w-4 fill-current" />
                  {c.cta_label}
                </button>
                {isAdmin ? (
                  <button
                    type="button"
                    onClick={() => handleDeleteCourse(c.id)}
                    disabled={deletingCourseId === c.id}
                    className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-red-200 bg-red-50 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-100 disabled:opacity-60"
                  >
                    {deletingCourseId === c.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                    Delete Course
                  </button>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>

      {filtered.length === 0 && q.trim() !== "" ? (
          <div className="mt-16 flex flex-col items-center justify-center text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-slate-50 border border-slate-100 shadow-inner">
               <Search className="h-8 w-8 text-slate-300" />
            </div>
            <h3 className="mt-5 text-lg font-display font-semibold text-slate-900">No matching courses</h3>
            <p className="mt-2 max-w-sm text-sm text-slate-500 leading-relaxed">
              We couldn't find anything matching "<strong className="text-slate-700">{q}</strong>". Try adjusting your search term or filtering options.
            </p>
            <button
              onClick={() => setQ("")}
              className="mt-6 rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-200"
            >
              Clear Search
            </button>
          </div>
        ) : null}
      </div>

      {isAdmin ? (
        <EnrollCourseModal
          isOpen={isEnrollModalOpen}
          onClose={() => setIsEnrollModalOpen(false)}
          onCourseEnrolled={() => setRefreshPulse(r => r + 1)}
        />
      ) : null}
    </div>
  );
}
