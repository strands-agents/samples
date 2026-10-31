/**
 * AppointmentDatabase.ts
 *
 * SQLite data access layer for appointment storage using better-sqlite3.
 *
 * Provides:
 * - createAppointment(): Insert new appointment with auto-generated UUID
 * - listAppointments(): Retrieve all appointments ordered by date
 * - updateAppointment(): Dynamically update specific fields by ID
 * - deleteAppointment(): Remove an appointment by ID
 * - findConflicts(): Find appointments that overlap a time range
 * - freeSlots(): Find open time slots on a given day
 * - close(): Clean up database connection
 *
 * Dates are stored as local "YYYY-MM-DD HH:MM" strings. Each appointment has a
 * duration in minutes (default 60), which is what overlap checks use.
 */

import Database from "better-sqlite3";
import { randomUUID } from "crypto";

export const DEFAULT_DURATION_MINUTES = 60;

export interface Appointment {
  id: string;
  date: string;
  duration_minutes: number;
  location: string;
  title: string;
  description: string;
}

export interface AppointmentUpdate {
  date?: string;
  duration_minutes?: number;
  location?: string;
  title?: string;
  description?: string;
}

/**
 * Parse "YYYY-MM-DD HH:MM" into minutes since the epoch (local time).
 * Returns undefined for anything that is not in that format.
 */
export function toMinutes(date: string): number | undefined {
  const match = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})$/.exec(date.trim());
  if (!match) return undefined;
  const [, y, mo, d, h, mi] = match.map(Number);
  return new Date(y, mo - 1, d, h, mi).getTime() / 60000;
}

/** Format minutes since the epoch back into "YYYY-MM-DD HH:MM" (local time). */
export function fromMinutes(minutes: number): string {
  const t = new Date(minutes * 60000);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())} ${pad(t.getHours())}:${pad(t.getMinutes())}`;
}

export class AppointmentDatabase {
  private db: Database.Database;

  constructor(databasePath: string = "appointments.db") {
    this.db = new Database(databasePath);
    this.initializeTables();
  }

  /**
   * Initialize database tables, adding the duration column to databases
   * created by earlier versions of this sample.
   */
  private initializeTables(): void {
    this.db.exec(`
    CREATE TABLE IF NOT EXISTS appointments (
      id TEXT PRIMARY KEY,
      date TEXT NOT NULL,
      duration_minutes INTEGER NOT NULL DEFAULT ${DEFAULT_DURATION_MINUTES},
      location TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL
    )
  `);
    const columns = this.db.prepare("PRAGMA table_info(appointments)").all() as { name: string }[];
    if (!columns.some((c) => c.name === "duration_minutes")) {
      this.db.exec(
        `ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT ${DEFAULT_DURATION_MINUTES}`
      );
    }
  }

  /**
   * Create a new appointment
   */
  createAppointment(
    date: string,
    location: string,
    title: string,
    description: string,
    durationMinutes: number = DEFAULT_DURATION_MINUTES
  ): string {
    const id = randomUUID(); // Generate a unique identifier for the appointment

    const stmt = this.db.prepare(`
    INSERT INTO appointments (id, date, duration_minutes, location, title, description)
    VALUES (?, ?, ?, ?, ?, ?)
  `);
    stmt.run(id, date, durationMinutes, location, title, description);

    return id;
  }

  /**
   * List all appointments ordered by date
   */
  listAppointments(): Appointment[] {
    const stmt = this.db.prepare("SELECT * FROM appointments ORDER BY date");
    return stmt.all() as Appointment[];
  }

  /**
   * Get one appointment by ID
   */
  getAppointment(id: string): Appointment | undefined {
    return this.db.prepare("SELECT * FROM appointments WHERE id = ?").get(id) as Appointment | undefined;
  }

  /**
   * Update an existing appointment
   */
  updateAppointment(id: string, updates: AppointmentUpdate): number {
    // Only update the fields that were actually provided
    const fields = Object.keys(updates).filter(
      (key) => updates[key as keyof AppointmentUpdate] !== undefined
    );

    if (fields.length === 0) {
      return 0;
    }

    // Builds "date = ?, location = ?" for the SET clause; values fill the placeholders
    const setClause = fields.map((field) => `${field} = ?`).join(", ");
    const values = fields.map((field) => updates[field as keyof AppointmentUpdate]);

    const stmt = this.db.prepare(`
    UPDATE appointments
    SET ${setClause}
    WHERE id = ?
  `);

    const result = stmt.run(...values, id);
    return result.changes; // Number of rows updated
  }

  /**
   * Delete an appointment by ID. Returns the number of rows removed.
   */
  deleteAppointment(id: string): number {
    return this.db.prepare("DELETE FROM appointments WHERE id = ?").run(id).changes;
  }

  /**
   * Find appointments that overlap [date, date + durationMinutes).
   * Pass ignoreId to skip the appointment being rescheduled.
   */
  findConflicts(date: string, durationMinutes: number, ignoreId?: string): Appointment[] {
    const start = toMinutes(date);
    if (start === undefined) return [];
    const end = start + durationMinutes;

    return this.listAppointments().filter((a) => {
      if (a.id === ignoreId) return false;
      const aStart = toMinutes(a.date);
      if (aStart === undefined) return false;
      const aEnd = aStart + (a.duration_minutes || DEFAULT_DURATION_MINUTES);
      return start < aEnd && aStart < end;
    });
  }

  /**
   * Open slots of durationMinutes on the given day (YYYY-MM-DD), on the hour
   * and half hour, between workday start and end hours.
   */
  freeSlots(day: string, durationMinutes: number = DEFAULT_DURATION_MINUTES, startHour = 9, endHour = 18): string[] {
    const dayStart = toMinutes(`${day} ${String(startHour).padStart(2, "0")}:00`);
    const dayEnd = toMinutes(`${day} ${String(endHour).padStart(2, "0")}:00`);
    if (dayStart === undefined || dayEnd === undefined) return [];

    const slots: string[] = [];
    for (let t = dayStart; t + durationMinutes <= dayEnd; t += 30) {
      if (this.findConflicts(fromMinutes(t), durationMinutes).length === 0) {
        slots.push(fromMinutes(t).slice(11));
      }
    }
    return slots;
  }

  /**
   * Close database connection
   */
  close(): void {
    this.db.close();
  }
}
