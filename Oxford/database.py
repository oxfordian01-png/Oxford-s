"""
database.py
-----------
Everything about SAVING and LOADING data lives here, using SQLite (a
small database that lives in a single file - no server needed, perfect
for a student desktop app).

BEGINNER NOTE: Think of SQLite like an Excel workbook with several
sheets (we call them "tables"): customers, meter_readings, bills,
payments. Each row in a sheet is one record.

This file demonstrates:
  - File handling / persistent storage (a requirement of the project)
  - Exception handling (every risky operation is wrapped in try/except)
  - Modular programming (database logic is separate from GUI logic)
"""

import sqlite3
import os
from exceptions import (
    DuplicateCustomerError,
    CustomerNotFoundError,
    BillNotFoundError,
    PaymentError,
)


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "billing_system.db")


class DatabaseManager:
    """Wraps all SQLite operations in easy-to-call Python methods, so the
    GUI code never has to write raw SQL directly."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_tables(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            meter_number TEXT NOT NULL UNIQUE,
            customer_type TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS meter_readings (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            previous_reading REAL NOT NULL,
            current_reading REAL NOT NULL,
            reading_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE IF NOT EXISTS bills (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            reading_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            bill_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Unpaid',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (reading_id) REFERENCES meter_readings(reading_id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            payment_date TEXT NOT NULL,
            method TEXT NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(bill_id)
        );
        """)
        conn.commit()
        conn.close()

    # ---------------- CUSTOMERS ----------------
    def add_customer(self, customer):
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO customers (customer_id, name, address, phone, "
                "meter_number, customer_type) VALUES (?, ?, ?, ?, ?, ?)",
                (customer.customer_id, customer.name, customer.address,
                 customer.phone, customer.meter_number, customer.customer_type),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise DuplicateCustomerError(
                f"Customer ID or meter number already exists: "
                f"{customer.customer_id} / {customer.meter_number}"
            )
        finally:
            conn.close()

    def get_all_customers(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT customer_id, name, address, phone, meter_number, "
                     "customer_type FROM customers ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_customer(self, customer_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT customer_id, name, address, phone, meter_number, "
                     "customer_type FROM customers WHERE customer_id = ?",
                     (customer_id,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            raise CustomerNotFoundError(f"No customer with ID {customer_id}")
        return row

    def search_customers(self, keyword):
        conn = self._get_connection()
        cur = conn.cursor()
        like = f"%{keyword}%"
        cur.execute(
            "SELECT customer_id, name, address, phone, meter_number, "
            "customer_type FROM customers WHERE customer_id LIKE ? "
            "OR name LIKE ? OR meter_number LIKE ?",
            (like, like, like),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------------- METER READINGS ----------------
    def get_last_reading(self, customer_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT current_reading FROM meter_readings WHERE customer_id = ? "
            "ORDER BY reading_id DESC LIMIT 1", (customer_id,)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0.0

    def add_meter_reading(self, customer_id, previous_reading, current_reading, reading_date):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO meter_readings (customer_id, previous_reading, "
            "current_reading, reading_date) VALUES (?, ?, ?, ?)",
            (customer_id, previous_reading, current_reading, reading_date),
        )
        conn.commit()
        reading_id = cur.lastrowid
        conn.close()
        return reading_id

    def get_readings_for_customer(self, customer_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT reading_id, previous_reading, current_reading, reading_date "
            "FROM meter_readings WHERE customer_id = ? ORDER BY reading_id DESC",
            (customer_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------------- BILLS ----------------
    def add_bill(self, customer_id, reading_id, amount, bill_date):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO bills (customer_id, reading_id, amount, bill_date, status) "
            "VALUES (?, ?, ?, ?, 'Unpaid')",
            (customer_id, reading_id, amount, bill_date),
        )
        conn.commit()
        bill_id = cur.lastrowid
        conn.close()
        return bill_id

    def get_all_bills(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT b.bill_id, b.customer_id, c.name, b.amount, b.bill_date, b.status "
            "FROM bills b JOIN customers c ON b.customer_id = c.customer_id "
            "ORDER BY b.bill_id DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_bill(self, bill_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT bill_id, customer_id, reading_id, amount, bill_date, "
                     "status FROM bills WHERE bill_id = ?", (bill_id,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            raise BillNotFoundError(f"No bill with ID {bill_id}")
        return row

    def mark_bill_paid(self, bill_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE bills SET status = 'Paid' WHERE bill_id = ?", (bill_id,))
        conn.commit()
        conn.close()

    # ---------------- PAYMENTS ----------------
    def add_payment(self, bill_id, amount_paid, payment_date, method):
        bill_id_int, customer_id, reading_id, amount, bill_date, status = self.get_bill(bill_id)
        if status == "Paid":
            raise PaymentError("This bill has already been paid.")
        if amount_paid < amount:
            raise PaymentError(
                f"Partial payments are not supported yet. Bill amount is "
                f"NGN {amount:.2f}, but NGN {amount_paid:.2f} was entered."
            )
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO payments (bill_id, amount_paid, payment_date, method) "
            "VALUES (?, ?, ?, ?)",
            (bill_id, amount_paid, payment_date, method),
        )
        conn.commit()
        payment_id = cur.lastrowid
        conn.close()
        self.mark_bill_paid(bill_id)
        return payment_id

    def get_all_payments(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT p.payment_id, p.bill_id, c.name, p.amount_paid, "
            "p.payment_date, p.method FROM payments p "
            "JOIN bills b ON p.bill_id = b.bill_id "
            "JOIN customers c ON b.customer_id = c.customer_id "
            "ORDER BY p.payment_id DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------------- REPORTS ----------------
    def monthly_consumption_report(self, year_month: str):
        """year_month like '2026-07'."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT c.customer_id, c.name, SUM(m.current_reading - m.previous_reading) "
            "AS total_units FROM meter_readings m "
            "JOIN customers c ON m.customer_id = c.customer_id "
            "WHERE m.reading_date LIKE ? "
            "GROUP BY c.customer_id ORDER BY total_units DESC",
            (f"{year_month}%",),
        )
        rows = cur.fetchall()
        conn.close()
        return rows
