/**
 * Custom Tools Tutorial - Appointment Management System
 *
 * Entry point for the Appointment Management Agent.
 * Orchestrates a Strands agent using Claude 3.5 Haiku (via Amazon Bedrock) to manage
 * appointments through natural language.
 *
 * This example demonstrates how to create custom tools with:
 * - Class-based architecture
 * - SQLite database integration
 * - Zod schema validation
 * - Type-safe tool definitions
 * - Multi-tool agent workflows
 *
 * Flow: User Input → Agent → Tool Selection → Database → Response
 */


import { Agent, BedrockModel } from "@strands-agents/sdk";
import { AppointmentDatabase } from "./database/AppointmentDatabase.js";
import { AppointmentTools } from "./tools/AppointmentTools.js";

// Agent Setup
// This is the system prompt for the agent
const systemPrompt = `You are a helpful personal assistant that specializes in managing my appointments and calendar. You have access to appointment management tools to help me organize my schedule effectively. Always provide the appointment id so that I can update it if required`;

async function main() {
  // Initialize database
  const database = new AppointmentDatabase();

  // Initialize tools with database dependency
  const appointmentTools = new AppointmentTools(database);

  // Get all tools
  const tools = appointmentTools.getAllTools();

  // Create agent with appointment management tools
  const agent = new Agent({
    model: new BedrockModel({
      modelId: "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    }),
    systemPrompt,
    tools,
  });

  // ===============================
  // Example Usage
  // ===============================

  // Example 1: Create an appointment
  console.log("Example 1: Creating an appointment\n");

  const userQuery1 = "Book 'Agent fun' for tomorrow 3pm in NYC. This meeting will discuss all the fun things that an agent can do";
  console.log("User:", userQuery1, "\n");

  let response = await agent.invoke(userQuery1);

  let messageContent = response.lastMessage.content[0];
  if (messageContent.type === "textBlock") {
    console.log("Agent:", messageContent.text);
  }
  console.log("\n" + "=".repeat(70) + "\n");

  // Example 2: Update an appointment
  console.log("Example 2: Updating an appointment\n");

  const userQuery2 = "Oh no! My bad, 'Agent fun' is actually happening in DC";
  console.log("User:", userQuery2, "\n");

  response = await agent.invoke(userQuery2);

  messageContent = response.lastMessage.content[0];
  if (messageContent.type === "textBlock") {
    console.log("Agent:", messageContent.text);
  }
  console.log("\n" + "=".repeat(70) + "\n");

  // Example 3: Create another appointment
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
  database.close();
}

main().catch(console.error);
