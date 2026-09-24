import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a standalone server bundle for a minimal production Docker image.
  output: "standalone",
  // Allow dev-server access (HMR/WebSocket and other _next dev resources) when
  // reaching the app via the LAN IP instead of localhost. Only affects `next dev`.
  allowedDevOrigins: ["192.168.100.162"],
  // Strands and the AWS SDK are Node-only; keep them external to the server
  // bundle so they load from node_modules at runtime instead of being bundled.
  serverExternalPackages: [
    "@strands-agents/sdk",
    "@ai-sdk/amazon-bedrock",
    "@aws-sdk/client-bedrock-runtime",
    "@aws-sdk/client-s3",
  ],
};

export default nextConfig;
