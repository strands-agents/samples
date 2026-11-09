/**
 * config.ts
 *
 * Settings for the appointment assistant. Each value is resolved, highest priority first, from:
 *   1. command-line flags        (--region us-west-2)
 *   2. environment variables     (AWS_REGION=us-west-2)
 *   3. the config file           (assistant.config.json, written by --setup)
 *   4. built-in defaults
 *
 * Every resolved value remembers where it came from, so /config can show it.
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";

export interface Settings {
  region: string;
  model: string;
  db: string;
  timezone: string;
  /** Fixed "now" as YYYY-MM-DD HH:MM, handy for rehearsing a demo; empty means the real clock */
  now: string;
  /** Length of an appointment when none is given, in minutes */
  duration: number;
  /** Working hours for free-slot suggestions, as HH-HH (24-hour) */
  workday: string;
}

export type Source = "flag" | "env" | "config file" | "default";

export interface ResolvedSettings {
  values: Settings;
  sources: Record<keyof Settings, Source>;
  configPath: string;
}

export const DEFAULTS: Settings = {
  region: "us-east-1",
  model: "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  db: "appointments.db",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  now: "",
  duration: 60,
  workday: "09-18",
};

/** Environment variable for each setting */
export const ENV_VARS: Record<keyof Settings, string> = {
  region: "AWS_REGION",
  model: "MODEL_ID",
  db: "APPOINTMENTS_DB",
  timezone: "ASSISTANT_TIMEZONE",
  now: "ASSISTANT_NOW",
  duration: "ASSISTANT_DURATION",
  workday: "ASSISTANT_WORKDAY",
};

/** Suggested models for --setup; any Bedrock model ID or inference profile also works. */
export const MODEL_CHOICES = [
  { id: "us.anthropic.claude-haiku-4-5-20251001-v1:0", label: "Claude Haiku 4.5 (fast, low cost)" },
  { id: "global.anthropic.claude-sonnet-4-6", label: "Claude Sonnet 4.6 (more capable)" },
];

const KEYS = Object.keys(DEFAULTS) as (keyof Settings)[];

function coerce(key: keyof Settings, raw: unknown): Settings[keyof Settings] {
  return key === "duration" ? Number(raw) : String(raw ?? "").trim();
}

export function resolveSettings(flags: Partial<Record<keyof Settings, string>>, configPath: string): ResolvedSettings {
  let file: Partial<Settings> = {};
  if (existsSync(configPath)) {
    try {
      file = JSON.parse(readFileSync(configPath, "utf8"));
    } catch (error) {
      throw new Error(`Could not read ${configPath}: ${(error as Error).message}`);
    }
  }

  const values = { ...DEFAULTS } as Record<keyof Settings, unknown>;
  const sources = {} as Record<keyof Settings, Source>;
  for (const key of KEYS) {
    const fromEnv = process.env[ENV_VARS[key]];
    if (flags[key] !== undefined) {
      values[key] = coerce(key, flags[key]);
      sources[key] = "flag";
    } else if (fromEnv !== undefined && fromEnv !== "") {
      values[key] = coerce(key, fromEnv);
      sources[key] = "env";
    } else if (file[key] !== undefined) {
      values[key] = coerce(key, file[key]);
      sources[key] = "config file";
    } else {
      sources[key] = "default";
    }
  }
  return { values: values as unknown as Settings, sources, configPath };
}

export function parseWorkday(workday: string): { start: number; end: number } | undefined {
  const match = /^(\d{1,2})\s*-\s*(\d{1,2})$/.exec(workday.trim());
  if (!match) return undefined;
  const start = Number(match[1]);
  const end = Number(match[2]);
  return start >= 0 && end <= 24 && start < end ? { start, end } : undefined;
}

/** Returns a list of problems; empty means the settings are usable. */
export function validateSettings(s: Settings): string[] {
  const problems: string[] = [];
  if (!/^[a-z]{2}(-[a-z]+)+-\d$/.test(s.region)) problems.push(`region "${s.region}" does not look like an AWS region (e.g. us-east-1)`);
  if (!s.model) problems.push("model is empty");
  if (!s.db) problems.push("db is empty");
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: s.timezone });
  } catch {
    problems.push(`timezone "${s.timezone}" is not a known IANA time zone (e.g. Asia/Kolkata, America/New_York)`);
  }
  if (s.now && !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(s.now)) problems.push(`now "${s.now}" must be YYYY-MM-DD HH:MM, or empty for the real clock`);
  if (!Number.isInteger(s.duration) || s.duration < 5 || s.duration > 24 * 60) problems.push(`duration "${s.duration}" must be a whole number of minutes between 5 and 1440`);
  if (!parseWorkday(s.workday)) problems.push(`workday "${s.workday}" must be start-end hours, e.g. 09-18`);
  return problems;
}

export function saveSettings(path: string, s: Settings): void {
  writeFileSync(path, JSON.stringify(s, null, 2) + "\n");
}

/** Local date, time and weekday for "now", in the configured time zone (or the fixed now). */
export function currentMoment(s: Settings): { date: string; time: string; weekday: string } {
  if (s.now) {
    const [date, time] = s.now.split(" ");
    const [y, m, d] = date.split("-").map(Number);
    const weekday = new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-US", { weekday: "long", timeZone: "UTC" });
    return { date, time, weekday };
  }
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: s.timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      weekday: "long",
      hourCycle: "h23",
    })
      .formatToParts(new Date())
      .map((p) => [p.type, p.value])
  );
  return { date: `${parts.year}-${parts.month}-${parts.day}`, time: `${parts.hour}:${parts.minute}`, weekday: parts.weekday };
}
