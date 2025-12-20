# Amazon Bedrock AgentCore Runtime Container
#
# Container Requirements (per AWS documentation):
#   - Platform: ARM64 (required for AgentCore Runtime compatibility)
#   - Host: 0.0.0.0
#   - Port: 8080 

FROM --platform=linux/arm64 public.ecr.aws/docker/library/node:20-slim

WORKDIR /app

# Install dependencies first (leverages Docker layer caching for faster rebuilds)
COPY package*.json ./
RUN npm ci

# Copy TypeScript configuration and source code
COPY tsconfig.json ./
COPY src ./src

# Compile TypeScript to JavaScript
RUN npm run build

# Remove dev dependencies to reduce container image size for deployment
RUN npm prune --production

# AgentCore Runtime requires port 8080 for HTTP protocol communication
EXPOSE 8080

# Start the agent server
CMD ["node", "dist/agent.js"]
