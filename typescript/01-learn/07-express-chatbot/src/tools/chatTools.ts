/**
 * Three custom tools defined with Zod input schemas.
 *
 * Mirrors the shape of the benchmark chatbot repo (three tools) but built on
 * the Strands `tool()` factory:
 *   - get_current_time: current time for an IANA timezone
 *   - calculate:        safe arithmetic over two operands
 *   - get_weather:      current weather for a lat/long via the open-meteo API
 *
 * Each tool validates its input with Zod, so the model must supply
 * well-typed arguments before the callback runs. Callbacks return plain
 * JSON-serializable objects (the SDK's `JSONValue`).
 */

import { tool } from "@strands-agents/sdk";
import type { JSONValue } from "@strands-agents/sdk";
import { z } from "zod";

/** Returns the current time formatted for the requested IANA timezone. */
export const getCurrentTime = tool({
  name: "get_current_time",
  description:
    "Get the current time for an IANA timezone identifier (e.g. 'America/New_York', 'Europe/Paris', 'UTC').",
  inputSchema: z.object({
    timezone: z
      .string()
      .describe("IANA timezone identifier, e.g. 'America/New_York' or 'UTC'."),
  }),
  callback: (input): JSONValue => {
    try {
      const formatted = new Intl.DateTimeFormat("en-US", {
        timeZone: input.timezone,
        dateStyle: "full",
        timeStyle: "long",
      }).format(new Date());
      return { timezone: input.timezone, currentTime: formatted };
    } catch {
      return {
        error: `Invalid timezone: '${input.timezone}'. Use an IANA identifier like 'UTC' or 'America/New_York'.`,
      };
    }
  },
});

/** Performs a single safe arithmetic operation over two numbers. */
export const calculate = tool({
  name: "calculate",
  description:
    "Perform a single arithmetic operation (add, subtract, multiply, divide) over two numbers.",
  inputSchema: z.object({
    operation: z
      .enum(["add", "subtract", "multiply", "divide"])
      .describe("The arithmetic operation to perform."),
    a: z.number().describe("The first operand."),
    b: z.number().describe("The second operand."),
  }),
  callback: (input): JSONValue => {
    const { operation, a, b } = input;
    switch (operation) {
      case "add":
        return { result: a + b };
      case "subtract":
        return { result: a - b };
      case "multiply":
        return { result: a * b };
      case "divide":
        if (b === 0) return { error: "Cannot divide by zero." };
        return { result: a / b };
    }
  },
});

interface CurrentWeather {
  temperature: number;
  windspeed: number;
  winddirection: number;
  weathercode: number;
  time: string;
}

/** Fetches current weather for a coordinate using the open-meteo public API. */
export const getWeather = tool({
  name: "get_weather",
  description:
    "Get the current weather for a geographic coordinate (latitude/longitude) using the open-meteo API.",
  inputSchema: z.object({
    latitude: z
      .number()
      .min(-90)
      .max(90)
      .describe("Latitude in decimal degrees, between -90 and 90."),
    longitude: z
      .number()
      .min(-180)
      .max(180)
      .describe("Longitude in decimal degrees, between -180 and 180."),
  }),
  callback: async (input): Promise<JSONValue> => {
    const url =
      `https://api.open-meteo.com/v1/forecast` +
      `?latitude=${input.latitude}&longitude=${input.longitude}&current_weather=true`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        return { error: `Weather API returned status ${response.status}.` };
      }
      const data = (await response.json()) as {
        current_weather?: CurrentWeather;
      };
      if (!data.current_weather) {
        return { error: "No current weather data returned for that location." };
      }
      return { weather: { ...data.current_weather } };
    } catch (error) {
      return { error: `Failed to reach the weather service: ${String(error)}` };
    }
  },
});

/** All local (non-MCP) tools, ready to hand to the agent. */
export const localTools = [getCurrentTime, calculate, getWeather];
