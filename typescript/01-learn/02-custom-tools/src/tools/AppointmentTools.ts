/**
 * AppointmentTools - Factory class for creating appointment management tools
 *
 * Tool definitions for the Strands appointment management agent.
 * This class provides methods to create tool instances that interact with
 * the AppointmentDatabase. Wraps database operations as LLM-callable tools
 * with Zod schema validation.
 *
 * Available Tools:
 * - create_appointment: Create new appointment, refusing slots that clash with an existing one
 * - list_appointments: Retrieve all scheduled appointments
 * - update_appointment: Modify existing appointment by ID, also checking for clashes
 * - delete_appointment: Cancel an appointment by ID
 * - check_availability: Show the free slots on a given day
 */

import { tool } from "@strands-agents/sdk";
import { z } from "zod";
import { AppointmentDatabase, DEFAULT_DURATION_MINUTES, toMinutes } from "../database/AppointmentDatabase.js";

const dateField = z.string().describe("Start time in local time, format YYYY-MM-DD HH:MM (24-hour)");
const durationField = z
  .number()
  .int()
  .positive()
  .optional()
  .describe(`Length in minutes (default ${DEFAULT_DURATION_MINUTES})`);

export class AppointmentTools {
  constructor(private database: AppointmentDatabase) { }

  /**
   * Describe a clash so the agent can explain it and offer alternatives.
   * The agent must then ask the user what to do rather than choosing for them.
   */
  private conflictResult(date: string, durationMinutes: number, ignoreId?: string) {
    const conflicts = this.database.findConflicts(date, durationMinutes, ignoreId);
    if (conflicts.length === 0) return undefined;
    return JSON.stringify(
      {
        status: "conflict",
        message: "The calendar is busy at that time. Nothing was saved. Ask the user how to proceed, offering only start times from free_slots_that_day.",
        requested: { date, duration_minutes: durationMinutes },
        conflicts: conflicts.map(({ id, date, duration_minutes, title, location }) => ({
          id,
          date,
          duration_minutes,
          title,
          location,
        })),
        free_slots_that_day: this.database.freeSlots(date.slice(0, 10), durationMinutes),
      },
      null,
      2
    );
  }

  /**
   * Get the create appointment tool
   */
  getCreateAppointmentTool() {
    return tool({
      // 1. Name of the tool
      name: "create_appointment",
      // 2. Description of the tool
      description:
        "Create a new personal appointment. Checks the calendar first: if the slot overlaps an existing appointment, nothing is saved and the result has status 'conflict' with the clashing appointments and free slots that day. Returns the appointment ID on success.",
      // 3. Input schema of the tool
      inputSchema: z.object({
        date: dateField,
        duration_minutes: durationField,
        location: z.string(),
        title: z.string(),
        description: z.string().optional().describe("Optional notes about the appointment"),
      }),
      // 4. Callback function of the tool
      // This function takes the input parameters and returns the result
      callback: (input) => {
        if (toMinutes(input.date) === undefined) {
          return `Invalid date "${input.date}". Use YYYY-MM-DD HH:MM.`;
        }
        const duration = input.duration_minutes ?? DEFAULT_DURATION_MINUTES;

        // Refuse to double-book; the agent will ask the user what to do instead
        const conflict = this.conflictResult(input.date, duration);
        if (conflict) return conflict;

        // This creates the appointment in the database
        const id = this.database.createAppointment(
          input.date,
          input.location,
          input.title,
          input.description ?? "",
          duration
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
      description:
        "Update an existing appointment by ID. If the new time overlaps another appointment, nothing is changed and the result has status 'conflict'.",
      inputSchema: z.object({
        appointment_id: z.string(), // Required appointment_id parameter
        date: dateField.optional(), // Optional date parameter
        duration_minutes: durationField, // Optional duration parameter
        location: z.string().optional(), // Optional location parameter
        title: z.string().optional(), // Optional title parameter
        description: z.string().optional(), // Optional description parameter
      }),
      // 4. Callback function of the tool
      callback: (input) => {
        // This extracts the appointment_id and the updates from the input
        const { appointment_id, ...updates } = input;

        // A time change must not create a double booking
        if (updates.date !== undefined || updates.duration_minutes !== undefined) {
          const current = this.database.getAppointment(appointment_id);
          if (!current) return `No appointment found with ID: ${appointment_id}`;
          const date = updates.date ?? current.date;
          if (toMinutes(date) === undefined) return `Invalid date "${date}". Use YYYY-MM-DD HH:MM.`;
          const conflict = this.conflictResult(
            date,
            updates.duration_minutes ?? current.duration_minutes ?? DEFAULT_DURATION_MINUTES,
            appointment_id
          );
          if (conflict) return conflict;
        }

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
   * Get the delete appointment tool
   */
  getDeleteAppointmentTool() {
    return tool({
      name: "delete_appointment",
      description:
        "Cancel (delete) an appointment by ID. Two steps: first call with confirmed=false to get the appointment details, show them to the user and ask them to confirm. Only after the user replies yes in a later message, call again with confirmed=true.",
      inputSchema: z.object({
        appointment_id: z.string(),
        confirmed: z.boolean().describe("true only after the user has explicitly confirmed the cancellation"),
      }),
      callback: (input) => {
        const appointment = this.database.getAppointment(input.appointment_id);
        if (!appointment) return `No appointment found with ID: ${input.appointment_id}`;
        if (!input.confirmed) {
          return JSON.stringify({
            status: "needs_confirmation",
            message: "Nothing was deleted. Show this appointment to the user and ask them to confirm the cancellation.",
            appointment,
          });
        }
        this.database.deleteAppointment(input.appointment_id);
        return `Appointment ${input.appointment_id} cancelled`;
      },
    });
  }

  /**
   * Get the check availability tool
   */
  getCheckAvailabilityTool() {
    return tool({
      name: "check_availability",
      description:
        "List the start times (09:00–18:00, on the hour and half hour) at which a meeting of the given length fits without overlapping anything, plus the appointments already booked that day. Only these start times are free; do not suggest others.",
      inputSchema: z.object({
        day: z.string().describe("Day in format YYYY-MM-DD"),
        duration_minutes: durationField,
      }),
      callback: (input) => {
        const duration = input.duration_minutes ?? DEFAULT_DURATION_MINUTES;
        return JSON.stringify(
          {
            day: input.day,
            duration_minutes: duration,
            booked: this.database.listAppointments().filter((a) => a.date.startsWith(input.day)),
            free_slots: this.database.freeSlots(input.day, duration),
          },
          null,
          2
        );
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
      this.getDeleteAppointmentTool(),
      this.getCheckAvailabilityTool(),
    ];
  }
}
