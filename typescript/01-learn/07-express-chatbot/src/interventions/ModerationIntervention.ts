/**
 * ModerationIntervention — a minimal content-moderation policy.
 *
 * Implemented as a Strands `InterventionHandler` that overrides `beforeModelCall`.
 * Before each model call it scans the most recent user message for any
 * configured blocked term (case-insensitive). On a match it returns
 * `deny(...)`, which stops the model call and surfaces a safe refusal message
 * instead of generating a response.
 *
 * This is deliberately simple (substring matching) to illustrate the pattern.
 * Swap the check for a real moderation model or service in production.
 */

import {
  InterventionHandler,
  InterventionActions,
  TextBlock,
  type BeforeModelCallEvent,
} from "@strands-agents/sdk";

export class ModerationIntervention extends InterventionHandler {
  readonly name = "moderation";
  /** Fail closed: if the policy check throws, deny rather than proceed. */
  override readonly onError = "deny" as const;

  private readonly blockedTerms: string[];

  constructor(blockedTerms: string[]) {
    super();
    this.blockedTerms = blockedTerms.map((term) => term.toLowerCase());
  }

  override beforeModelCall(
    event: BeforeModelCallEvent,
  ):
    | ReturnType<typeof InterventionActions.proceed>
    | ReturnType<typeof InterventionActions.deny> {
    if (this.blockedTerms.length === 0) {
      return InterventionActions.proceed();
    }

    const messages = event.agent.messages;
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser) {
      return InterventionActions.proceed();
    }

    const text = lastUser.content
      .filter((block): block is TextBlock => block instanceof TextBlock)
      .map((block) => block.text)
      .join(" ")
      .toLowerCase();

    const matched = this.blockedTerms.find((term) => text.includes(term));
    if (matched) {
      return InterventionActions.deny(
        "This request was blocked by the content moderation policy. " +
          "Respond with a brief, polite refusal and do not fulfil the request.",
      );
    }

    return InterventionActions.proceed();
  }
}
