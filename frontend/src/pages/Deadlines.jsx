import { useEffect, useState } from "react";
import { api } from "../api/client";

function urgencyClass(u) {
  if (u === "today" || u === "overdue") return "bg-red-100 text-red-700";
  if (u === "soon" || u === "upcoming") return "bg-amber-100 text-amber-800";
  return "bg-slate-100 text-slate-600";
}

export function Deadlines() {
  const [items, setItems] = useState({ overdue: [], today: [], upcoming: [], later: [] });
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const tasks = await api("/api/tasks/");
        const pending = tasks.filter(t => t.status === "pending" && t.deadline);
        
        const now = new Date();
        now.setHours(0,0,0,0);

        const grouped = { overdue: [], today: [], upcoming: [], later: [] };

        pending.forEach(t => {
           const dDate = t.deadline_date ? new Date(t.deadline_date) : new Date(t.deadline);
           dDate.setHours(0,0,0,0);
           
           const diffTime = dDate - now;
           const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
           
           let group = "later";
           let urgency_label = `${diffDays} days`;
           let uClass = "later";

           if (diffDays < 0) {
             group = "overdue"; urgency_label = "Overdue"; uClass = "overdue";
           } else if (diffDays === 0) {
             group = "today"; urgency_label = "Today"; uClass = "today";
           } else if (diffDays <= 3) {
             group = "upcoming"; urgency_label = `In ${diffDays} days`; uClass = "soon";
           } else {
             group = "later"; urgency_label = `In ${diffDays} days`; uClass = "later";
           }
           
           grouped[group].push({
             id: t.id,
             title: t.title,
             description: t.description,
             group,
             urgency: uClass,
             urgency_label,
             timestamp: dDate.getTime(),
             formattedDate: new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(dDate)
           });
        });

        Object.values(grouped).forEach(arr => arr.sort((a,b) => a.timestamp - b.timestamp));

        if (!cancelled) setItems(grouped);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (err) {
    return (
      <div className="p-8">
        <p className="text-red-600">{err}</p>
      </div>
    );
  }

  const sections = [
    { key: "overdue", title: "Overdue" },
    { key: "today", title: "Due Today" },
    { key: "upcoming", title: "Upcoming (Next 3 Days)" },
    { key: "later", title: "Later" }
  ];

  const hasItems = items.overdue.length > 0 || items.today.length > 0 || items.upcoming.length > 0 || items.later.length > 0;

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10">
      <header className="mb-8">
        <h1 className="font-display text-3xl text-slate-900">Deadlines</h1>
        <p className="mt-1 text-sm text-slate-500">Stay ahead of what&apos;s due next</p>
      </header>

      <section className="mx-auto max-w-2xl rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        {!hasItems ? (
          <p className="text-center text-slate-500 py-4">No deadlines right now.</p>
        ) : (
          <div className="space-y-8">
            {sections.map(({ key, title }) => {
              const list = items[key];
              if (!list || list.length === 0) return null;

              return (
                <div key={key}>
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    {title}
                  </h3>
                  <ul className="divide-y divide-slate-100 rounded-xl border border-slate-100">
                    {list.map((d) => (
                      <li key={d.id} className="flex flex-col py-3 px-4 hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between">
                        <div className="mb-2 sm:mb-0">
                          <span className="block font-medium text-slate-900">{d.title}</span>
                          <span className="mt-0.5 block text-xs text-slate-500">{d.formattedDate}</span>
                        </div>
                        <span className={`inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-semibold ${urgencyClass(d.urgency)}`}>
                          {d.urgency_label}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
