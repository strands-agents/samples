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
 *
 * Options (flags win over environment variables):
 *   --region <region>   or AWS_REGION        (default us-east-1)
 *   --model <model-id>  or MODEL_ID          (default Claude Haiku 4.5 inference profile)
 *   --db <path>         or APPOINTMENTS_DB   (default appointments.db)
 */

import * as readline from "node:readline";
import { parseArgs } from "node:util";
import { Agent, BedrockModel } from "@strands-agents/sdk";
import { AppointmentDatabase, DEFAULT_DURATION_MINUTES } from "./database/AppointmentDatabase.js";
import { AppointmentTools } from "./tools/AppointmentTools.js";

const DEFAULT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0";

const { values: args } = parseArgs({
  options: {
    region: { type: "string" },
    model: { type: "string" },
    db: { type: "string" },
    chat: { type: "boolean", default: false },
    auto: { type: "boolean", default: false },
    help: { type: "boolean", short: "h", default: false },
  },
});

if (args.help) {
  console.log(`Usage: npm run dev -- [--chat | --auto] [--region <region>] [--model <model-id>] [--db <path>]

  (no flag)   guided demo: two scripted requests, a calendar clash, then you take over
  --chat      chat with the agent from the first turn
  --auto      run the three scripted requests without asking for input

In chat, type /calendar to see the saved appointments, /help for commands, exit to quit.`);
  process.exit(0);
}

const config = {
  region: args.region ?? process.env.AWS_REGION ?? "us-east-1",
  modelId: args.model ?? process.env.MODEL_ID ?? DEFAULT_MODEL_ID,
  dbPath: args.db ?? process.env.APPOINTMENTS_DB ?? "appointments.db",
};

// The agent needs "now" in local time to resolve phrases like "tomorrow at 3pm".
function nowContext(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  const time = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
  const weekday = now.toLocaleDateString("en-US", { weekday: "long" });
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return `Today is ${weekday}, ${date}, and the local time is ${time} (${zone}).`;
}

// Agent Setup
// This is the system prompt for the agent
const systemPrompt = `You are a helpful personal assistant that specializes in managing my appointments and calendar. You have access to appointment management tools to help me organize my schedule effectively. Always provide the appointment id so that I can update it if required.

${nowContext()} Appointments last ${DEFAULT_DURATION_MINUTES} minutes unless I say otherwise; use that default without asking. A title, a time and a location are enough to book; the description is optional.

When a tool returns status "conflict", the calendar is busy and nothing was saved. Tell me which appointment clashes, suggest two or three start times copied from the free slots in the tool result, and ask me how to proceed. Only ever suggest start times that appear in a free slots list; do not work out other times yourself. Never double-book, and never pick an alternative time on my behalf. If details you need are missing, ask for them instead of inventing them. Confirm with me before cancelling an appointment.`;

// The scripted requests. The third deliberately clashes with the first, so the
// agent has to stop and ask you what to do.
const SCRIPTED = [
  "Book 'Agent fun' for tomorrow 3pm in NYC. This meeting will discuss all the fun things that an agent can do",
  "Oh no! My bad, 'Agent fun' is actually happening in DC",
  "Also book 'Design review' tomorrow at 3pm in the office, to walk through the new calendar screens",
];

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

async function chat(ask: (message: string) => Promise<void>, database: AppointmentDatabase) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  // Reading lines with for-await ends cleanly when input closes (Ctrl+D or piped input).
  process.stdout.write("\n> ");
  for await (const line of rl) {
    const input = line.trim();
    if (["exit", "quit"].includes(input.toLowerCase())) break;
    if (input === "/calendar") {
      printCalendar(database);
    } else if (input === "/help") {
      console.log(
        'Ask in plain English, e.g. "What\'s on tomorrow?", "Move Design review to 4pm", "Cancel Agent fun".\n' +
          "/calendar  show saved appointments\n" +
          "exit       quit"
      );
    } else if (input) {
      await ask(input);
    }
    process.stdout.write("\n> ");
  }
  rl.close();
}

async function main() {
  // Initialize database
  const database = new AppointmentDatabase(config.dbPath);

  // Initialize tools with database dependency
  const appointmentTools = new AppointmentTools(database);

  // Get all tools
  const tools = appointmentTools.getAllTools();

  // Create agent with appointment management tools. The agent streams its replies,
  // and the tools it calls, to the console as they happen.
  const agent = new Agent({
    model: new BedrockModel({ modelId: config.modelId, region: config.region }),
    systemPrompt,
    tools,
  });

  console.log(`Appointment assistant · model ${config.modelId} · region ${config.region} · calendar ${config.dbPath}`);
  console.log(nowContext());

  const ask = async (message: string) => {
    console.log(`\nYou: ${message}\n`);
    process.stdout.write("Agent: ");
    await agent.invoke(message);
    console.log("\n" + "=".repeat(70));
  };

  // ===============================
  // Scripted requests
  // ===============================
  if (!args.chat) {
    for (const [i, message] of SCRIPTED.entries()) {
      console.log(`\nExample ${i + 1} of ${SCRIPTED.length}`);
      await ask(message);
    }
  }

  // ===============================
  // Turn-by-turn chat
  // ===============================
  if (!args.auto) {
    console.log(
      args.chat
        ? "\nChat with the assistant. Type /calendar, /help, or exit."
        : "\nYour turn: answer the assistant, for example by picking one of the free slots. Type /calendar, /help, or exit."
    );
    await chat(ask, database);
  }

  console.log("\nFinal calendar:");
  printCalendar(database);

  // Cleanup
  database.close();
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
