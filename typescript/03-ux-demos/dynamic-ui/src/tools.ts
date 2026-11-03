/** Data tools over a small in-memory workout log. */
import { readFileSync } from "node:fs";
import { tool } from "@strands-agents/sdk";
import { z } from "zod";

const activity = z.enum(["run", "ride", "swim", "yoga", "strength"]);

interface Workout {
  date: string;
  activity: z.infer<typeof activity>;
  minutes: number;
  distance_km: number | null;
}

interface StoredWorkout {
  days_ago: number;
  activity: Workout["activity"];
  minutes: number;
  distance_km?: number;
}

const isoDate = (d: Date): string => d.toISOString().slice(0, 10);

const daysAgo = (days: number): Date => {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d;
};

// Dates are stored relative to today so the sample data always looks recent.
const stored: StoredWorkout[] = JSON.parse(
  readFileSync(new URL("../data/workouts.json", import.meta.url), "utf8"),
);
const workouts: Workout[] = stored.map((w) => ({
  date: isoDate(daysAgo(w.days_ago)),
  activity: w.activity,
  minutes: w.minutes,
  distance_km: w.distance_km ?? null,
}));

function recent(days: number, only?: Workout["activity"]): Workout[] {
  const since = isoDate(daysAgo(days - 1));
  return workouts
    .filter((w) => w.date >= since && (only === undefined || w.activity === only))
    .sort((a, b) => b.date.localeCompare(a.date));
}

function weekStart(date: string): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  return isoDate(d);
}

export const listWorkouts = tool({
  name: "list_workouts",
  description: "List logged workouts, newest first.",
  inputSchema: z.object({
    days: z.number().int().default(30).describe("How many days back to include, counting today."),
    activity: activity.optional().describe("Only include this activity."),
  }),
  callback: ({ days, activity }) => recent(days, activity),
});

export const summarizeWorkouts = tool({
  name: "summarize_workouts",
  description: "Totals for recent workouts: overall, per activity, and per week (oldest week first).",
  inputSchema: z.object({
    days: z.number().int().default(30).describe("How many days back to include, counting today."),
  }),
  callback: ({ days }) => {
    const list = recent(days);
    const byActivity: Record<string, { count: number; minutes: number; distance_km: number }> = {};
    const byWeek: Record<string, number> = {};
    for (const w of list) {
      const totals = (byActivity[w.activity] ??= { count: 0, minutes: 0, distance_km: 0 });
      totals.count += 1;
      totals.minutes += w.minutes;
      totals.distance_km = Math.round((totals.distance_km + (w.distance_km ?? 0)) * 10) / 10;
      const week = weekStart(w.date);
      byWeek[week] = (byWeek[week] ?? 0) + w.minutes;
    }
    return {
      count: list.length,
      minutes: list.reduce((sum, w) => sum + w.minutes, 0),
      distance_km: Math.round(list.reduce((sum, w) => sum + (w.distance_km ?? 0), 0) * 10) / 10,
      by_activity: byActivity,
      by_week: Object.keys(byWeek)
        .sort()
        .map((week) => ({ week_start: week, minutes: byWeek[week]! })),
    };
  },
});

export const logWorkout = tool({
  name: "log_workout",
  description: "Add a workout to the log.",
  inputSchema: z.object({
    activity: activity.describe("The kind of workout."),
    minutes: z.number().int().describe("How long it lasted."),
    distance_km: z.number().optional().describe("Distance covered, for runs, rides and swims."),
    day: z.string().optional().describe("ISO date (YYYY-MM-DD). Defaults to today."),
  }),
  callback: ({ activity, minutes, distance_km, day }) => {
    const workout: Workout = {
      date: day ?? isoDate(new Date()),
      activity,
      minutes,
      distance_km: distance_km ?? null,
    };
    workouts.push(workout);
    return { ...workout };
  },
});
