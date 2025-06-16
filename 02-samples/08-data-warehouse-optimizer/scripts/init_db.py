"""
Initialize SQLite database with sample sales_data table.
"""

import sqlite3


def init_db():
    """Create and populate sales_data table."""
    conn = sqlite3.connect("query_optimizer.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_data (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT,
            amount REAL
        )
    """
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO sales_data (order_id, customer_id, order_date, amount) "
        "VALUES (?, ?, ?, ?)",
        [
            (1, 101, "2025-01-01", 100.50),
            (2, 102, "2025-01-02", 200.75),
            (3, 101, "2025-01-03", 150.25),
        ],
    )
    conn.commit()
    conn.close()
    print("Database initialized with sales_data table.")


if __name__ == "__main__":
    init_db()
