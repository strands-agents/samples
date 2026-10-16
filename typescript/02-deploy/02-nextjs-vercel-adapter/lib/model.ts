/**
 * Model selection.
 *
 * The **Vercel AI SDK owns the providers**: we build a `LanguageModelV3` with
 * `@ai-sdk/*` (Amazon Bedrock by default, OpenAI optional) and hand it to Strands
 * through the `VercelModel` adapter. Strands then drives the agent loop, tools,
 * sessions, and hooks on top of that provider.
 *
 * Switch providers with a single env var (`MODEL_PROVIDER`) — no code changes.
 */
import type { LanguageModelV3 } from "@ai-sdk/provider";
import { VercelModel } from "@strands-agents/sdk/models/vercel";

export type ProviderName = "bedrock" | "openai";

/**
 * Resolve the configured provider into a Vercel AI SDK `LanguageModelV3`.
 *
 * Providers are imported lazily so an app that only uses one provider never
 * needs the other provider's credentials or bundle.
 */
async function resolveProvider(): Promise<LanguageModelV3> {
  const provider = (process.env.MODEL_PROVIDER ?? "bedrock") as ProviderName;

  switch (provider) {
    case "openai": {
      const { openai } = await import("@ai-sdk/openai");
      const modelId = process.env.OPENAI_MODEL_ID ?? "gpt-4o-mini";
      // Uses OPENAI_API_KEY from the environment.
      return openai(modelId) as unknown as LanguageModelV3;
    }
    case "bedrock":
    default: {
      const { bedrock } = await import("@ai-sdk/amazon-bedrock");
      const modelId =
        process.env.BEDROCK_MODEL_ID ?? "us.amazon.nova-pro-v1:0";
      // Uses the standard AWS credential chain / AWS_REGION from the environment.
      return bedrock(modelId) as unknown as LanguageModelV3;
    }
  }
}

/**
 * Build the Strands model: a Vercel AI SDK provider wrapped by `VercelModel`.
 */
export async function createModel(): Promise<VercelModel> {
  const provider = await resolveProvider();
  return new VercelModel({ provider });
}
