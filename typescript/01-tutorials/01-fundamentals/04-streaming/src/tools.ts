import { tool } from "@strands-agents/sdk";
import z from "zod";

export const calculator = tool({
  name: "calculator",
  description: "Performs basic arithmetic",
  inputSchema: z.object({
    operation: z.enum(["add", "subtract", "multiply", "divide"]),
    a: z.number(),
    b: z.number(),
  }),
  callback: (input) => {
    switch (input.operation) {
      case "add":
        return input.a + input.b;
      case "subtract":
        return input.a - input.b;
      case "multiply":
        return input.a * input.b;
      case "divide":
        return input.a / input.b;
    }
  },
});

export const weatherForecast = tool({
  name: "WeatherForecast",
  description: "Predicts the weather",
  inputSchema: z.object({
    city: z.string(),
    days: z.number().default(3),
  }),
  callback: (input) =>
    `Weather forecast for ${input.city} for the next ${input.days} days is clear skies and 25 degress.`,
});
