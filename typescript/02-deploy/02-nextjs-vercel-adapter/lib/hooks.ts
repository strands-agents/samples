/**
 * Strands hooks, packaged as a Plugin.
 *
 * Plugins register lifecycle hooks on the agent. This one logs every tool call
 * (before/after) — a minimal observability example. Swap `console` for your
 * logger, metrics, or tracing. Strands exposes 15+ lifecycle events; see
 * https://strandsagents.com for the full list.
 */
import {
  BeforeToolCallEvent,
  AfterToolCallEvent,
  type Plugin,
  type LocalAgent,
} from "@strands-agents/sdk";

export class LoggingPlugin implements Plugin {
  get name(): string {
    return "logging";
  }

  initAgent(agent: LocalAgent): void {
    agent.addHook(BeforeToolCallEvent, (event) => {
      console.log(
        `[tool:before] ${event.toolUse.name}`,
        JSON.stringify(event.toolUse.input),
      );
    });

    agent.addHook(AfterToolCallEvent, (event) => {
      if (event.error) {
        console.error(
          `[tool:after]  ${event.toolUse.name} failed:`,
          event.error.message,
        );
      } else {
        console.log(`[tool:after]  ${event.toolUse.name} ok`);
      }
    });
  }
}
