/**
 * Custom Tools Tutorial - Appointment Management System
 *
 * Entry point for the Appointment Management Agent.
 * Orchestrates a Strands agent (via Amazon Bedrock) that manages appointments
 * through natural language, turn by turn.
 *
 * This example demonstrates how to create custom tools with:
 * - Class-based architecture
 * - SQLite database integration
 * - Zod schema validation
 * - Type-safe tool definitions
 * - Multi-tool agent workflows, including asking the user when a slot is busy
 *
 * Flow: User Input → Agent → Tool Selection → Database → Response
 *
 * Modes:
 *   npm run dev                 guided demo: two scripted requests, a calendar clash, then you take over
 *   npm run dev -- --chat       chat only, from the first turn
 *   npm run dev -- --auto       the three scripted requests with no input (for quick checks)
 *   npm run dev -- --setup      choose and save your settings interactively
 *
 * Every setting (model, region, calendar file, time zone, "now", default length,
 * working hours) can come from a flag, an environment variable or the config file.
 * Run with --help for the full list.
 */

import * as readline from "node:readline";
import { parseArgs } from "node:util";
import { Agent, BedrockModel } from "@strands-agents/sdk";
import { AppointmentDatabase } from "./database/AppointmentDatabase.js";
import { AppointmentTools } from "./tools/AppointmentTools.js";
import {
  DEFAULTS,
  ENV_VARS,
  MODEL_CHOICES,
  type ResolvedSettings,
  type Settings,
  currentMoment,
  parseWorkday,
  resolveSettings,
  saveSettings,
  validateSettings,
} from "./config.js";

const { values: args } = parseArgs({
  options: {
    region: { type: "string" },
    model: { type: "string" },
    db: { type: "string" },
    timezone: { type: "string" },
    now: { type: "string" },
    duration: { type: "string" },
    workday: { type: "string" },
    config: { type: "string", default: "assistant.config.json" },
    setup: { type: "boolean", default: false },
    chat: { type: "boolean", default: false },
    auto: { type: "boolean", default: false },
    help: { type: "boolean", short: "h", default: false },
  },
});

const SETTING_HELP: Record<keyof Settings, string> = {
  region: "AWS region for Amazon Bedrock",
  model: "Bedrock model ID or inference profile",
  db: "SQLite file that holds the calendar",
  timezone: "IANA time zone used for \"today\" and \"tomorrow\"",
  now: "fixed date and time YYYY-MM-DD HH:MM, for rehearsing a demo (empty = real clock)",
  duration: "default appointment length in minutes",
  workday: "working hours for free-slot suggestions, start-end (24h)",
};

if (args.help) {
  const rows = (Object.keys(DEFAULTS) as (keyof Settings)[])
    .map((k) => `  --${k.padEnd(9)} ${ENV_VARS[k].padEnd(19)} ${SETTING_HELP[k]} (default: ${String(DEFAULTS[k]) || "real clock"})`)
    .join("\n");
  console.log(`Usage: npm run dev -- [--setup | --chat | --auto] [options]

  (no mode)   guided demo: two scripted requests, a calendar clash, then you take over
  --setup     choose your settings interactively and save them to the config file
  --chat      chat with the agent from the first turn
  --auto      run the three scripted requests without asking for input

Options (flag, environment variable, meaning):
${rows}
  --config    path to the config file (default: assistant.config.json)

Priority: flag, then environment variable, then config file, then default.
In the chat: /config shows the settings, /set <name> <value> changes one, /save stores them,
/calendar shows the saved appointments, /help lists commands, exit quits.`);
  process.exit(0);
}

const flags = Object.fromEntries(
  (Object.keys(DEFAULTS) as (keyof Settings)[]).filter((k) => args[k] !== undefined).map((k) => [k, args[k]])
);

// One reader for the whole session, so setup answers and chat turns come from the same input.
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const lines = rl[Symbol.asyncIterator]();
async function readLine(prompt: string): Promise<string | undefined> {
  process.stdout.write(prompt);
  const next = await lines.next();
  return next.done ? undefined : next.value.trim();
}

function nowContext(s: Settings): string {
  const { date, time, weekday } = currentMoment(s);
  return `Today is ${weekday}, ${date}, and the local time is ${time} (${s.timezone}${s.now ? ", fixed for this demo" : ""}).`;
}

