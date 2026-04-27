import calendar
import json
import re
import asyncio
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException

from app.db.mongodb import get_database
from app.schemas.task import TaskStatus
from app.services.common import to_object_id
from app.core.config import settings


def _extract_json_object(text: str) -> dict | None:
    """
    Best-effort extraction of a JSON object from model output.
    We expect a top-level object like: {"tasks":[...]}.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to find fenced JSON first
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass

    # Fallback: first {...} block
    obj = re.search(r"\{[\s\S]*\}", text)
    if obj:
        try:
            return json.loads(obj.group(0))
        except Exception:
            return None

    return None


def _weekday_name(d: date) -> str:
    return d.strftime("%A")


def _safe_header_date(d: date) -> str:
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"


async def _get_user(user_id: str) -> dict:
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    from bson import ObjectId

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _theme_cycle(i: int) -> str:
    return ("blue", "purple", "green", "orange")[i % 4]


async def dashboard(user_id: str) -> dict:
    user = await _get_user(user_id)
    db = get_database()
    lf = user.get("learnflow") or {}
    today = date.today()
    role = str(user.get("role", "")).strip().lower()

    if role == "admin":
        courses = await db.courses.find({"owner_id": user_id}).to_list(length=None)
    else:
        all_users = await db.users.find({}, {"_id": 1, "role": 1}).to_list(length=None)
        admin_users = [u for u in all_users if str(u.get("role", "")).strip().lower() == "admin"]
        admin_ids = [str(u["_id"]) for u in admin_users]
        owner_filter = {"owner_id": {"$in": admin_ids}} if admin_ids else {"owner_id": {"$in": []}}
        courses = await db.courses.find(owner_filter).to_list(length=None)
    total_courses = len(courses)
    total_tasks = await db.tasks.count_documents({"user_id": user_id})
    completed_tasks = await db.tasks.count_documents(
        {"user_id": user_id, "status": TaskStatus.COMPLETED.value}
    )

    tc_done = completed_tasks
    tc_tot = total_tasks

    # Calculate real weekly study hours and study streak
    recent_tasks = await db.tasks.find({"user_id": user_id, "status": TaskStatus.COMPLETED.value}).to_list(length=None)
    weekly_mins = 0
    streak_dates = set()
    
    for t in recent_tasks:
        dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        if not dt: continue
        delta = (today - dt).days
        if 0 <= delta <= 7:
            weekly_mins += int(t.get("duration_minutes") or 120)
        if delta >= 0:
            streak_dates.add(dt)
            
    weekly_total = round(weekly_mins / 60.0, 1)
    
    # Simple consecutive streak calculation
    streak = 0
    check_day = today
    if check_day not in streak_dates:
        check_day = today - timedelta(days=1) # Streak holds if missed today but did yesterday
        
    while check_day in streak_dates:
        streak += 1
        check_day -= timedelta(days=1)

    kpis = [
        {
            "label": "Active Courses",
            "value": f"{total_courses} courses",
            "sublabel": None,
            "icon": "book",
            "variant": "default",
        },
        {
            "label": "Study Hours",
            "value": f"{weekly_total} hrs this week",
            "sublabel": None,
            "icon": "clock",
            "variant": "default",
        },
        {
            "label": "Tasks Completed",
            "value": f"{tc_done} / {tc_tot} total",
            "sublabel": None,
            "icon": "check",
            "variant": "default",
        },
        {
            "label": "Study Streak",
            "value": f"{streak} day streak",
            "sublabel": None,
            "icon": "bolt",
            "variant": "primary",
        },
    ]

    course_progress = []
    for i, c in enumerate(courses[:8]):
        cid = str(c["_id"])
        if role == "admin":
            prog_docs = await db.course_progress.find({"course_id": cid}).to_list(length=None)
            pct = (sum(float(d.get("progress_percent") or 0.0) for d in prog_docs) / len(prog_docs)) if prog_docs else float(c.get("progress_override") or 0)
        else:
            prog_doc = await db.course_progress.find_one({"course_id": cid, "user_id": user_id})
            pct = float((prog_doc or {}).get("progress_percent") or c.get("progress_override") or 0.0)
        theme = c.get("theme_color") or _theme_cycle(i)
        course_progress.append(
            {
                "course_id": cid,
                "title": c["title"],
                "progress_percent": round(pct, 1),
                "theme": theme,
            }
        )

    # Dynamic Today's Plan (prefer active/upcoming tasks; avoid stale completed rows)
    today_plan = []
    today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    active_q = {
        "user_id": user_id,
        "status": TaskStatus.PENDING.value,
        "$or": [
            {"deadline_date": {"$gte": today.isoformat()}},
            {"deadline": {"$gte": today_start}},
        ],
    }
    db_today_tasks = await db.tasks.find(active_q).sort([("deadline_date", 1), ("deadline", 1), ("title", 1)]).limit(4).to_list(length=4)
    for t in db_today_tasks:
        dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        delta = (dt - today).days if dt else 999
        title = t.get("title", "")
        
        kind = "assignment"
        if "watch" in title.lower() or "video" in title.lower() or "lecture" in title.lower():
            kind = "watch"
        elif "quiz" in title.lower() or "test" in title.lower():
            kind = "quiz"
            
        status = "in_progress"
        accent = "blue"
        sub = f"Due {dt.strftime('%b %d')}" if dt else None

        if delta == 0:
            status = "due_tonight"
            accent = "orange"
        
        today_plan.append({
            "id": str(t["_id"]),
            "kind": kind,
            "title": title,
            "subtitle": sub,
            "status": status,
            "accent": accent,
        })
    today_plan = today_plan[:3]

    # Always compute deadlines from real pending tasks.
    # Avoid stale/static values from old seeded profile fields.
    tasks = (
        await db.tasks.find({"user_id": user_id, "status": TaskStatus.PENDING.value})
        .sort([("deadline_date", 1), ("deadline", 1), ("title", 1)])
        .limit(10)
        .to_list(length=10)
    )
    deadlines = []
    for t in tasks:
        dl = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        if not dl:
            continue
        delta = (dl - today).days
        if delta <= 0:
            urg, label = "today", "Today"
        elif delta <= 2:
            urg, label = "soon", f"{delta} days"
        else:
            urg, label = "later", f"{delta} days"
        deadlines.append(
            {
                "id": str(t["_id"]),
                "title": t.get("title", "Task"),
                "urgency_label": label,
                "urgency": urg,
            }
        )
        if len(deadlines) >= 3:
            break

    # Dynamic Weekly Hours Chart (Mon=0 to Sun=6)
    weekly = [0.0] * 7
    for t in recent_tasks:
        dt_val = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        if not dt_val: continue
        delta = (today - dt_val).days
        if 0 <= delta <= 7:
            wd = dt_val.weekday()
            mins = int(t.get("duration_minutes") or 120)
            weekly[wd] += (mins / 60.0)
    weekly = [round(w, 1) for w in weekly]
    
    first = user.get("full_name", "Learner").split()[0]
    pending = await db.tasks.count_documents(
        {"user_id": user_id, "status": TaskStatus.PENDING.value}
    )

    return {
        "greeting_name": first,
        "header_date": _safe_header_date(today),
        "task_summary": f"{pending} tasks due soon",
        "kpis": kpis,
        "course_progress": course_progress[:4],
        "today_plan": today_plan,
        "deadlines": deadlines[:3],
        "weekly_hours": weekly,
        "weekly_hours_label": f"This Week: {weekly_total} hrs",
    }


_PERIOD_KEY = {"month": "analytics_month", "quarter": "analytics_quarter", "all": "analytics_all"}


async def analytics(user_id: str, period: str) -> dict:
    user = await _get_user(user_id)
    db = get_database()
    today = date.today()

    period = period if period in ("month", "quarter", "all") else "month"
    days_in_period = 30 if period == "month" else (90 if period == "quarter" else 365)
    start_date = None if period == "all" else today - timedelta(days=days_in_period)

    # Fetch all tasks for user
    tasks = await db.tasks.find({"user_id": user_id}).to_list(length=None)

    # Process Tasks
    period_tasks = []
    completed_period_tasks = []
    for t in tasks:
        dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        if not dt:
            continue
        if start_date is None or dt >= start_date:
            period_tasks.append(t)
            if t.get("status") == TaskStatus.COMPLETED.value:
                completed_period_tasks.append(t)

    total_period = len(period_tasks)
    num_completed = len(completed_period_tasks)
    overall_score = (num_completed / total_period * 100) if total_period > 0 else 0.0

    hours_studied = sum(int(t.get("duration_minutes") or 120) for t in completed_period_tasks) / 60.0
    avg_daily = hours_studied / days_in_period

    kpis = [
        {"label": "Completion Rate", "value": f"{overall_score:.1f}%", "badge": "Task Ratio", "badge_tone": "success" if overall_score >= 70 else "warning"},
        {"label": "Hours Studied", "value": f"{hours_studied:.1f}", "badge": "In Period", "badge_tone": "info"},
        {"label": "Assignments Done", "value": f"{num_completed} / {total_period}", "badge": f"{total_period - num_completed} pending", "badge_tone": "warning" if total_period > num_completed else "success"},
        {"label": "Avg Daily Study", "value": f"{avg_daily:.1f} hrs", "badge": f"{days_in_period} days", "badge_tone": "neutral"},
    ]

    # Monthly Hours (Last 6 months)
    monthly_data = {}
    for i in range(5, -1, -1):
        m_date = today - timedelta(days=30 * i)
        m_name = m_date.strftime("%b")
        if m_name not in monthly_data:
            monthly_data[m_name] = 0

    for t in tasks:
        if t.get("status") != TaskStatus.COMPLETED.value:
            continue
        dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        if not dt:
            continue
        if (today - dt).days <= 180:
            m_name = dt.strftime("%b")
            if m_name in monthly_data:
                monthly_data[m_name] += int(t.get("duration_minutes") or 120)

    monthly_hours = []
    for m_name, mins in monthly_data.items():
        monthly_hours.append({
            "month": m_name,
            "hours": round(mins / 60.0, 1),
            "highlight": m_name == today.strftime("%b")
        })

    # Subjects & Courses
    role = str(user.get("role", "")).strip().lower()
    if role == "admin":
        courses = await db.courses.find({"owner_id": user_id}).to_list(length=None)
    else:
        all_users = await db.users.find({}, {"_id": 1, "role": 1}).to_list(length=None)
        admin_users = [u for u in all_users if str(u.get("role", "")).strip().lower() == "admin"]
        admin_ids = [str(u["_id"]) for u in admin_users]
        owner_filter = {"owner_id": {"$in": admin_ids}} if admin_ids else {"owner_id": {"$in": []}}
        courses = await db.courses.find(owner_filter).to_list(length=None)
    course_map = {str(c["_id"]): c for c in courses}

    subjects = []
    for c in courses:
        cid = str(c["_id"])
        c_tasks = [t for t in tasks if t.get("course_id") == cid]
        course_task_count = len(c_tasks)
        done = sum(1 for t in c_tasks if t.get("status") == TaskStatus.COMPLETED.value)
        if role == "admin":
            prog_docs = await db.course_progress.find({"course_id": cid}).to_list(length=None)
            pct = (sum(float(d.get("progress_percent") or 0.0) for d in prog_docs) / len(prog_docs)) if prog_docs else float(c.get("progress_override") or 0)
        else:
            prog_doc = await db.course_progress.find_one({"course_id": cid, "user_id": user_id})
            pct = float((prog_doc or {}).get("progress_percent") or c.get("progress_override") or 0.0)
        subjects.append({
            "name": c.get("title", "Unknown"),
            "percent": round(pct),
            "theme": c.get("theme_color") or "blue"
        })

    subjects = sorted(subjects, key=lambda x: x["percent"], reverse=True)[:4]
    if not subjects:
        subjects = [{"name": "No courses found", "percent": 0, "theme": "neutral"}]

    # Performance
    performance = []
    for c in courses[:5]:
        cid = str(c["_id"])
        c_tasks = [t for t in tasks if t.get("course_id") == cid]
        completed_c_tasks = [t for t in c_tasks if t.get("status") == TaskStatus.COMPLETED.value]
        
        course_task_count = len(c_tasks)
        done = len(completed_c_tasks)
        if role == "admin":
            prog_docs = await db.course_progress.find({"course_id": cid}).to_list(length=None)
            pct = (sum(float(d.get("progress_percent") or 0.0) for d in prog_docs) / len(prog_docs)) if prog_docs else float(c.get("progress_override") or 0)
        else:
            prog_doc = await db.course_progress.find_one({"course_id": cid, "user_id": user_id})
            pct = float((prog_doc or {}).get("progress_percent") or c.get("progress_override") or 0.0)

        has_overdue = False
        for t in c_tasks:
             if t.get("status") != TaskStatus.COMPLETED.value:
                  dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
                  if dt and dt < today:
                      has_overdue = True
                      break

        if len(c_tasks) == 0:
            status = "New"
            status_tone = "neutral"
            score_tone = "neutral"
        else:
            status = "Needs Focus" if has_overdue else ("Excellent" if pct >= 80 else "On Track")
            status_tone = "warning" if has_overdue else "success"
            score_tone = "success" if pct >= 70 else "warning"

        performance.append({
             "course": c.get("title", "Course"),
             "last_score": f"{len(completed_c_tasks)} / {len(c_tasks)} tasks",
             "score_tone": score_tone,
             "progress_percent": round(pct),
             "progress_theme": c.get("theme_color") or "blue",
             "status": status,
             "status_tone": status_tone,
             "trend": "Active" if len(c_tasks) > 0 else "Empty",
        })

    if not performance:
        performance = [{
            "course": "No courses created yet",
            "last_score": "-",
            "score_tone": "neutral",
            "progress_percent": 0,
            "progress_theme": "blue",
            "status": "New",
            "status_tone": "info",
            "trend": "—",
        }]

    return {
        "period": period,
        "kpis": kpis,
        "monthly_hours": monthly_hours,
        "subjects": subjects,
        "performance": performance,
    }


def _task_deadline_as_date(dl: datetime | date | str | None) -> date | None:
    if dl is None:
        return None
    if isinstance(dl, datetime):
        return dl.date()
    if isinstance(dl, date):
        return dl
    if isinstance(dl, str):
        try:
            return datetime.fromisoformat(dl.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def _week_bounds(d: date) -> tuple[date, date]:
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def _date_range_to_task_query(
    *,
    user_id: str,
    start: date,
    end_exclusive: date,
    include_completed: bool = False,
) -> dict:
    """Mongo query for tasks in [start, end_exclusive).

    Uses `deadline_date` (YYYY-MM-DD) when present, and falls back to datetime range for older docs.
    """
    start_s = start.isoformat()
    end_s = end_exclusive.isoformat()
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_exclusive, datetime.min.time(), tzinfo=timezone.utc)
    q = {
        "user_id": user_id,
        "$or": [
            {"deadline_date": {"$gte": start_s, "$lt": end_s}},
            {"deadline": {"$gte": start_dt, "$lt": end_dt}},
        ],
    }
    if not include_completed:
        q["status"] = {"$ne": TaskStatus.COMPLETED.value}
    return q


def _tasks_to_planner_blocks(
    tasks: list[dict],
    *,
    highlight_first_pending: bool = False,
    max_blocks: int = 80,
) -> list[dict]:
    capped = tasks[:max_blocks]
    first_pending_idx: int | None = None
    if highlight_first_pending:
        for j, t in enumerate(capped):
            if t.get("status") != TaskStatus.COMPLETED.value:
                first_pending_idx = j
                break
    blocks: list[dict] = []
    for i, t in enumerate(capped):
        if t.get("status") == TaskStatus.COMPLETED.value:
            st = "done"
        elif highlight_first_pending and first_pending_idx is not None and i == first_pending_idx:
            st = "now"
        else:
            st = "pending"
        dl = _task_deadline_as_date(t.get("deadline"))
        dl_str = dl.strftime("%a %b %d") if dl else ""
        desc = (t.get("description") or "").strip()
        if desc:
            sub = f"{dl_str} · {desc[:40]}" if dl_str else desc[:50]
        else:
            sub = dl_str or "Task"
        dur = int(t.get("duration_minutes") or 120)
        hour = 8 + (i % 6) * 2
        ampm = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        blocks.append(
            {
                "id": str(t["_id"]),
                "time": f"{hour_12}:00 {ampm}",
                "title": t.get("title", "Task"),
                "subtitle": sub,
                "duration_minutes": dur,
                "duration_label": f"{dur//60} hrs" if dur >= 60 and dur % 60 == 0 else (f"{dur} min" if dur < 60 else f"{dur//60}h {dur%60}m"),
                "status": st,
            }
        )
    return blocks


def _default_demo_blocks(lf: dict) -> list[dict]:
    return [
        {
            "time": "—",
            "title": "No tasks scheduled for today",
            "subtitle": "Click '+ Add Task' to add a new task to your planner.",
            "duration_label": "—",
            "status": "scheduled",
        }
    ]


def _empty_period_blocks() -> list[dict]:
    return [
        {
            "time": "—",
            "title": "No tasks with deadlines in this period",
            "subtitle": "Add a task from the planner or choose another day on the calendar.",
            "duration_label": "—",
            "status": "scheduled",
        }
    ]


def _apply_first_pending_highlight(blocks: list[dict]) -> None:
    for b in blocks:
        tid = b.get("id")
        if not tid or b.get("status") == "done":
            continue
        b["status"] = "now"
        return


def _compose_day_blocks_from_tasks_and_saved(
    day_tasks: list[dict],
    saved_blocks: list[dict] | None,
) -> list[dict]:
    """Keep manual / auto-scheduled order when blocks were saved with task ids; sync fields from DB."""
    tasks_by_id = {str(t["_id"]): t for t in day_tasks}
    out: list[dict] = []
    seen: set[str] = set()

    if saved_blocks:
        for sb in saved_blocks:
            tid = sb.get("id")
            if not tid or tid not in tasks_by_id:
                continue
            t = tasks_by_id[tid]
            st = "done" if t.get("status") == TaskStatus.COMPLETED.value else sb.get("status", "pending")
            if st not in ("done", "now", "pending", "scheduled"):
                st = "pending"
            dl = _task_deadline_as_date(t.get("deadline"))
            dl_str = dl.strftime("%a %b %d") if dl else ""
            desc = (t.get("description") or "").strip()
            if desc:
                sub = f"{dl_str} · {desc[:40]}" if dl_str else desc[:50]
            else:
                sub = dl_str or sb.get("subtitle", "Task")
            out.append(
                {
                    **sb,
                    "title": t.get("title", sb.get("title", "Task")),
                    "subtitle": sub,
                    "status": st,
                    "duration_minutes": int(t.get("duration_minutes") or sb.get("duration_minutes") or 120),
                    "duration_label": sb.get("duration_label")
                    or (
                        f"{int(t.get('duration_minutes') or 120)//60} hrs"
                        if int(t.get("duration_minutes") or 120) >= 60 and int(t.get("duration_minutes") or 120) % 60 == 0
                        else (
                            f"{int(t.get('duration_minutes') or 120)} min"
                            if int(t.get("duration_minutes") or 120) < 60
                            else f"{int(t.get('duration_minutes') or 120)//60}h {int(t.get('duration_minutes') or 120)%60}m"
                        )
                    ),
                }
            )
            seen.add(tid)

    for t in day_tasks:
        tid = str(t["_id"])
        if tid in seen:
            continue
            
        dur = int(t.get("duration_minutes") or 120)
        dur_label = f"{dur//60} hrs" if dur >= 60 and dur % 60 == 0 else (f"{dur} min" if dur < 60 else f"{dur//60}h {dur%60}m")
        
        dl = _task_deadline_as_date(t.get("deadline"))
        dl_str = dl.strftime("%a %b %d") if dl else ""
        desc = (t.get("description") or "").strip()
        sub = f"{dl_str} · {desc[:40]}" if dl_str else desc[:50]
        if not desc:
            sub = dl_str or "Task"
            
        out.append({
            "id": tid,
            "time": "TBD",
            "title": t.get("title", "Task"),
            "subtitle": sub,
            "duration_minutes": dur,
            "duration_label": dur_label,
            "status": "pending",
        })

    if not out:
        # If still empty, return empty list instead of forcing auto-schedule logic
        return []

    for b in out:
        tid = b.get("id")
        if tid and b.get("status") != "done":
            b["status"] = "pending"
    _apply_first_pending_highlight(out)
    return out


def _build_calendar(year: int, month: int, today: date, deadline_days: set[int]) -> list[dict]:
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    weeks = cal.monthdatescalendar(year, month)
    days: list[dict] = []
    for week in weeks:
        for d in week:
            days.append(
                {
                    "day": d.day,
                    "is_current_month": d.month == month,
                    "is_today": d == today,
                    "is_deadline": d.month == month and d.day in deadline_days,
                }
            )
    return days


async def planner(user_id: str, view: str, ref: date | None) -> dict:
    user = await _get_user(user_id)
    db = get_database()
    lf = user.get("learnflow") or {}
    today = date.today()
    day = ref or today
    view = view if view in ("day", "week", "month") else "day"

    y, m = day.year, day.month
    # Month bounds (used for calendar highlighting regardless of selected view).
    month_start = date(y, m, 1)
    next_month = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

    # Fetch only tasks in the visible calendar month for deadline highlights.
    month_q = _date_range_to_task_query(
        user_id=user_id,
        start=month_start,
        end_exclusive=next_month,
        include_completed=True,
    )
    month_tasks = await db.tasks.find(month_q, {"deadline": 1, "deadline_date": 1}).to_list(length=2000)

    deadline_days = set(lf.get("planner_deadline_days", []))
    if not deadline_days:
        for t in month_tasks:
            # Prefer deadline_date if present (timezone-safe).
            if (ds := t.get("deadline_date")) and isinstance(ds, str) and len(ds) >= 10:
                try:
                    d0 = date.fromisoformat(ds[:10])
                    if d0.year == y and d0.month == m:
                        deadline_days.add(d0.day)
                    continue
                except ValueError:
                    pass
            dl = _task_deadline_as_date(t.get("deadline"))
            if dl and dl.year == y and dl.month == m:
                deadline_days.add(dl.day)

    cal_title = f"{calendar.month_name[m]} {y}"
    cal_days = _build_calendar(y, m, today, deadline_days)

    blocks_doc = await db.planner_blocks.find_one({"user_id": user_id, "day": day.isoformat()})

    blocks: list[dict]
    timeline_title: str
    summary_hrs: str

    if view == "week":
        wk_start, wk_end = _week_bounds(day)
        wk_end_excl = wk_end + timedelta(days=1)
        week_q = _date_range_to_task_query(
            user_id=user_id,
            start=wk_start,
            end_exclusive=wk_end_excl,
            include_completed=True,
        )
        week_tasks = await db.tasks.find(week_q).sort([("deadline_date", 1), ("deadline", 1), ("title", 1)]).to_list(length=500)
        if week_tasks:
            blocks = _tasks_to_planner_blocks(week_tasks, highlight_first_pending=True, max_blocks=80)
            timeline_title = f"Week of {wk_start.strftime('%b %d')} – {wk_end.strftime('%b %d, %Y')}"
            summary_hrs = f"{len(week_tasks)} tasks with deadlines this week"
        else:
            blocks = _empty_period_blocks()
            timeline_title = f"Week of {wk_start.strftime('%b %d')} – {wk_end.strftime('%b %d, %Y')}"
            summary_hrs = "No deadlines this week"

    elif view == "month":
        full_month_tasks = await db.tasks.find(month_q).sort([("deadline_date", 1), ("deadline", 1), ("title", 1)]).to_list(length=1000)
        if full_month_tasks:
            blocks = _tasks_to_planner_blocks(full_month_tasks, highlight_first_pending=True, max_blocks=60)
            timeline_title = f"{calendar.month_name[m]} {y} — all due dates"
            summary_hrs = f"{len(full_month_tasks)} tasks due this month"
        else:
            blocks = _empty_period_blocks()
            timeline_title = f"{calendar.month_name[m]} {y}"
            summary_hrs = "No deadlines this month"

    else:
        day_end_excl = day + timedelta(days=1)
        day_q = _date_range_to_task_query(
            user_id=user_id,
            start=day,
            end_exclusive=day_end_excl,
            include_completed=True,
        )
        day_tasks = await db.tasks.find(day_q).sort([("title", 1)]).to_list(length=300)
        saved = blocks_doc.get("blocks") if blocks_doc else None
        if day_tasks:
            blocks = _compose_day_blocks_from_tasks_and_saved(day_tasks, saved)
            timeline_title = f"{_weekday_name(day)}, {_safe_header_date(day)}"
            summary_hrs = lf.get("planner_timeline_summary") or f"{len(blocks)} tasks scheduled"
        elif saved:
            # Saved layout exists, but no tasks matched for this day.
            # Load only tasks referenced by saved blocks (fast + avoids wrong month/day bleed).
            ids: list[str] = []
            for x in saved:
                tid = x.get("id")
                if tid:
                    ids.append(str(tid))
            tasks_by_id: dict[str, date | None] = {}
            if ids:
                docs = []
                for tid in ids:
                    try:
                        docs.append({"_id": to_object_id(tid, "task_id")})
                    except HTTPException:
                        continue
                if docs:
                    found = await db.tasks.find({"user_id": user_id, "$or": docs}, {"deadline": 1, "deadline_date": 1}).to_list(length=len(docs))
                    for t in found:
                        tid_s = str(t["_id"])
                        if (ds := t.get("deadline_date")) and isinstance(ds, str) and len(ds) >= 10:
                            try:
                                tasks_by_id[tid_s] = date.fromisoformat(ds[:10])
                                continue
                            except ValueError:
                                pass
                        tasks_by_id[tid_s] = _task_deadline_as_date(t.get("deadline"))

            blocks = []
            for x in saved:
                tid = x.get("id")
                if not tid:
                    blocks.append(x)
                    continue
                tid_s = str(tid)
                if tasks_by_id.get(tid_s) == day:
                    blocks.append(x)
            if not blocks:
                blocks = _default_demo_blocks(lf)
            timeline_title = f"{_weekday_name(day)}, {_safe_header_date(day)}"
            summary_hrs = lf.get("planner_timeline_summary") or f"{len(blocks)} blocks"
        else:
            blocks = _default_demo_blocks(lf)
            timeline_title = f"{_weekday_name(day)}, {_safe_header_date(day)}"
            summary_hrs = lf.get("planner_timeline_summary") or f"{len(blocks)} tasks scheduled"

    ai_text = lf.get(
        "ai_recommendation",
        "Based on your deadlines, study 2h React today + 1.5h Data Science tonight for optimal retention.",
    )

    return {
        "view": view,
        "calendar_title": cal_title,
        "calendar_weekday_labels": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        "calendar_days": cal_days,
        "calendar": {
            "title": cal_title,
            "weekday_labels": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
            "days": cal_days,
        },
        "ai_recommendation": ai_text,
        "timeline_title": timeline_title,
        "timeline_subtitle": summary_hrs,
        "blocks": blocks,
    }


async def save_planner_blocks(user_id: str, day: date, blocks: list[dict]) -> dict:
    await _get_user(user_id)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    await db.planner_blocks.update_one(
        {"user_id": user_id, "day": day.isoformat()},
        {"$set": {"user_id": user_id, "day": day.isoformat(), "blocks": blocks}},
        upsert=True,
    )
    return {"ok": True}


async def clear_planner_blocks_for_day(user_id: str, ref: date | None) -> dict:
    await _get_user(user_id)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    d = ref or date.today()
    await db.planner_blocks.delete_one({"user_id": user_id, "day": d.isoformat()})
    return {"ok": True, "cleared_day": d.isoformat()}


def _minutes_to_label(minutes: int) -> str:
    m = max(5, int(minutes))
    if m < 60:
        return f"{m} min"
    h, r = divmod(m, 60)
    if r == 0:
        return f"{h} hrs"
    return f"{h}h {r}m"


def _schedule_times(
    tasks: list[dict],
    *,
    start_minutes: int = 20 * 60,
    end_minutes: int = 32 * 60,
    gap_minutes: int = 15,
) -> list[dict]:
    """Assign non-overlapping timeslots sequentially."""
    cur = start_minutes
    out: list[dict] = []
    for t in tasks:
        dur = int(t.get("duration_minutes") or 120)
        dur = max(5, min(dur, 24 * 60))
        # wrap to next morning if overflow
        if cur + dur > end_minutes:
            cur = start_minutes
        hh = (cur // 60) % 24
        mm = cur % 60
        ampm = "AM" if hh < 12 else "PM"
        hh_12 = hh % 12
        if hh_12 == 0:
            hh_12 = 12
        out.append({**t, "_slot_time": f"{hh_12}:{mm:02d} {ampm}", "_slot_dur": dur})
        cur += dur + gap_minutes
    return out


async def auto_schedule_day(user_id: str, ref: date | None) -> dict:
    """Backend-driven auto-schedule for a specific day.

    - Pull tasks due on that day (pending + completed)
    - Assign times sequentially (no overlaps)
    - Save layout to planner_blocks so UI stays stable
    - Return standard planner response (day view)
    """
    await _get_user(user_id)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    day = ref or date.today()
    day_end = day + timedelta(days=1)

    q = {
        "user_id": user_id,
        "$or": [
            # Pending tasks due before day_end (includes overdue + today)
            {
                "status": {"$ne": TaskStatus.COMPLETED.value},
                "$or": [
                    {"deadline_date": {"$lt": day_end.isoformat()}},
                    {"deadline": {"$lt": datetime.combine(day_end, datetime.min.time(), tzinfo=timezone.utc)}},
                ]
            },
            # Completed tasks due exactly on day
            {
                "status": TaskStatus.COMPLETED.value,
                "$or": [
                    {"deadline_date": {"$gte": day.isoformat(), "$lt": day_end.isoformat()}},
                    {
                        "deadline": {
                            "$gte": datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                            "$lt": datetime.combine(day_end, datetime.min.time(), tzinfo=timezone.utc),
                        }
                    },
                ]
            }
        ],
    }
    tasks = await db.tasks.find(q).sort([("status", 1), ("title", 1)]).to_list(length=500)

    # map course_id -> title for nicer subtitles
    course_ids = list({t.get("course_id") for t in tasks if t.get("course_id")})
    courses = []
    if course_ids:
        courses = await db.courses.find({"_id": {"$in": [to_object_id(cid, "course_id") for cid in course_ids]}}).to_list(length=len(course_ids))
    course_title_by_id = {str(c["_id"]): c.get("title", "Course") for c in courses}

    scheduled = _schedule_times(tasks)
    blocks: list[dict] = []
    # status mapping + "now" highlight for first pending
    first_pending = None
    for t in scheduled:
        if t.get("status") != TaskStatus.COMPLETED.value:
            first_pending = str(t["_id"])
            break
    for t in scheduled:
        tid = str(t["_id"])
        done = t.get("status") == TaskStatus.COMPLETED.value
        st = "done" if done else ("now" if tid == first_pending else "pending")
        ct = course_title_by_id.get(t.get("course_id"), "Course")
        desc = (t.get("description") or "").strip()
        sub = f"{ct} · {desc[:60]}" if desc else ct
        dur = int(t.get("_slot_dur") or t.get("duration_minutes") or 120)
        blocks.append(
            {
                "id": tid,
                "time": t.get("_slot_time") or "08:00",
                "title": t.get("title", "Task"),
                "subtitle": sub,
                "duration_minutes": dur,
                "duration_label": _minutes_to_label(dur),
                "status": st,
            }
        )

    await db.planner_blocks.update_one(
        {"user_id": user_id, "day": day.isoformat()},
        {"$set": {"user_id": user_id, "day": day.isoformat(), "blocks": blocks}},
        upsert=True,
    )
    # Return standard planner response (day view)
    return await planner(user_id, "day", day)


async def apply_ai_recommendation(user_id: str, ref: date | None) -> dict:
    """Create a couple of suggested tasks (if needed) and auto-schedule the day."""
    await _get_user(user_id)
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    day = ref or date.today()

    # Pick a course to attach suggested tasks to.
    # Learners don't own courses, so we just pick any available course.
    course = await db.courses.find_one({})
    if not course:
        # No courses exist in DB => just run auto-schedule
        return await auto_schedule_day(user_id, day)
    course_id = str(course["_id"])

    # Create suggestions and optionally an updated message.
    day_end = day + timedelta(days=1)
    today_q = {
        "user_id": user_id,
        "$or": [
            {"deadline_date": {"$gte": day.isoformat(), "$lt": day_end.isoformat()}},
            {
                "deadline": {
                    "$gte": datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                    "$lt": datetime.combine(day_end, datetime.min.time(), tzinfo=timezone.utc),
                }
            },
        ],
    }
    existing_today = await db.tasks.count_documents(today_q)
    
    now = datetime.now(timezone.utc)

    suggested_docs: list[dict] | None = None
    ai_message: str | None = None
    if settings.gemini_api_key:
        try:
            from google import genai  # type: ignore

            courses = await db.courses.find({}).to_list(length=20)
            course_list = [
                {
                    "id": str(c["_id"]),
                    "title": c.get("title"),
                    "category": c.get("category"),
                    "category_theme": c.get("category_theme"),
                }
                for c in courses
            ]
            course_ids = {c["id"] for c in course_list}

            prompt = {
                "selected_day": day.isoformat(),
                "courses": course_list,
                "tasks_due_today_already": existing_today,
                "instructions": (
                    "Generate 1 to 3 study tasks for the selected day to supplement existing tasks. "
                    "Tasks must align with the user's courses. "
                    "Return ONLY valid JSON of the form: "
                    "{\"tasks\":[{\"title\":string,\"description\":string,\"duration_minutes\":int,\"video_url\":string|null,\"course_id\":string}], \"message\": string}. "
                    "Rules: duration_minutes must be an integer between 30 and 120. "
                    "video_url must be null or a valid YouTube URL. "
                    "course_id must be one of the provided course ids. "
                    "The 'message' should be a short, encouraging 1-sentence summary of your recommendation. "
                    "Do not include any extra text."
                ),
            }

            client = genai.Client(api_key=settings.gemini_api_key)
            # Use a thread because the SDK call is synchronous.
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model,
                contents=json.dumps(prompt),
            )
            text = getattr(resp, "text", None) or str(resp)
            parsed = _extract_json_object(text) or {}
            tasks = parsed.get("tasks")
            if parsed.get("message"):
                ai_message = parsed.get("message")

            if isinstance(tasks, list) and tasks:
                out: list[dict] = []
                for t in tasks[:4]:
                    if not isinstance(t, dict):
                        continue
                    cid = str(t.get("course_id") or "")
                    if cid not in course_ids:
                        # Fallback to the previously picked first course.
                        cid = course_id
                    title = str(t.get("title") or "").strip()
                    description = str(t.get("description") or "").strip()
                    duration_minutes = t.get("duration_minutes")
                    try:
                        duration_minutes_i = int(duration_minutes)
                    except Exception:
                        duration_minutes_i = 120
                    duration_minutes_i = max(5, min(duration_minutes_i, 24 * 60))

                    video_url = t.get("video_url")
                    if video_url is None:
                        video_url_s = None
                    else:
                        video_url_s = str(video_url)
                        # Keep only YouTube-ish URLs; otherwise drop to None.
                        if "youtube.com" not in video_url_s and "youtu.be" not in video_url_s:
                            video_url_s = None

                    if not title:
                        continue
                    out.append(
                        {
                            "course_id": cid,
                            "user_id": user_id,
                            "title": title,
                            "description": description,
                            "deadline": datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                            "deadline_date": day.isoformat(),
                            "duration_minutes": duration_minutes_i,
                            "status": TaskStatus.PENDING.value,
                            "video_url": video_url_s,
                            "created_at": now,
                        }
                    )

                suggested_docs = out
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Safety: never block scheduling due to Gemini issues.
            suggested_docs = []
            ai_message = f"AI could not generate tasks due to an error: {str(e)[:50]}..."
        
    if suggested_docs:
        await db.tasks.insert_many(suggested_docs)
        
    if ai_message:
        from bson import ObjectId
        ai_message_display = ai_message + " Tasks generated successfully! Click 'Auto-Schedule' above to place them on your timeline."
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"learnflow.ai_recommendation": ai_message_display}}
        )

    # Return current planner state WITHOUT auto-scheduling
    return await planner(user_id, "day", day)


async def courses_catalog(current_user: dict, status_filter: str) -> dict:
    user_id = current_user["id"]
    role = str(current_user.get("role", "")).strip().lower()
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    from bson import ObjectId

    if role == "admin":
        owner_filter: dict = {"owner_id": user_id}
    else:
        all_users = await db.users.find({}, {"_id": 1, "role": 1}).to_list(length=None)
        admin_users = [u for u in all_users if str(u.get("role", "")).strip().lower() == "admin"]
        admin_ids = [str(u["_id"]) for u in admin_users]
        owner_filter = {"owner_id": {"$in": admin_ids}} if admin_ids else {"owner_id": {"$in": []}}

    raw = await db.courses.find(owner_filter).to_list(length=None)

    cards = []
    active = 0
    completed = 0
    total_completed_learners = 0
    for c in raw:
        cid = str(c["_id"])
        progress_docs = await db.course_progress.find({"course_id": cid}).to_list(length=None)

        if role == "admin":
            completed_docs = [p for p in progress_docs if p.get("status") == "completed"]
            in_progress_docs = [p for p in progress_docs if p.get("status") != "completed"]

            completed += 1 if completed_docs else 0
            active += 1 if in_progress_docs or not completed_docs else 0
            total_completed_learners += len(completed_docs)

            if status_filter == "completed" and not completed_docs:
                continue
            if status_filter == "in_progress" and not in_progress_docs:
                continue

            learner_ids = [p.get("user_id") for p in progress_docs if p.get("user_id")]
            users_by_id = {}
            if learner_ids:
                learner_users = await db.users.find({"_id": {"$in": [ObjectId(uid) for uid in learner_ids if ObjectId.is_valid(uid)]}}, {"full_name": 1}).to_list(length=None)
                users_by_id = {str(u["_id"]): u.get("full_name") or "Learner" for u in learner_users}

            completed_names = [users_by_id.get(p.get("user_id"), "Learner") for p in completed_docs][:3]
            in_progress_names = [users_by_id.get(p.get("user_id"), "Learner") for p in in_progress_docs][:3]
            pct = round((len(completed_docs) / len(progress_docs) * 100.0), 1) if progress_docs else 0.0
            st = "completed" if completed_docs and not in_progress_docs else "in_progress"
        else:
            progress_doc = await db.course_progress.find_one({"course_id": cid, "user_id": user_id})
            pct = round(float((progress_doc or {}).get("progress_percent") or 0.0), 1)
            
            if not progress_doc or pct == 0.0:
                st = "not_started"
            elif (progress_doc or {}).get("status") == "completed" or pct >= 100:
                st = "completed"
            else:
                st = "in_progress"

            if st == "completed":
                completed += 1
            elif st == "in_progress":
                active += 1

            if status_filter != "all" and st != status_filter:
                continue

            completed_names = []
            in_progress_names = []

        cat_theme = c.get("category_theme") or "blue"
        cta_theme = c.get("cta_theme") or cat_theme
        cta_label = "Completed" if pct >= 100 else "Continue Learning"

        cards.append(
            {
                "id": cid,
                "title": c["title"],
                "category": c.get("category") or "General",
                "category_theme": cat_theme,
                "image_url": c.get("image_url") or "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
                "author": c.get("author") or "Instructor",
                "module_count": int(c.get("module_count") or 8),
                "certificate_eligible": bool(c.get("certificate_eligible", True)),
                "hours_remaining_label": c.get("hours_remaining_label"),
                "progress_percent": pct,
                "cta_theme": cta_theme,
                "status": st,
                "cta_label": cta_label,
                "youtube_url": c.get("youtube_url"),
                "learner_completed_count": len(completed_docs) if role == "admin" else 0,
                "learner_in_progress_count": len(in_progress_docs) if role == "admin" else 0,
                "learner_completed_names": completed_names,
                "learner_in_progress_names": in_progress_names,
            }
        )

    summary = (
        f"{len(cards)} courses - {total_completed_learners} learners completed"
        if role == "admin"
        else f"{active} active courses - {completed} completed"
    )
    return {"summary": summary, "courses": cards}


async def global_search(user_id: str, query: str) -> dict:
    await _get_user(user_id)
    db = get_database()
    if not query.strip():
        return {"courses": [], "tasks": []}
        
    regex_q = {"$regex": query.strip(), "$options": "i"}
    
    # 1. Search Courses
    course_q = {
        "owner_id": user_id,
        "$or": [
            {"title": regex_q},
            {"description": regex_q},
            {"category": regex_q}
        ]
    }
    raw_courses = await db.courses.find(course_q).to_list(length=100)
    
    course_cards = []
    for c in raw_courses:
        cid = str(c["_id"])
        course_task_count = await db.tasks.count_documents({"course_id": cid})
        done = await db.tasks.count_documents(
            {"course_id": cid, "status": TaskStatus.COMPLETED.value}
        )
        pct = (done / course_task_count * 100.0) if course_task_count else float(c.get("progress_override") or 0)
        pct = round(pct, 1)
        st = c.get("course_status") or "in_progress"
        cat_theme = c.get("category_theme") or "blue"
        cta_theme = c.get("cta_theme") or cat_theme
        cta_label = "Completed" if pct >= 100 else "Continue Learning"

        course_cards.append(
            {
                "id": cid,
                "title": c["title"],
                "category": c.get("category") or "General",
                "category_theme": cat_theme,
                "image_url": c.get("image_url") or "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
                "author": c.get("author") or "Instructor",
                "module_count": int(c.get("module_count") or 8),
                "certificate_eligible": bool(c.get("certificate_eligible", True)),
                "hours_remaining_label": c.get("hours_remaining_label"),
                "progress_percent": pct,
                "cta_theme": cta_theme,
                "status": st if st in ("in_progress", "completed", "saved") else "in_progress",
                "cta_label": cta_label,
                "youtube_url": c.get("youtube_url"),
            }
        )
        
    # 2. Search Tasks
    task_q = {
        "user_id": user_id,
        "$or": [
            {"title": regex_q},
            {"description": regex_q}
        ]
    }
    raw_tasks = await db.tasks.find(task_q).to_list(length=100)
    
    course_ids = list({t.get("course_id") for t in raw_tasks if t.get("course_id")})
    courses = []
    if course_ids:
        courses = await db.courses.find({"_id": {"$in": [to_object_id(cid, "course_id") for cid in course_ids]}}).to_list(length=len(course_ids))
    course_title_by_id = {str(cc["_id"]): cc.get("title", "Course") for cc in courses}

    task_items = []
    for t in raw_tasks:
        dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        dt_label = dt.strftime("%b %d, %Y") if dt else None
        c_title = course_title_by_id.get(str(t.get("course_id")))
        
        task_items.append({
            "id": str(t["_id"]),
            "title": t.get("title", ""),
            "description": t.get("description", ""),
            "status": t.get("status", "pending"),
            "course_name": c_title,
            "deadline_label": dt_label
        })
        
    return {
        "courses": course_cards,
        "tasks": task_items
    }


async def get_smart_notifications(user_id: str) -> dict:
    await _get_user(user_id)
    db = get_database()
    today = date.today()
    
    notifications = []
    
    # 1. Overdue and Due Today Tasks
    pending_tasks = await db.tasks.find({"user_id": user_id, "status": TaskStatus.PENDING.value}).to_list(length=100)
    for t in pending_tasks:
        dt = _task_deadline_as_date(t.get("deadline_date") or t.get("deadline"))
        if not dt:
            continue
        delta = (dt - today).days
        if delta < 0:
            notifications.append({
                "id": f"alert_{t['_id']}",
                "title": "Overdue Deadline",
                "message": f"Task '{t.get('title')}' is overdue by {-delta} day(s).",
                "type": "alert",
                "timestamp": t.get("deadline_date") or dt.strftime("%b %d")
            })
        elif delta == 0:
            notifications.append({
                "id": f"warn_{t['_id']}",
                "title": "Due Today",
                "message": f"Task '{t.get('title')}' is due today. Complete it to maintain your streak!",
                "type": "warning",
                "timestamp": "Today"
            })
            
    # 2. Recent Successes
    completed_q = {
        "user_id": user_id, 
        "status": TaskStatus.COMPLETED.value
    }
    recent_done = await db.tasks.find(completed_q).sort([("_id", -1)]).to_list(length=3)
    for t in recent_done:
        notifications.append({
            "id": f"succ_{t['_id']}",
            "title": "Task Completed!",
            "message": f"Great job finishing '{t.get('title')}'. Keep up the momentum!",
            "type": "success",
            "timestamp": "Recently"
        })
        
    return {
        "notifications": notifications[:10],
        "unread_count": len([n for n in notifications if n["type"] in ("alert", "warning")])
    }


async def enroll_new_course(user_id: str, data: dict) -> dict:
    await _get_user(user_id)
    db = get_database()
    
    cat_lower = data.get("category", "").lower()
    if "data" in cat_lower or "math" in cat_lower or "python" in cat_lower:
        cat_theme = "purple"
        image_url = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80"
    elif "design" in cat_lower or "art" in cat_lower:
        cat_theme = "teal"
        image_url = "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800&q=80"
    elif "business" in cat_lower or "marketing" in cat_lower:
        cat_theme = "orange"
        image_url = "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80"
    else:
        cat_theme = "blue"
        image_url = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&q=80"

    doc = {
        "owner_id": user_id,
        "title": data.get("title", "New Course"),
        "category": data.get("category", "General"),
        "category_theme": cat_theme,
        "author": data.get("author", "Instructor"),
        "image_url": image_url,
        "module_count": 10,
        "certificate_eligible": True,
        "course_status": "in_progress",
        "hours_remaining_label": "20 Hrs",
        "progress_override": 0.0,
        "youtube_url": (str(data.get("youtube_url")).strip() or None) if data.get("youtube_url") is not None else None,
        "created_at": datetime.now(timezone.utc)
    }
    
    res = await db.courses.insert_one(doc)
    return {"ok": True, "course_id": str(res.inserted_id)}


async def course_detail(current_user: dict, course_id: str) -> dict:
    user_id = current_user["id"]
    role = str(current_user.get("role", "")).strip().lower()
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    from bson import ObjectId

    try:
        oid = ObjectId(course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course id")

    if role == "admin":
        course_query: dict = {"_id": oid, "owner_id": user_id}
    else:
        all_users = await db.users.find({}, {"_id": 1, "role": 1}).to_list(length=None)
        admin_users = [u for u in all_users if str(u.get("role", "")).strip().lower() == "admin"]
        admin_ids = [str(u["_id"]) for u in admin_users]
        course_query = {"_id": oid, "owner_id": {"$in": admin_ids}}

    c = await db.courses.find_one(course_query)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    cid = str(c["_id"])
    progress_doc = await db.course_progress.find_one({"course_id": cid, "user_id": user_id})
    pct = round(float((progress_doc or {}).get("progress_percent") or 0.0), 1)
    st_out = "completed" if (progress_doc or {}).get("status") == "completed" else "in_progress"

    return {
        "id": cid,
        "title": c.get("title") or "Course",
        "category": c.get("category") or "General",
        "author": c.get("author") or "Instructor",
        "image_url": c.get("image_url") or "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
        "module_count": int(c.get("module_count") or 8),
        "certificate_eligible": bool(c.get("certificate_eligible", True)),
        "progress_percent": pct,
        "status": st_out,
        "youtube_url": c.get("youtube_url"),
        "resume_seconds": int((progress_doc or {}).get("resume_seconds") or 0),
    }


async def record_watch_progress(
    current_user: dict,
    course_id: str,
    seconds_watched: int,
    current_seconds: int | None = None,
    duration_seconds: int | None = None,
) -> dict:
    user_id = current_user["id"]
    role = str(current_user.get("role", "")).strip().lower()
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    from bson import ObjectId

    try:
        oid = ObjectId(course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course id")

    if role == "admin":
        course_query: dict = {"_id": oid, "owner_id": user_id}
    else:
        all_users = await db.users.find({}, {"_id": 1, "role": 1}).to_list(length=None)
        admin_users = [u for u in all_users if str(u.get("role", "")).strip().lower() == "admin"]
        admin_ids = [str(u["_id"]) for u in admin_users]
        course_query = {"_id": oid, "owner_id": {"$in": admin_ids}}

    c = await db.courses.find_one(course_query)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    cid = str(c["_id"])
    total_tasks = await db.tasks.count_documents({"course_id": cid})

    progress_doc = await db.course_progress.find_one({"course_id": cid, "user_id": user_id})
    current = float((progress_doc or {}).get("progress_percent") or 0.0)
    watched_bank = int((progress_doc or {}).get("watched_seconds_accum") or 0)
    watched_bank = max(0, watched_bank + max(0, int(seconds_watched)))

    # Prefer duration-based progress when duration is known (video-relative progress).
    if duration_seconds is not None and int(duration_seconds) > 0 and current_seconds is not None:
        current_s = max(0, int(current_seconds))
        duration_s = max(1, int(duration_seconds))
        relative_pct = (current_s / float(duration_s)) * 100.0
        # YouTube player occasionally never emits the exact final second.
        # Treat "within last 2s" as completed to avoid getting stuck at ~96-99%.
        remaining_seconds = max(0, duration_s - current_s)
        if remaining_seconds <= 2:
            relative_pct = 100.0
        pct = round(min(100.0, max(current, relative_pct)), 1)
    else:
        progress_gain = watched_bank // 60  # fallback: +1% per 60 seconds watched
        watched_bank = watched_bank % 60
        pct = round(min(100.0, current + float(progress_gain)), 1)

    if pct >= 100.0:
        st = "completed"
    else:
        st = "in_progress"

    new_resume = int(current_seconds) if current_seconds is not None else int((progress_doc or {}).get("resume_seconds") or 0)

    await db.course_progress.update_one(
        {"course_id": cid, "user_id": user_id},
        {
            "$set": {
                "course_id": cid,
                "user_id": user_id,
                "progress_percent": pct,
                "status": st,
                "resume_seconds": max(0, new_resume),
                "watched_seconds_accum": watched_bank,
            }
        },
        upsert=True,
    )
    return {
        "progress_percent": pct,
        "status": st,
        "resume_seconds": max(0, new_resume),
    }
