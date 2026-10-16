# syntax=docker/dockerfile:1
#
# Amazon Bedrock AgentCore Runtime image.
# AgentCore requires an ARM64 container that serves /ping + /invocations on :8080.
# Build:  docker build --platform linux/arm64 -f agentcore/Dockerfile -t strands-agentcore .
FROM --platform=linux/arm64 node:22-slim
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY lib ./lib
COPY agentcore ./agentcore
COPY tsconfig.json ./

ENV NODE_ENV=production
ENV PORT=8080
EXPOSE 8080

# tsx runs the TypeScript entrypoint directly (no separate build step).
CMD ["npx", "tsx", "agentcore/server.ts"]
