"""
One-time migration: backfill `deadline_date` on tasks.

Run from repo root:
  python scripts/migrate_deadline_date.py

Safety:
- Does NOT overwrite existing `deadline_date`
- Skips tasks with missing/invalid `deadline`

Uses the same `.env` config as the app (MONGODB_URI, MONGODB_DB).
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.core.config import settings  # noqa: E402


def _deadline_to_datestr(dl: object) -> str | None:
    """Convert task.deadline (datetime/date/iso str) -> YYYY-MM-DD string."""
    if dl is None:
        return None
    if isinstance(dl, datetime):
        # If naive, assume UTC to be consistent with app writes.
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return dl.date().isoformat()
    if isinstance(dl, date) and not isinstance(dl, datetime):
        return dl.isoformat()
    if isinstance(dl, str):
        s = dl.strip()
        if len(s) >= 10:
            # Fast path for 'YYYY-MM-DD...' strings
            try:
                return date.fromisoformat(s[:10]).isoformat()
            except ValueError:
                pass
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.date().isoformat()
        except ValueError:
            return None
    return None


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    updated = 0
    skipped_has_deadline_date = 0
    skipped_invalid_deadline = 0

    # Only tasks missing deadline_date (or null) are scanned.
    cursor = db.tasks.find(
        {"$or": [{"deadline_date": {"$exists": False}}, {"deadline_date": None}]},
        {"deadline": 1, "deadline_date": 1},
        batch_size=500,
    )

    async for t in cursor:
        if t.get("deadline_date"):
            skipped_has_deadline_date += 1
            continue

        datestr = _deadline_to_datestr(t.get("deadline"))
        if not datestr:
            skipped_invalid_deadline += 1
            continue

        res = await db.tasks.update_one(
            {"_id": t["_id"], "$or": [{"deadline_date": {"$exists": False}}, {"deadline_date": None}]},
            {"$set": {"deadline_date": datestr}},
        )
        if res.modified_count:
            updated += 1

    print("Migration complete: backfilled tasks.deadline_date")
    print(f"  updated: {updated}")
    print(f"  skipped (already had deadline_date): {skipped_has_deadline_date}")
    print(f"  skipped (invalid/missing deadline): {skipped_invalid_deadline}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())