function systemPromptFor(s: Settings): string {
  const { start, end } = parseWorkday(s.workday)!;
  return `You are a helpful personal assistant that specializes in managing my appointments and calendar. You have access to appointment management tools to help me organize my schedule effectively. Always provide the appointment id so that I can update it if required.

${nowContext(s)} Appointments last ${s.duration} minutes unless I say otherwise; use that default without asking. My working hours are ${String(start).padStart(2, "0")}:00 to ${String(end).padStart(2, "0")}:00. A title, a time and a location are enough to book; the description is optional.

Always use the tools to check the calendar; never decide from memory that a time is free or busy. When a tool returns status "conflict", the calendar is busy and nothing was saved: tell me which appointment clashes, offer the suggested_start_times from that result, and ask me how to proceed. Only ever propose times that a tool returned as free; never work out other times yourself. Never double-book, and never pick an alternative time on my behalf. If details you need are missing, ask for them instead of inventing them. Confirm with me before cancelling an appointment.`;
}

// The scripted requests. The third deliberately clashes with the first, so the
// agent has to stop and ask you what to do.
const SCRIPTED = [
  "Book 'Agent fun' for tomorrow 3pm in NYC. This meeting will discuss all the fun things that an agent can do",
  "Oh no! My bad, 'Agent fun' is actually happening in DC",
  "Also book 'Design review' tomorrow at 3pm in the office, to walk through the new calendar screens",
];

/** The scripted requests as a copy-paste list; the third clashes with the first. */
function samplePrompts(): string {
  return (
    "Try these, one at a time (copy and paste):\n\n" +
    SCRIPTED.map((prompt, i) => `  ${i + 1}. ${prompt}`).join("\n") +
    "\n\nThe third clashes with the first, so the assistant will ask you to pick another time."
  );
}

/** Everything built from the settings. Rebuilt by /set, keeping the conversation. */
interface Session {
  settings: Settings;
  sources: ResolvedSettings["sources"];
  database: AppointmentDatabase;
  agent: Agent;
}

function buildSession(settings: Settings, sources: ResolvedSettings["sources"], previous?: Session): Session {
  const { start, end } = parseWorkday(settings.workday)!;
  const database =
    previous && previous.settings.db === settings.db ? previous.database : new AppointmentDatabase(settings.db);
  if (previous && previous.database !== database) previous.database.close();

  const tools = new AppointmentTools(database, {
    defaultDurationMinutes: settings.duration,
    workdayStartHour: start,
    workdayEndHour: end,
  }).getAllTools();

  // The agent streams its replies, and the tools it calls, to the console as they happen.
  const agent = new Agent({
    model: new BedrockModel({ modelId: settings.model, region: settings.region }),
    systemPrompt: systemPromptFor(settings),
    tools,
    ...(previous && { messages: previous.agent.messages }),
  });
  return { settings, sources, database, agent };
}

function header(session: Session): string {
  const s = session.settings;
  return `Appointment assistant · model ${s.model} · region ${s.region} · calendar ${s.db}\n${nowContext(s)}`;
}

function printSettings(session: Session, configPath: string): void {
  console.table(
    (Object.keys(DEFAULTS) as (keyof Settings)[]).map((k) => ({
      setting: k,
      value: String(session.settings[k]) || "(real clock)",
      from: session.sources[k],
    }))
  );
  console.log(`Config file: ${configPath}. Change a value with /set <setting> <value>, then /save to keep it.`);
}

function printCalendar(database: AppointmentDatabase): void {
  const rows = database.listAppointments().map(({ id, date, duration_minutes, title, location }) => ({
    id: id.slice(0, 8),
    date,
    minutes: duration_minutes,
    title,
    location,
  }));
  if (rows.length === 0) console.log("(calendar is empty)");
  else console.table(rows);
}

async function runSetup(resolved: ResolvedSettings): Promise<Settings | undefined> {
  const s = { ...resolved.values };
  console.log(`Setting up the appointment assistant. Press Enter to keep the value in [brackets].\n`);

  const ask = async <K extends keyof Settings>(key: K, question: string, parse: (raw: string) => Settings[K] = (r) => r as Settings[K]) => {
    for (;;) {
      const current = String(s[key]) || "real clock";
      const answer = await readLine(`${question} [${current}]: `);
      if (answer === undefined) return false;
      if (answer === "") return true;
      const candidate = { ...s, [key]: parse(answer) };
      const problem = validateSettings(candidate).find((p) => p.startsWith(key === "now" ? "now" : key));
      if (!problem) {
        s[key] = candidate[key];
        return true;
      }
      console.log(`  ${problem}`);
    }
  };

  console.log("Models:");
  MODEL_CHOICES.forEach((m, i) => console.log(`  ${i + 1}. ${m.label} — ${m.id}`));
  const steps: [keyof Settings, string, ((raw: string) => never | Settings[keyof Settings])?][] = [
    ["model", "Model (number from the list, or any Bedrock model ID)", (r) => MODEL_CHOICES[Number(r) - 1]?.id ?? r],
    ["region", "AWS region"],
    ["db", "Calendar file"],
    ["timezone", "Time zone"],
    ["now", "Fixed date and time for a demo, YYYY-MM-DD HH:MM (type 'clock' for the real clock)", (r) => (r === "clock" ? "" : r)],
    ["duration", "Default appointment length in minutes", (r) => Number(r)],
    ["workday", "Working hours, start-end"],
  ];
  for (const [key, question, parse] of steps) {
    if (!(await ask(key, question, parse as never))) return undefined;
  }

  saveSettings(resolved.configPath, s);
  console.log(`\nSaved to ${resolved.configPath}.`);
  return s;
}

