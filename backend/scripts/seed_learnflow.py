"""
Populate MongoDB with LearnFlow demo data for a test user.
Run from repo root:  python scripts/seed_learnflow.py

Requires .env with MONGODB_URI, MONGODB_DB, JWT_SECRET_KEY (or defaults in config).
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt  # noqa: E402

from app.core.config import settings  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402


def _hash_demo_password(plain: str) -> str:
    """Use bcrypt directly; passlib + bcrypt 5.x can error on Windows/Python 3.13."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

DEMO_EMAIL = "alex@learnflow.demo"
DEMO_PASSWORD = "learnflow123"
DEMO_NAME = "Alex Johnson"


# (total_tasks, completed_tasks) => progress % for dashboard/cards
COURSES = [
    {
        "title": "UI/UX Design Fundamentals",
        "description": "Foundations of product design.",
        "category": "Design",
        "category_theme": "blue",
        "cta_theme": "blue",
        "theme_color": "blue",
        "author": "Sarah Chen",
        "module_count": 12,
        "certificate_eligible": True,
        "course_status": "in_progress",
        "hours_remaining_label": "42 hrs left",
        "image_url": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800",
        "task_split": (50, 39),
    },
    {
        "title": "Advanced React Development",
        "description": "Hooks, patterns, performance.",
        "category": "Development",
        "category_theme": "purple",
        "cta_theme": "purple",
        "theme_color": "purple",
        "author": "Marcus Webb",
        "module_count": 14,
        "certificate_eligible": True,
        "course_status": "in_progress",
        "saved": True,
        "hours_remaining_label": "28 hrs left",
        "image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800",
        "task_split": (50, 27),
    },
    {
        "title": "Data Science with Python",
        "description": "EDA, modeling, visualization.",
        "category": "Data Science",
        "category_theme": "green",
        "cta_theme": "green",
        "theme_color": "green",
        "author": "Dr. Priya Nair",
        "module_count": 16,
        "certificate_eligible": True,
        "course_status": "in_progress",
        "hours_remaining_label": "12 hrs left",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "task_split": (25, 23),
    },
    {
        "title": "Machine Learning Basics",
        "description": "Intro to ML workflows.",
        "category": "Data Science",
        "category_theme": "orange",
        "cta_theme": "orange",
        "theme_color": "orange",
        "author": "Jordan Lee",
        "module_count": 10,
        "certificate_eligible": True,
        "course_status": "in_progress",
        "hours_remaining_label": "56 hrs left",
        "image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800",
        "task_split": (20, 7),
    },
    {
        "title": "Product Strategy Masterclass",
        "description": "Ship outcomes, not outputs.",
        "category": "Business",
        "category_theme": "teal",
        "cta_theme": "teal",
        "theme_color": "green",
        "author": "Casey Morgan",
        "module_count": 8,
        "certificate_eligible": True,
        "course_status": "completed",
        "hours_remaining_label": None,
        "progress_override": 100.0,
        "image_url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800",
        "task_split": (10, 10),
    },
]


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    existing = await db.users.find_one({"email": DEMO_EMAIL.lower()})
    if existing:
        oid = str(existing["_id"])
        course_docs = await db.courses.find({"owner_id": oid}).to_list(length=None)
        cids = [str(c["_id"]) for c in course_docs]
        await db.tasks.delete_many({"user_id": oid})
        if cids:
            await db.tasks.delete_many({"course_id": {"$in": cids}})
        await db.courses.delete_many({"owner_id": oid})
        await db.planner_blocks.delete_many({"user_id": oid})
        await db.users.delete_one({"_id": existing["_id"]})

    now = datetime.now(timezone.utc)
    user_doc = {
        "email": DEMO_EMAIL.lower(),
        "full_name": DEMO_NAME,
        "password_hash": _hash_demo_password(DEMO_PASSWORD),
        "role": "user",
        "created_at": now,
        "tier_label": "Pro Learner",
        "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200",
        "learnflow": {
            "study_streak_days": 14,
            "weekly_study_hours_total": 42.5,
            "weekly_hours_by_day": [3.2, 4.1, 2.0, 8.0, 11.2, 3.5, 10.5],
            "tasks_completed_total": 28,
            "tasks_total": 35,
            "planner_deadline_days": [19],
            "ai_recommendation": "AI Study Recommendation — Based on your deadlines, study 2h React today + 1.5h Data Science tonight for optimal retention.",
            "planner_timeline_summary": "4 tasks - 5.5 hrs",
            "today_plan": [
                {
                    "id": "tp1",
                    "kind": "watch",
                    "title": "Watch: React Hooks Deep Dive",
                    "subtitle": None,
                    "status": "in_progress",
                    "accent": "blue",
                },
                {
                    "id": "tp2",
                    "kind": "quiz",
                    "title": "Quiz: UX Design Principles",
                    "subtitle": None,
                    "status": "completed",
                    "accent": "green",
                },
                {
                    "id": "tp3",
                    "kind": "assignment",
                    "title": "Assignment: EDA Notebook",
                    "subtitle": "Due 11:59 PM",
                    "status": "due_tonight",
                    "accent": "orange",
                },
            ],
            "deadlines": [
                {
                    "id": "d1",
                    "title": "Final Project: UX Case Study",
                    "urgency_label": "Today",
                    "urgency": "today",
                },
                {
                    "id": "d2",
                    "title": "Assignment: EDA Notebook",
                    "urgency_label": "2 days",
                    "urgency": "soon",
                },
                {
                    "id": "d3",
                    "title": "Midterm: React Patterns",
                    "urgency_label": "5 days",
                    "urgency": "later",
                },
            ],
            "analytics": {
                "analytics_month": {
                    "kpis": [
                        {"label": "Overall Score", "value": "87.4", "badge": "+5.2%", "badge_tone": "success"},
                        {"label": "Hours Studied", "value": "168.5", "badge": "+12 hrs", "badge_tone": "success"},
                        {"label": "Assignments Done", "value": "24 / 26", "badge": "2 pending", "badge_tone": "warning"},
                        {"label": "Avg Daily Study", "value": "5.6 hrs", "badge": "Goal: 6h", "badge_tone": "info"},
                    ],
                    "monthly_hours": [
                        {"month": "Jan", "hours": 22, "highlight": False},
                        {"month": "Feb", "hours": 28, "highlight": False},
                        {"month": "Mar", "hours": 31, "highlight": False},
                        {"month": "Apr", "hours": 26, "highlight": False},
                        {"month": "May", "hours": 35, "highlight": False},
                        {"month": "Jun", "hours": 40, "highlight": True},
                    ],
                    "subjects": [
                        {"name": "UI/UX Design", "percent": 40, "theme": "blue"},
                        {"name": "React Dev", "percent": 54, "theme": "purple"},
                        {"name": "Data Science", "percent": 92, "theme": "green"},
                        {"name": "Machine Learning", "percent": 35, "theme": "orange"},
                    ],
                    "performance": [
                        {
                            "course": "UI/UX Design Fundamentals",
                            "last_score": "94/100",
                            "score_tone": "success",
                            "progress_percent": 78,
                            "progress_theme": "blue",
                            "status": "On Track",
                            "status_tone": "success",
                            "trend": "+3.2%",
                        },
                        {
                            "course": "Advanced React Development",
                            "last_score": "76/100",
                            "score_tone": "warning",
                            "progress_percent": 54,
                            "progress_theme": "purple",
                            "status": "Needs Focus",
                            "status_tone": "warning",
                            "trend": "+1.8%",
                        },
                        {
                            "course": "Data Science with Python",
                            "last_score": "98/100",
                            "score_tone": "success",
                            "progress_percent": 92,
                            "progress_theme": "green",
                            "status": "Excellent",
                            "status_tone": "success",
                            "trend": "+6.4%",
                        },
                    ],
                }
            },
        },
    }
    ins_user = await db.users.insert_one(user_doc)
    uid = str(ins_user.inserted_id)

    today = date.today()
    course_ids: list[str] = []

    for spec in COURSES:
        total_tasks, done = spec["task_split"]
        doc = {
            "owner_id": uid,
            "title": spec["title"],
            "description": spec["description"],
            "created_at": now,
            "category": spec["category"],
            "category_theme": spec["category_theme"],
            "cta_theme": spec["cta_theme"],
            "theme_color": spec["theme_color"],
            "author": spec["author"],
            "module_count": spec["module_count"],
            "certificate_eligible": spec["certificate_eligible"],
            "course_status": spec["course_status"],
            "saved": bool(spec.get("saved", False)),
            "hours_remaining_label": spec.get("hours_remaining_label"),
            "progress_override": spec.get("progress_override"),
            "image_url": spec["image_url"],
        }
        res = await db.courses.insert_one(doc)
        cid = str(res.inserted_id)
        course_ids.append(cid)

        for i in range(total_tasks):
            await db.tasks.insert_one(
                {
                    "course_id": cid,
                    "user_id": uid,
                    "title": f"Module {i + 1}",
                    "description": "",
                    "deadline": datetime.combine(
                        today + timedelta(days=7 + i), datetime.min.time(), tzinfo=timezone.utc
                    ),
                    "status": "completed" if i < done else "pending",
                    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "created_at": now,
                }
            )

    blocks = [
        {
            "time": "08:00",
            "title": "Morning Review — UX Design Principles",
            "subtitle": "UI/UX Design Fundamentals · 60 min",
            "duration_label": "60 min",
            "status": "done",
        },
        {
            "time": "10:00",
            "title": "React Hooks Deep Dive — Lecture 7",
            "subtitle": "Advanced React Dev · 90 min",
            "duration_label": "90 min",
            "status": "now",
        },
        {
            "time": "14:00",
            "title": "EDA Assignment — Exploratory Analysis",
            "subtitle": "Data Science with Python · 2 hrs",
            "duration_label": "2 hrs",
            "status": "pending",
        },
        {
            "time": "17:00",
            "title": "ML Study Group — Chapter 3",
            "subtitle": "Machine Learning Basics · 75 min",
            "duration_label": "75 min",
            "status": "scheduled",
        },
    ]
    await db.planner_blocks.insert_one({"user_id": uid, "day": today.isoformat(), "blocks": blocks})

    print("Seed complete.")
    print(f"  User: {DEMO_EMAIL}  /  {DEMO_PASSWORD}")
    print(f"  user_id: {uid}")
    print(f"  courses: {len(course_ids)}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
