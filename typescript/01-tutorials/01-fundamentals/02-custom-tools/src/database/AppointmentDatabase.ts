/**
 * AppointmentDatabase.ts
 * 
 * SQLite data access layer for appointment storage using better-sqlite3.
 * 
 * Provides CRUD operations:
 * - createAppointment(): Insert new appointment with auto-generated UUID
 * - listAppointments(): Retrieve all appointments ordered by date
 * - updateAppointment(): Dynamically update specific fields by ID
 * - close(): Clean up database connection
 */


import Database from "better-sqlite3";
import { randomUUID } from "crypto";

export interface Appointment {
  id: string;
  date: string;
  location: string;
  title: string;
  description: string;
}

export interface AppointmentUpdate {
  date?: string;
  location?: string;
  title?: string;
  description?: string;
}

export class AppointmentDatabase {
  private db: Database.Database;

  constructor(databasePath: string = "appointments.db") {
    this.db = new Database(databasePath);
    this.initializeTables();
  }

  /**
   * Initialize database tables
   */
  private initializeTables(): void {
    this.db.exec(`
    CREATE TABLE IF NOT EXISTS appointments (
      id TEXT PRIMARY KEY,
      date TEXT NOT NULL,
      location TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL
    )
  `);
  }

  /**
   * Create a new appointment
   */
  createAppointment(
    date: string,
    location: string,
    title: string,
    description: string
  ): string {
    const id = randomUUID(); // Generate a unique identifier for the appointment

    // This creates the SQL query string to insert the appointment into the database
    const stmt = this.db.prepare(`
    INSERT INTO appointments (id, date, location, title, description)
    VALUES (?, ?, ?, ?, ?)
  `);

    // This runs the SQL query and returns the number of rows inserted
    stmt.run(id, date, location, title, description);

    return id;
  }

  /**
   * List all appointments ordered by date
   */
  listAppointments(): Appointment[] {
    // This creates the SQL query string to select all appointments ordered by date
    const stmt = this.db.prepare("SELECT * FROM appointments ORDER BY date");
    // This runs the SQL query and returns the results
    return stmt.all() as Appointment[];
  }

  /**
   * Update an existing appointment
   */
  updateAppointment(id: string, updates: AppointmentUpdate): number {
    // Build dynamic UPDATE query based on provided fields
    // Get only the fields that are actually provided in the updates object
    const fields = Object.keys(updates).filter(
      (key) => updates[key as keyof AppointmentUpdate] !== undefined
    );

    if (fields.length === 0) {
      return 0;
    }

    // Build dynamic SQL query based on the fields that are provided in the updates object
    // This creates a string like "date = ?, location = ?, title = ?, description = ?" for the SET part of the SQL query
    const setClause = fields.map((field) => `${field} = ?`).join(", ");
    // This creates an array of values for the SET part of the SQL query
    const values = fields.map((field) => updates[field as keyof AppointmentUpdate]);

    // This creates the SQL query string
    //  Example Query:
    // UPDATE appointments
    // SET date = ?
    // WHERE id = ?
    const stmt = this.db.prepare(`
    UPDATE appointments
    SET ${setClause}
    WHERE id = ?
  `);

    /**
     * What happens:
     * - prepare() creates a SQL statement with placeholders (?)
     * - run(...values, id) fills in the placeholders
     * - The ... (spread operator) unpacks the array
     */
    const result = stmt.run(...values, id);

    return result.changes; // Return the number of rows updated
  }

  /**
   * Close database connection
   */
  close(): void {
    this.db.close();
  }
}