async function chat(session: Session, configPath: string): Promise<Session> {
  for (;;) {
    const input = await readLine("\n> ");
    if (input === undefined || ["exit", "quit"].includes(input.toLowerCase())) return session;

    if (input === "/calendar") {
      printCalendar(session.database);
    } else if (input === "/config") {
      printSettings(session, configPath);
    } else if (input === "/save") {
      saveSettings(configPath, session.settings);
      console.log(`Saved to ${configPath}.`);
    } else if (input.startsWith("/set")) {
      const [, key, ...rest] = input.split(/\s+/);
      const raw = rest.join(" ");
      if (!key || !(key in DEFAULTS)) {
        console.log(`Usage: /set <setting> <value>. Settings: ${Object.keys(DEFAULTS).join(", ")}. Use /set now clock for the real clock.`);
        continue;
      }
      const k = key as keyof Settings;
      const value = k === "duration" ? Number(raw) : k === "now" && raw === "clock" ? "" : raw;
      const candidate = { ...session.settings, [k]: value } as Settings;
      const problems = validateSettings(candidate);
      if (problems.length) {
        console.log(problems.join("\n"));
        continue;
      }
      session = buildSession(candidate, { ...session.sources, [k]: "flag" }, session);
      console.log(`${k} set to ${String(value) || "real clock"}. The conversation continues with the new setting.\n${header(session)}`);
    } else if (input === "/help") {
      console.log(
        `${samplePrompts()}\n\nOr ask anything in plain English, e.g. "What's on tomorrow?", "Move Design review to 4pm", "Cancel Agent fun".\n\n` +
          "/calendar               show saved appointments\n" +
          "/config                 show settings and where each came from\n" +
          "/set <setting> <value>  change a setting, e.g. /set model global.anthropic.claude-sonnet-4-6\n" +
          "/save                   save the current settings to the config file\n" +
          "exit                    quit"
      );
    } else if (input) {
      await ask(session, input);
    }
  }
}

async function ask(session: Session, message: string): Promise<void> {
  console.log(`\nYou: ${message}\n`);
  process.stdout.write("Agent: ");
  await session.agent.invoke(message);
  console.log("\n" + "=".repeat(70));
}

async function main() {
  let resolved = resolveSettings(flags, args.config!);

  if (args.setup) {
    const saved = await runSetup(resolved);
    if (!saved) {
      console.log("\nSetup cancelled; nothing saved.");
      return;
    }
    resolved = resolveSettings(flags, args.config!);
  }

  const problems = validateSettings(resolved.values);
  if (problems.length) {
    console.error(`Invalid settings:\n  ${problems.join("\n  ")}\nRun with --help, or --setup to choose settings interactively.`);
    process.exitCode = 1;
    return;
  }

  let session = buildSession(resolved.values, resolved.sources);
  console.log(header(session));

  // ===============================
  // Scripted requests
  // ===============================
  if (!args.chat && !args.setup) {
    for (const [i, message] of SCRIPTED.entries()) {
      console.log(`\nExample ${i + 1} of ${SCRIPTED.length}`);
      await ask(session, message);
    }
  }

  // ===============================
  // Turn-by-turn chat
  // ===============================
  if (!args.auto) {
    console.log(
      args.chat || args.setup
        ? `\nChat with the assistant. Type /help for commands, or exit.\n\n${samplePrompts()}`
        : "\nYour turn: answer the assistant, for example by picking one of the free slots. Type /help for commands, or exit."
    );
    session = await chat(session, resolved.configPath);
  }

  console.log("\nFinal calendar:");
  printCalendar(session.database);

  // Cleanup
  session.database.close();
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => rl.close());
