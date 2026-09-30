# Adding custom tools to your Strands Agents

## Overview

In this example we will guide you through creating custom tools using the Strands Agents `tool()` function. We will build a personal assistant that connects with a local SQLite database to manage appointments, turn by turn in your terminal.

![Custom Tools Architecture](images/agent_with_custom_tools.png)

| Feature | Description |
|---------|-------------|
| Custom tools created | create_appointment, list_appointments, update_appointment, delete_appointment, check_availability |
| Agent Structure | Single agent architecture |
| Interaction | Guided demo, then turn-by-turn chat |

## What the assistant does

- **Books, lists, moves and cancels appointments** in plain English: "Book a 30 minute call with Priya on Friday at 11am", "Move Design review to 4pm", "Cancel the gym session".
- **Understands relative dates.** It is told today's date and your local time zone, so "tomorrow at 3pm" resolves correctly.
- **Never double-books.** The tools check for overlapping appointments before saving. When a slot is busy, nothing is saved; the agent tells you what clashes, offers free times from the calendar, and waits for you to choose.
- **Asks before it acts on anything destructive.** Cancelling takes two steps: the agent shows the appointment and asks you to confirm before it deletes anything.
- **Asks for what's missing** instead of inventing it. A title, a time and a location are enough; appointments last 60 minutes unless you say otherwise.

## Prerequisites

- Node.js 22 or later (the version `@strands-agents/sdk` supports)
- AWS credentials with Amazon Bedrock access, and the model enabled in your region
- Basic TypeScript knowledge

## Running the Example

```bash
cd typescript/01-learn/02-custom-tools
npm install
npx tsx src/index.ts
```

This runs the **guided demo**:

1. Books "Agent fun" for tomorrow at 3pm in NYC.
2. Moves it to DC.
3. Tries to book "Design review" tomorrow at 3pm. **The calendar is busy**, so the agent stops, explains the clash, suggests free times, and asks you what to do.
4. **Your turn.** Answer the agent (for example "4pm works"), then keep chatting as long as you like.

### Modes and options

| Command | What it does |
|---|---|
| `npx tsx src/index.ts` | Guided demo, then you take over |
| `npx tsx src/index.ts --chat` | Chat from the first turn, no scripted requests |
| `npx tsx src/index.ts --auto` | The three scripted requests only, no input (useful for quick checks) |
| `npx tsx src/index.ts --help` | Show all options |

| Option | Environment variable | Default |
|---|---|---|
| `--region <region>` | `AWS_REGION` | `us-east-1` |
| `--model <model-id>` | `MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `--db <path>` | `APPOINTMENTS_DB` | `appointments.db` |

Flags win over environment variables. For example:

```bash
npx tsx src/index.ts --chat --region us-west-2 --model global.anthropic.claude-sonnet-4-6
```

### In the chat

| Type | To |
|---|---|
| Any request in plain English | Talk to the assistant |
| `/calendar` | Print the saved appointments straight from the database |
| `/help` | Show example requests |
| `exit` | Quit and print the final calendar |

Delete `appointments.db` to start again with an empty calendar.

## Project Structure

```
src/
├── database/
│   └── AppointmentDatabase.ts    # SQLite data access, overlap checks, free slots
├── tools/
│   └── AppointmentTools.ts       # Tool definitions factory
└── index.ts                      # Entry point: options, guided demo, chat loop
```

## Key Concepts

### Class-Based Tool Organization

Tools are organized using a factory class pattern that encapsulates tool creation and database dependencies:

```typescript
export class AppointmentTools {
  constructor(private database: AppointmentDatabase) { }

  getCreateAppointmentTool() {
    return tool({
      name: "create_appointment",
      description: "Create a new personal appointment. Checks the calendar first...",
      inputSchema: z.object({ date, duration_minutes, location, title, description }),
      callback: (input) => {
        const conflict = this.conflictResult(input.date, duration);
        if (conflict) return conflict; // nothing saved; the agent asks the user
        const id = this.database.createAppointment(...);
        return `Appointment created successfully with ID: ${id}`;
      }
    });
  }

  getAllTools() {
    return [
      this.getCreateAppointmentTool(),
      this.getListAppointmentsTool(),
      this.getUpdateAppointmentTool(),
      this.getDeleteAppointmentTool(),
      this.getCheckAvailabilityTool(),
    ];
  }
}
```

### Tools that return decisions, not just data

A tool result can tell the agent that it needs the user. When a slot is taken, `create_appointment` and `update_appointment` return:

```json
{
  "status": "conflict",
  "message": "The calendar is busy at that time. Nothing was saved. Ask the user how to proceed, offering only start times from free_slots_that_day.",
  "conflicts": [{ "title": "Agent fun", "date": "2026-10-01 15:00", "duration_minutes": 60 }],
  "free_slots_that_day": ["09:00", "09:30", "…", "14:00", "16:00", "16:30", "17:00"]
}
```

The rule lives in the tool, so the agent cannot double-book even if it tries. `delete_appointment` works the same way: without `confirmed: true` it returns `needs_confirmation` and deletes nothing.

### Database Integration

The `AppointmentDatabase` class uses `better-sqlite3` to store appointment information. Existing databases from earlier versions of this sample are upgraded automatically.

```typescript
export class AppointmentDatabase {
  createAppointment(date, location, title, description, durationMinutes?): string
  listAppointments(): Appointment[]
  updateAppointment(id, updates): number
  deleteAppointment(id): number
  findConflicts(date, durationMinutes, ignoreId?): Appointment[]
  freeSlots(day, durationMinutes?): string[]
}
```

### Agent Configuration

```typescript
const agent = new Agent({
  model: new BedrockModel({ modelId: config.modelId, region: config.region }),
  systemPrompt, // includes today's date, the default duration, and the clash rules
  tools,
});
```

The agent streams its replies, and the tools it calls, to the terminal as they happen.

## Additional Resources

- [Strands Agents Documentation](https://strandsagents.com/latest/)
