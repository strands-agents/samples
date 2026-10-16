/**
 * Strands sessions.
 *
 * Sessions persist conversation state across requests via pluggable storage:
 * - `memory` (default): in-process, resets on restart. Good for local dev and
 *   stateless/serverless demos.
 * - `file`: local filesystem under `SESSION_DIR`. Good for a single long-lived
 *   container.
 * - `s3`: Amazon S3. Good for serverless + the AgentCore container path, where
 *   state must survive across instances. Set `SESSION_S3_BUCKET`.
 *
 * A `SessionManager` is itself a Strands plugin — pass it to the agent and it
 * saves/restores the conversation for the given `sessionId`.
 */
import { SessionManager } from "@strands-agents/sdk";

export type SessionBackend = "memory" | "file" | "s3";

export async function createSessionManager(
  sessionId: string,
): Promise<SessionManager> {
  const backend = (process.env.SESSION_BACKEND ?? "memory") as SessionBackend;

  switch (backend) {
    case "file": {
      const { LocalFileStorage } = await import("@strands-agents/sdk/storage");
      const baseDir = process.env.SESSION_DIR ?? "./.sessions";
      return new SessionManager({
        storage: new LocalFileStorage(baseDir),
        sessionId,
      });
    }
    case "s3": {
      const { S3Storage } = await import("@strands-agents/sdk/storage");
      const bucket = process.env.SESSION_S3_BUCKET;
      if (!bucket) {
        throw new Error(
          "SESSION_BACKEND=s3 requires SESSION_S3_BUCKET to be set.",
        );
      }
      return new SessionManager({
        storage: new S3Storage(bucket, {
          prefix: process.env.SESSION_S3_PREFIX ?? "sessions/",
          ...(process.env.AWS_REGION ? { region: process.env.AWS_REGION } : {}),
        }),
        sessionId,
      });
    }
    case "memory":
    default: {
      const { InMemoryStorage } = await import("@strands-agents/sdk/storage");
      return new SessionManager({
        storage: new InMemoryStorage(),
        sessionId,
      });
    }
  }
}
