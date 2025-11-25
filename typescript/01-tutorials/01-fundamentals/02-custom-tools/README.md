# Adding custom tools to your Strands Agents

## Overview

In this example we will guide you through the different ways to create custom tools using Strands Agents. We will build a personal assistant use case that connects with a local SQLite database to perform data tasks. 

## What You'll Build

A personal assistant agent that manages appointments using:
- **Custom tools** - Three tools for creating, listing, and updating appointments
- **SQLite database** - Persistent storage for appointment data
- **Natural language interface** - Conversational interaction with the agent

## Prerequisites

- Node.js 18.x or later
- AWS account with Amazon Bedrock access
- Basic TypeScript knowledge

## Running the Example

```bash
cd typescript/01-tutorials/01-fundamentals/02-custom-tools
npm install
npx tsx src/index.ts
```

## Custom Tools Overview

This example demonstrates three custom tools:

### 1. Create Appointment
Creates a new appointment with date, location, title, and description.

### 2. List Appointments
Retrieves all appointments from the database.

### 3. Update Appointment
Modifies an existing appointment by ID.

## Tool Definition Pattern

Custom tools are defined using the `tool()` function:

```typescript
const createAppointment = tool({
  name: "create_appointment",
  description: "Create a new personal appointment in the database...",
  inputSchema: z.object({
    date: z.string(),
    location: z.string(),
    title: z.string(),
    description: z.string()
  }),
  callback: (input) => {
    // Tool implementation
    return `Appointment created successfully with ID: ${id}`;
  }
});
```

## Database Integration

The example uses `better-sqlite3` for:
- Synchronous SQLite operations
- Simple table creation and queries
- Persistent appointment storage

## Agent Configuration

```typescript
const agent = new Agent({
  model: new BedrockModel({
    modelId: "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  }),
  systemPrompt: "You are a helpful personal assistant...",
  tools: [createAppointment, listAppointments, updateAppointment]
});
```
