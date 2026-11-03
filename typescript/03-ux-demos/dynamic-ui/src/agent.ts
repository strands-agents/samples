/** A chat whose agent can render UI components in the browser. */
import { Agent, tool } from "@strands-agents/sdk";
import { z } from "zod";
import { component, type Component } from "./catalog.js";
import { listWorkouts, logWorkout, summarizeWorkouts } from "./tools.js";

const systemPrompt = (today: string): string => `You are a friendly assistant inside a workout log app. Today is ${today}.

The app can show UI components that you choose. Prefer showing over telling: call
render_ui with the components that fit the question, for example stats for totals,
a bar_chart for trends over time, a table for a list of workouts, a form to collect
input, and buttons for useful next steps. Group related stats in a row.

Take every total, count and per-week figure from summarize_workouts. Never add up
numbers yourself.

Call render_ui first, then finish with a text reply of one or two short sentences
that appears above the components, in plain text without markdown. Don't repeat
data that is already shown in a component.

Messages that start with [ui action] come from the user clicking a button or
submitting a form you rendered, followed by the action name and the values as
JSON. Act on them (for example, log the workout), then render the updated view.`;

export interface Reply {
  text: string;
  ui: Component[];
}

/** One conversation: an agent plus the UI it rendered on the latest turn. */
export class Chat {
  private ui: Component[] = [];

  private readonly agent = new Agent({
    systemPrompt: systemPrompt(new Date().toISOString().slice(0, 10)),
    tools: [
      listWorkouts,
      summarizeWorkouts,
      logWorkout,
      tool({
        name: "render_ui",
        description: "Show UI components to the user, in order, below your reply.",
        inputSchema: z.object({ components: z.array(component).describe("The components to show.") }),
        callback: ({ components }) => {
          this.ui.push(...components);
          return "Shown to the user. Now write your short reply.";
        },
      }),
    ],
    printer: false,
  });

  async send(message: string): Promise<Reply> {
    this.ui = [];
    const result = await this.agent.invoke(message);
    return { text: result.toString().trim(), ui: this.ui };
  }
}
