/**
 * Strands tools.
 *
 * Tools run inside the Strands agent loop (server-side, in the route handler).
 * Define them with a Zod schema for runtime validation + full type inference.
 * Replace these samples with your own; the client never needs to change.
 */
import { tool } from "@strands-agents/sdk";
import { z } from "zod";

/** A simple, safe calculator over the four basic operations. */
export const calculator = tool({
  name: "calculator",
  description:
    "Perform a basic arithmetic operation (add, subtract, multiply, divide) on two numbers.",
  inputSchema: z.object({
    operation: z
      .enum(["add", "subtract", "multiply", "divide"])
      .describe("The arithmetic operation to perform."),
    a: z.number().describe("The first operand."),
    b: z.number().describe("The second operand."),
  }),
  callback: ({ operation, a, b }) => {
    switch (operation) {
      case "add":
        return String(a + b);
      case "subtract":
        return String(a - b);
      case "multiply":
        return String(a * b);
      case "divide":
        if (b === 0) return "Error: division by zero.";
        return String(a / b);
    }
  },
});

/** Returns the current server time in ISO-8601, optionally for a given IANA time zone. */
export const currentTime = tool({
  name: "current_time",
  description:
    "Get the current date and time as an ISO-8601 string, optionally in a specific IANA time zone (e.g. 'America/Mexico_City').",
  inputSchema: z.object({
    timeZone: z
      .string()
      .optional()
      .describe("Optional IANA time zone name. Defaults to UTC."),
  }),
  callback: ({ timeZone }) => {
    const now = new Date();
    if (!timeZone) return now.toISOString();
    try {
      return new Intl.DateTimeFormat("en-US", {
        timeZone,
        dateStyle: "full",
        timeStyle: "long",
      }).format(now);
    } catch {
      return `Unknown time zone "${timeZone}". Current UTC time: ${now.toISOString()}`;
    }
  },
});

/** All tools exposed to the agent. */
export const tools = [calculator, currentTime];
