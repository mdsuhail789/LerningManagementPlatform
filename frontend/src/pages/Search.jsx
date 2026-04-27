import { AlertCircle, BookOpen, CheckCircle2, ChevronRight, Play, Search as SearchIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { ProgressBar } from "../components/ProgressBar";
import { getTheme } from "../lib/theme";

export function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawQ = searchParams.get("q") || "";
  const [q, setQ] = useState(rawQ);
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    if (!rawQ.trim()) {
      setData({ courses: [], tasks: [] });
      return;
    }

    setIsLoading(true);
    setErr("");
    
    (async () => {
      try {
        const qs = new URLSearchParams({ q: rawQ });
        const res = await api(`/api/learnflow/search?${qs.toString()}`);
        if (!cancelled) {
          setData(res);
          setIsLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : "Failed to load search results");
          setIsLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [rawQ]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (q.trim() !== rawQ) {
      setSearchParams({ q: q.trim() });
    }
  };

  const courses = data?.courses || [];
  const tasks = data?.tasks || [];

  const displayCourses = activeTab === "all" || activeTab === "courses" ? courses : [];
  const displayTasks = activeTab === "all" || activeTab === "tasks" ? tasks : [];
  
  const hasResults = courses.length > 0 || tasks.length > 0;
  
  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10">
      <header className="mb-8 max-w-3xl">
        <h1 className="font-display text-3xl text-slate-900">Global Search</h1>
        <p className="mt-1 text-sm text-slate-500">Find courses, tasks, and materials across your LMS.</p>
        
        <form onSubmit={handleSearchSubmit} className="relative mt-6">
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            id="global-search-input"
            name="global_search"
            aria-label="Global search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search anything..."
            className="w-full rounded-2xl border-2 border-slate-200 bg-white py-4 pl-12 pr-4 text-base outline-none ring-blue-500/20 focus:border-blue-500 focus:ring-4 transition-all"
          />
          <button 
            type="submit" 
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
          >
            Search
          </button>
        </form>
      </header>

      {err && (
        <div className="mb-8 rounded-xl bg-red-50 p-4 text-red-700">
          <p className="flex items-center gap-2"><AlertCircle className="h-5 w-5"/> {err}</p>
        </div>
      )}

      {isLoading ? (
        <div className="flex h-32 items-center justify-center text-slate-500">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"></div>
          <span className="ml-3 font-medium">Searching...</span>
        </div>
      ) : !rawQ.trim() ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-500">
          <SearchIcon className="mb-3 h-8 w-8 text-slate-400" />
          <p>Type a keyword above to start searching.</p>
        </div>
      ) : !hasResults ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-2xl bg-white border border-slate-100 shadow-sm text-slate-500">
          <p className="font-medium text-slate-700 mb-1">No results found for "{rawQ}"</p>
          <p className="text-sm">Try using different or more general keywords.</p>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="flex space-x-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-4 py-3 text-sm font-semibold transition-colors ${
                activeTab === "all" ? "border-b-2 border-blue-600 text-blue-600" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              All Results
            </button>
            <button
              onClick={() => setActiveTab("courses")}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold transition-colors ${
                activeTab === "courses" ? "border-b-2 border-blue-600 text-blue-600" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Courses <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{courses.length}</span>
            </button>
            <button
              onClick={() => setActiveTab("tasks")}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold transition-colors ${
                activeTab === "tasks" ? "border-b-2 border-blue-600 text-blue-600" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Tasks <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{tasks.length}</span>
            </button>
          </div>

          {(activeTab === "all" || activeTab === "courses") && displayCourses.length > 0 && (
            <section>
              <h2 className="mb-4 font-display text-lg text-slate-900 flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-slate-400"/> Matching Courses
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {displayCourses.map((c) => {
                  const th = getTheme(c.category_theme);
                  const btn = getTheme(c.cta_theme);
                  return (
                    <article
                      key={c.id}
                      className="flex flex-col overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm transition hover:shadow-md"
                    >
                      <div className="relative aspect-[16/10] overflow-hidden">
                        <img src={c.image_url} alt="" className="h-full w-full object-cover" />
                      </div>
                      <div className="flex flex-1 flex-col p-5">
                        <div className="mb-3 flex items-start justify-between gap-2">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${th.soft}`}>{c.category}</span>
                        </div>
                        <h2 className="font-display text-lg leading-snug text-slate-900">{c.title}</h2>
                        <p className="mt-2 text-sm text-slate-500">{c.author}</p>
                        <div className="mt-4">
                          <div className="mb-1 flex justify-between text-xs font-medium text-slate-500">
                            <span>Progress</span>
                            <span>{c.progress_percent}%</span>
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
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          )}

          {(activeTab === "all" || activeTab === "tasks") && displayTasks.length > 0 && (
            <section>
              <h2 className="mb-4 font-display text-lg text-slate-900 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-slate-400"/> Matching Tasks
              </h2>
              <ul className="grid gap-3 lg:grid-cols-2">
                {displayTasks.map((t) => (
                  <li
                    key={t.id}
                    onClick={() => navigate('/planner')}
                    className="flex cursor-pointer flex-col justify-center rounded-xl border border-slate-100 bg-white p-4 transition-colors hover:border-slate-300 hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium text-slate-900">{t.title}</h3>
                        {t.description && <p className="mt-1 line-clamp-1 text-sm text-slate-500">{t.description}</p>}
                        
                        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                          {t.status === "completed" ? (
                            <span className="rounded-full bg-emerald-100 px-2 py-0.5 font-medium text-emerald-700">Completed</span>
                          ) : (
                            <span className="rounded-full bg-blue-100 px-2 py-0.5 font-medium text-blue-700">Pending</span>
                          )}
                          
                          {t.deadline_label && (
                            <span className="font-medium text-slate-500">Due {t.deadline_label}</span>
                          )}
                          
                          {t.course_name && (
                            <span className="flex items-center gap-1 font-medium text-slate-500">
                              <span className="h-1 w-1 rounded-full bg-slate-300"></span> {t.course_name}
                            </span>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="mt-1 h-5 w-5 shrink-0 text-slate-300" />
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
