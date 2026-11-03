"""Data tools over a small in-memory workout log."""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from strands import tool

Activity = Literal["run", "ride", "swim", "yoga", "strength"]

# Dates are stored relative to today so the sample data always looks recent.
_today = date.today()
WORKOUTS: list[dict] = [
    {
        "date": (_today - timedelta(days=w["days_ago"])).isoformat(),
        "activity": w["activity"],
        "minutes": w["minutes"],
        "distance_km": w.get("distance_km"),
    }
    for w in json.loads((Path(__file__).parent / "data" / "workouts.json").read_text())
]


@tool
def list_workouts(days: int = 30, activity: Activity | None = None) -> list[dict]:
    """List logged workouts, newest first.

    Args:
        days: How many days back to include, counting today.
        activity: Only include this activity.
    """
    return _recent(days, activity)


@tool
def summarize_workouts(days: int = 30) -> dict:
    """Totals for recent workouts: overall, per activity, and per week (oldest week first).

    Args:
        days: How many days back to include, counting today.
    """
    workouts = _recent(days)
    by_activity: dict[str, dict] = {}
    by_week: dict[str, int] = {}
    for w in workouts:
        totals = by_activity.setdefault(w["activity"], {"count": 0, "minutes": 0, "distance_km": 0.0})
        totals["count"] += 1
        totals["minutes"] += w["minutes"]
        totals["distance_km"] = round(totals["distance_km"] + (w["distance_km"] or 0), 1)
        week = date.fromisoformat(w["date"])
        week_start = (week - timedelta(days=week.weekday())).isoformat()
        by_week[week_start] = by_week.get(week_start, 0) + w["minutes"]
    return {
        "count": len(workouts),
        "minutes": sum(w["minutes"] for w in workouts),
        "distance_km": round(sum(w["distance_km"] or 0 for w in workouts), 1),
        "by_activity": by_activity,
        "by_week": [{"week_start": k, "minutes": v} for k, v in sorted(by_week.items())],
    }


@tool
def log_workout(activity: Activity, minutes: int, distance_km: float | None = None, day: str | None = None) -> dict:
    """Add a workout to the log.

    Args:
        activity: The kind of workout.
        minutes: How long it lasted.
        distance_km: Distance covered, for runs, rides and swims.
        day: ISO date (YYYY-MM-DD). Defaults to today.
    """
    workout = {
        "date": day or date.today().isoformat(),
        "activity": activity,
        "minutes": minutes,
        "distance_km": distance_km,
    }
    WORKOUTS.append(workout)
    return workout


def _recent(days: int, activity: str | None = None) -> list[dict]:
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    matches = [w for w in WORKOUTS if w["date"] >= since and activity in (None, w["activity"])]
    return sorted(matches, key=lambda w: w["date"], reverse=True)
