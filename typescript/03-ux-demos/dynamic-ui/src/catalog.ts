/**
 * The component catalog: every UI component the agent is allowed to render.
 *
 * This schema is the input of the `render_ui` tool, so the model sees exactly
 * these components and props, and Strands validates its output against them
 * before the tool runs. The browser has one renderer per `type`
 * (see web/app.js). To add a component, add a schema here and a renderer there.
 */
import { z } from "zod";

const text = z.object({
  type: z.literal("text"),
  content: z.string().describe("A short paragraph of plain text."),
});

const stat = z.object({
  type: z.literal("stat"),
  label: z.string(),
  value: z.string().describe("The headline number, formatted for display, e.g. '42 km'."),
  hint: z.string().optional().describe("Optional small print, e.g. 'up 12% on last week'."),
});

const table = z.object({
  type: z.literal("table"),
  title: z.string().optional(),
  columns: z.array(z.string()),
  rows: z.array(z.array(z.string())).describe("One list of cell values per row, in column order."),
});

const barChart = z.object({
  type: z.literal("bar_chart"),
  title: z.string().optional(),
  unit: z.string().optional().describe("Unit shown after each value, e.g. 'min'."),
  bars: z.array(z.object({ label: z.string(), value: z.number() })),
});

const form = z.object({
  type: z.literal("form"),
  title: z.string().optional(),
  action: z.string().describe("Name sent back to you with the values when the user submits."),
  submit: z.string().optional().describe("Submit button label."),
  fields: z.array(
    z.object({
      name: z.string().describe("Key for this field in the submitted values."),
      label: z.string(),
      kind: z.enum(["text", "number", "date", "select"]),
      options: z.array(z.string()).optional().describe("Choices, required when kind is 'select'."),
      value: z.string().optional().describe("Pre-filled value."),
    }),
  ),
});

const button = z.object({
  type: z.literal("button"),
  label: z.string(),
  action: z.string().describe("Name sent back to you when the user clicks."),
});

const leaf = z.discriminatedUnion("type", [text, stat, table, barChart, form, button]);

const row = z.object({
  type: z.literal("row"),
  items: z.array(leaf).describe("Components shown side by side, e.g. a few stats."),
});

export const component = z.discriminatedUnion("type", [text, stat, table, barChart, form, button, row]);

export type Component = z.infer<typeof component>;
