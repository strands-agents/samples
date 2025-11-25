/**
 * Custom Tools Tutorial - Appointment Management System
 *
 * This example demonstrates how to create custom tools with:
 * - SQLite database integration
 * - Zod schema validation
 * - Type-safe tool definitions
 * - Multi-tool agent workflows
 */

import { Agent, BedrockModel, tool } from "@strands-agents/sdk";
import Database from "better-sqlite3";
import { z } from "zod";
import { randomUUID } from "crypto";

// ============================================================================
// DATABASE SETUP
// ============================================================================

// Initialize SQLite database
const db = new Database("appointments.db");

// Create appointments table
db.exec(`
  CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    location TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL
  )
`);

// ============================================================================
// CUSTOM TOOLS DEFINITION
// ============================================================================

/**
 * Tool 1: Create Appointment
 * Creates a new personal appointment in the database
 */
const createAppointment = tool({
  name: "create_appointment",
  description: "Create a new personal appointment in the database. Args: date (str): Date and time of the appointment (format: YYYY-MM-DD HH:MM). location (str): Location of the appointment. title (str): Title of the appointment. description (str): Description of the appointment. Returns: str: The ID of the newly created appointment.",
  inputSchema: z.object({
    date: z.string(),
    location: z.string(),
    title: z.string(),
    description: z.string()
  }),
  callback: (input) => {
    const id = randomUUID();

    const stmt = db.prepare(`
      INSERT INTO appointments (id, date, location, title, description)
      VALUES (?, ?, ?, ?, ?)
    `);

    stmt.run(id, input.date, input.location, input.title, input.description);

    return `Appointment created successfully with ID: ${id}`;
  }
});

/**
 * Tool 2: List Appointments
 * Lists all available appointments from the database
 */
const listAppointments = tool({
  name: "list_appointments",
  description: "List all available appointments from the database. Returns: str: the appointments available",
  inputSchema: z.object({}), // No input parameters needed
  callback: () => {
    const stmt = db.prepare("SELECT * FROM appointments ORDER BY date");
    const appointments = stmt.all();

    if (appointments.length === 0) {
      return "No appointments found.";
    }

    return JSON.stringify(appointments, null, 2);
  }
});

/**
 * Tool 3: Update Appointment
 * Update an appointment based on the appointment ID
 */
const updateAppointment = tool({
  name: "update_appointment",
  description: "Update an appointment based on the appointment ID.",
  inputSchema: z.object({
    appointment_id: z.string(),
    date: z.string().optional(),
    location: z.string().optional(),
    title: z.string().optional(),
    description: z.string().optional()
  }),
  callback: (input) => {
    const { appointment_id, ...updates } = input;

    // Build dynamic UPDATE query based on provided fields
    const fields = Object.keys(updates).filter(key => updates[key as keyof typeof updates] !== undefined);

    if (fields.length === 0) {
      return "No fields to update.";
    }

    const setClause = fields.map(field => `${field} = ?`).join(", ");
    const values = fields.map(field => updates[field as keyof typeof updates]);

    const stmt = db.prepare(`
      UPDATE appointments
      SET ${setClause}
      WHERE id = ?
    `);

    const result = stmt.run(...values, appointment_id);

    if (result.changes === 0) {
      return `No appointment found with ID: ${appointment_id}`;
    }

    return `Appointment ${appointment_id} updated successfully`;
  }
});


// ============================================================================
// AGENT SETUP
// ============================================================================

const systemPrompt = `You are a helpful personal assistant that specializes in managing my appointments and calendar. You have access to appointment management tools to help me organize my schedule effectively. Always provide the appointment id so that I can update it if required`;

async function main() {

  // Create agent with appointment management tools
  const agent = new Agent({
    model: new BedrockModel({
      modelId: "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    }),
    systemPrompt,
    tools: [createAppointment, listAppointments, updateAppointment]
  });

  // ========================================================================
  // Example 1: Create an appointment
  // ========================================================================
  console.log("Example 1: Creating an appointment\n");

  const userQuery1 = "Book 'Agent fun' for tomorrow 3pm in NYC. This meeting will discuss all the fun things that an agent can do";
  console.log("User:", userQuery1, "\n");

  let response = await agent.invoke(userQuery1);

  let messageContent = response.lastMessage.content[0];
  if (messageContent.type === "textBlock") {
    console.log("Agent:", messageContent.text);
  }
  console.log("\n" + "=".repeat(70) + "\n");

  // ========================================================================
  // Example 2: Update an appointment
  // ========================================================================
  console.log("Example 2: Updating an appointment\n");

  const userQuery2 = "Oh no! My bad, 'Agent fun' is actually happening in DC";
  console.log("User:", userQuery2, "\n");

  response = await agent.invoke(userQuery2);

  messageContent = response.lastMessage.content[0];
  if (messageContent.type === "textBlock") {
    console.log("Agent:", messageContent.text);
  }
  console.log("\n" + "=".repeat(70) + "\n");

  // ========================================================================
  // Example 3: Create another appointment
  // ========================================================================
  console.log("Example 3: Creating another appointment\n");

  const userQuery3 = "I want to add a new appointment for tomorrow at 2pm";
  console.log("User:", userQuery3, "\n");

  response = await agent.invoke(userQuery3);

  messageContent = response.lastMessage.content[0];
  if (messageContent.type === "textBlock") {
    console.log("Agent:", messageContent.text);
  }
  console.log("\n" + "=".repeat(70) + "\n");

  // Cleanup
  db.close();
}

main().catch(console.error);
