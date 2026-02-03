/**
 * AppointmentTools - Factory class for creating appointment management tools
 *
 * Tool definitions for the Strands appointment management agent.
 * This class provides methods to create tool instances that interact with
 * the AppointmentDatabase. Wraps database operations as LLM-callable tools
 * with Zod schema validation.
 *
 * Available Tools:
 * - create_appointment: Create new appointment (date, location, title, description)
 * - list_appointments: Retrieve all scheduled appointments
 * - update_appointment: Modify existing appointment by ID
 */

import { tool } from "@strands-agents/sdk";
import { z } from "zod";
import { AppointmentDatabase } from "../database/AppointmentDatabase.js";

export class AppointmentTools {
  constructor(private database: AppointmentDatabase) { }

  /**
   * Get the create appointment tool
   */
  getCreateAppointmentTool() {
    return tool({
      // 1. Name of the tool
      name: "create_appointment",
      // 2. Description of the tool
      description:
        "Create a new personal appointment in the database with date (format: YYYY-MM-DD HH:MM), location, title, and description. Returns the appointment ID.",
      // 3. Input schema of the tool
      inputSchema: z.object({
        date: z.string(),
        location: z.string(),
        title: z.string(),
        description: z.string(),
      }),
      // 4. Callback function of the tool 
      // This function takes the input parameters and returns the result
      callback: (input) => {
        // This creates the appointment in the database
        const id = this.database.createAppointment(
          input.date,
          input.location,
          input.title,
          input.description
        );
        // This returns the result of the tool
        return `Appointment created successfully with ID: ${id}`;
      },
    });
  }

  /**
   * Get the list appointments tool
   */
  getListAppointmentsTool() {
    return tool({
      // 1. Name of the tool
      name: "list_appointments",
      // 2. Description of the tool
      description: "List all appointments from the database, ordered by date.",
      // 3. Input schema of the tool
      inputSchema: z.object({}), // No input parameters needed
      // 4. Callback function of the tool
      callback: () => {
        // This lists all the appointments from the database
        const appointments = this.database.listAppointments();

        if (appointments.length === 0) {
          // If no appointments were found, return an error message
          return "No appointments found.";
        }

        // This returns the appointments as a JSON string
        return JSON.stringify(appointments, null, 2);
      },
    });
  }

  /**
   * Get the update appointment tool
   */
  getUpdateAppointmentTool() {
    return tool({
      // 1. Name of the tool
      name: "update_appointment",
      // 2. Description of the tool
      description: "Update an existing appointment by ID.",
      inputSchema: z.object({
        appointment_id: z.string(), // Required appointment_id parameter
        date: z.string().optional(), // Optional date parameter
        location: z.string().optional(), // Optional location parameter
        title: z.string().optional(), // Optional title parameter
        description: z.string().optional(), // Optional description parameter
      }),
      // 4. Callback function of the tool
      callback: (input) => {
        // This extracts the appointment_id and the updates from the input
        const { appointment_id, ...updates } = input;

        // This updates the appointment in the database
        const changes = this.database.updateAppointment(appointment_id, updates);

        if (changes === 0) {
          // If no changes were made, return an error message
          return Object.keys(updates).length > 0
            ? `No appointment found with ID: ${appointment_id}` // If no appointment was found, return an error message
            : "No fields to update."; // If no fields to update, return an error message
        }

        // This returns the result of the tool
        return `Appointment ${appointment_id} updated successfully`;
      },
    });
  }

  /**
   * Get all appointment tools
   */
  // Returns an array of tool definitions that can be used by the agent
  getAllTools() {
    return [
      this.getCreateAppointmentTool(),
      this.getListAppointmentsTool(),
      this.getUpdateAppointmentTool(),
    ];
  }
}
