# Running Strands Agents in the Browser

## Overview

This tutorial demonstrates how to run a Strands Agent entirely in the browser using the TypeScript SDK with Vite as the build tool. The example creates a simple chat interface where users can interact with an AI agent directly from their web browser.

| Feature | Description |
|---------|-------------|
| Architecture | Client-side only (browser) |
| Build Tool | Vite |
| Model Provider | Amazon Bedrock (default) |

## Prerequisites

- Node.js 18.x or later
- AWS credentials configured for Amazon Bedrock access
- Basic TypeScript and web development knowledge

## Project Structure

```
03-browser-agent/
├── index.html          # Entry HTML with chat UI
├── src/
│   ├── main.ts        # Agent setup and DOM interaction
│   ├── style.css      # Chat interface styling
│   └── vite-env.d.ts  # Vite type declarations
├── package.json       # Dependencies
├── tsconfig.json      # TypeScript configuration
├── vite.config.ts     # Vite configuration
└── README.md          # This file
```

## Running the Example

```bash
cd typescript/01-tutorials/01-fundamentals/03-browser-agent
npm install
npm run dev
```

This will start the Vite dev server and open `http://localhost:5173` in your browser.

## Key Concepts

### Browser-Based Agent

The agent runs entirely in the browser, which means:

1. **No backend required** - The SDK handles API calls directly from the browser
2. **Simple deployment** - Can be hosted on any static file server
3. **Real-time interaction** - Direct communication with the model provider

### Agent Configuration

```typescript
import { Agent } from "@strands-agents/sdk";

const agent = new Agent({
  systemPrompt: "You are a helpful assistant running in the browser."
});

// Invoke the agent with user input
const response = await agent.invoke(userMessage);
```

### Vite for Browser Development

Vite provides:
- Hot Module Replacement (HMR) for fast development
- TypeScript support out of the box
- Optimized production builds
- ES module support

## Security Considerations

When running agents in the browser, be aware of:

1. **API Keys Exposure** - Any credentials used in browser code are visible in the network tab
2. **For Production** - Consider using a backend proxy with proper authentication
3. **Development Only** - This tutorial is intended for development and demonstration purposes

## Building for Production

```bash
npm run build
```

This creates an optimized build in the `dist/` directory that can be deployed to any static hosting service.

## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Vite Documentation](https://vitejs.dev/)
