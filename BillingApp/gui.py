"""
gui.py
------
The Graphical User Interface (GUI): everything the user sees and clicks.
Built with Tkinter, which comes built into Python (no extra install).

BEGINNER NOTE: A GUI app usually has ONE main window, and inside it,
"tabs" or "frames" for each feature. We use a ttk.Notebook, which is
just Tkinter's name for a tabbed panel (like tabs in a web browser).

This file demonstrates: modular programming (GUI is separate from data
logic in database.py and models.py) and exception handling (every
button click that could fail is wrapped in try/except so the app never
crashes, it just shows a friendly popup message).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import DatabaseManager
from models import create_customer
from exceptions import BillingSystemError


class BillingApp(tk.Tk):
    """The main application window."""

    def __init__(self):
        super().__init__()
        self.title("Electricity Billing Management System - Group H")
        self.geometry("950x600")
        self.db = DatabaseManager()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.customer_tab = CustomerTab(notebook, self.db)
        self.reading_tab = ReadingTab(notebook, self.db)
        self.billing_tab = BillingTab(notebook, self.db)
        self.payment_tab = PaymentTab(notebook, self.db)
        self.report_tab = ReportTab(notebook, self.db)
        self.search_tab = SearchTab(notebook, self.db)

        notebook.add(self.customer_tab, text="Customer Registration")
        notebook.add(self.reading_tab, text="Meter Reading")
        notebook.add(self.billing_tab, text="Billing")
        notebook.add(self.payment_tab, text="Payments")
        notebook.add(self.report_tab, text="Monthly Report")
        notebook.add(self.search_tab, text="Search Customer")


# ---------------------------------------------------------------------
class CustomerTab(ttk.Frame):
    """Tab 1: Customer registration."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._build_form()
        self._build_table()
        self.refresh_table()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Register New Customer")
        form.pack(fill="x", padx=10, pady=10)

        labels = ["Customer ID", "Name", "Address", "Phone", "Meter Number"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(form, text=label + ":").grid(row=i // 2, column=(i % 2) * 2,
                                                     sticky="w", padx=5, pady=5)
            entry = ttk.Entry(form, width=25)
            entry.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=5, pady=5)
            self.entries[label] = entry

        ttk.Label(form, text="Customer Type:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.customer_type = ttk.Combobox(
            form, values=["Residential", "Commercial", "Industrial"],
            state="readonly", width=22
        )
        self.customer_type.current(0)
        self.customer_type.grid(row=2, column=3, padx=5, pady=5)

        ttk.Button(form, text="Register Customer",
                   command=self.register_customer).grid(row=3, column=0, columnspan=4, pady=10)

    def _build_table(self):
        table_frame = ttk.LabelFrame(self, text="All Customers")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Name", "Address", "Phone", "Meter No.", "Type")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)
        self.tree.pack(fill="both", expand=True)

    def register_customer(self):
        try:
            cid = self.entries["Customer ID"].get()
            name = self.entries["Name"].get()
            address = self.entries["Address"].get()
            phone = self.entries["Phone"].get()
            meter = self.entries["Meter Number"].get()
            ctype = self.customer_type.get()

            customer = create_customer(ctype, cid, name, address, phone, meter)
            self.db.add_customer(customer)

            messagebox.showinfo("Success", f"Customer {name} registered successfully!")
            for entry in self.entries.values():
                entry.delete(0, tk.END)
            self.refresh_table()
        except BillingSystemError as e:
            messagebox.showerror("Registration Failed", str(e))
        except Exception as e:
            messagebox.showerror("Unexpected Error", str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.db.get_all_customers():
            self.tree.insert("", tk.END, values=row)


# ---------------------------------------------------------------------
class ReadingTab(ttk.Frame):
    """Tab 2: Meter reading entry."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._build_form()
        self._build_table()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Record Meter Reading")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.customer_id_entry = ttk.Entry(form, width=20)
        self.customer_id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(form, text="Load Previous Reading",
                   command=self.load_previous).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(form, text="Previous Reading:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.previous_entry = ttk.Entry(form, width=20)
        self.previous_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Current Reading:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.current_entry = ttk.Entry(form, width=20)
        self.current_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form, text="Save Reading",
                   command=self.save_reading).grid(row=3, column=0, columnspan=3, pady=10)

    def _build_table(self):
        table_frame = ttk.LabelFrame(self, text="Readings for Loaded Customer")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("Reading ID", "Previous", "Current", "Units", "Date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)
        self.tree.pack(fill="both", expand=True)

    def load_previous(self):
        try:
            cid = self.customer_id_entry.get()
            self.db.get_customer(cid)  # validates it exists
            last = self.db.get_last_reading(cid)
            self.previous_entry.delete(0, tk.END)
            self.previous_entry.insert(0, str(last))
            self.refresh_table(cid)
        except BillingSystemError as e:
            messagebox.showerror("Error", str(e))

    def save_reading(self):
        try:
            cid = self.customer_id_entry.get()
            self.db.get_customer(cid)
            previous = float(self.previous_entry.get())
            current = float(self.current_entry.get())
            from models import MeterReading
            reading = MeterReading(None, cid, previous, current, date.today().isoformat())
            self.db.add_meter_reading(cid, reading.previous_reading,
                                       reading.current_reading, reading.reading_date)
            messagebox.showinfo("Success",
                                 f"Reading saved. Units consumed: {reading.units_consumed}")
            self.current_entry.delete(0, tk.END)
            self.refresh_table(cid)
        except ValueError:
            messagebox.showerror("Invalid Input", "Readings must be numbers.")
        except BillingSystemError as e:
            messagebox.showerror("Error", str(e))

    def refresh_table(self, cid):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for reading_id, prev, curr, rdate in self.db.get_readings_for_customer(cid):
            units = round(curr - prev, 2)
            self.tree.insert("", tk.END, values=(reading_id, prev, curr, units, rdate))


# ---------------------------------------------------------------------
class BillingTab(ttk.Frame):
    """Tab 3: Generate bills from readings, view all bills."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._build_form()
        self._build_table()
        self.refresh_table()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Generate Bill")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.customer_id_entry = ttk.Entry(form, width=20)
        self.customer_id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Reading ID:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.reading_id_entry = ttk.Entry(form, width=20)
        self.reading_id_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(form, text="Generate Bill",
                   command=self.generate_bill).grid(row=1, column=0, columnspan=4, pady=10)

    def _build_table(self):
        table_frame = ttk.LabelFrame(self, text="All Bills")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("Bill ID", "Customer ID", "Name", "Amount (NGN)", "Date", "Status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)
        self.tree.pack(fill="both", expand=True)

    def generate_bill(self):
        try:
            cid = self.customer_id_entry.get()
            reading_id = int(self.reading_id_entry.get())

            customer_row = self.db.get_customer(cid)
            customer = create_customer(customer_row[5], *customer_row[:5])

            readings = self.db.get_readings_for_customer(cid)
            match = next((r for r in readings if r[0] == reading_id), None)
            if match is None:
                messagebox.showerror("Error", "Reading ID not found for this customer.")
                return
            _, previous, current, rdate = match
            units = current - previous

            amount = customer.calculate_bill(units)
            self.db.add_bill(cid, reading_id, amount, date.today().isoformat())

            messagebox.showinfo("Bill Generated",
                                 f"Bill for {customer.name}: NGN {amount:.2f} "
                                 f"({units} units, {customer.customer_type} rate)")
            self.refresh_table()
        except ValueError:
            messagebox.showerror("Invalid Input", "Reading ID must be a number.")
        except BillingSystemError as e:
            messagebox.showerror("Error", str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.db.get_all_bills():
            bill_id, cid, name, amount, bdate, status = row
            self.tree.insert("", tk.END, values=(bill_id, cid, name, f"{amount:.2f}", bdate, status))


# ---------------------------------------------------------------------
class PaymentTab(ttk.Frame):
    """Tab 4: Record and view payments."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._build_form()
        self._build_table()
        self.refresh_table()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Record Payment")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Bill ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.bill_id_entry = ttk.Entry(form, width=20)
        self.bill_id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Amount Paid (NGN):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(form, width=20)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Method:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.method_combo = ttk.Combobox(form, values=["Cash", "Bank Transfer", "Card", "POS"],
                                          state="readonly", width=18)
        self.method_combo.current(0)
        self.method_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(form, text="Record Payment",
                   command=self.record_payment).grid(row=2, column=0, columnspan=4, pady=10)

    def _build_table(self):
        table_frame = ttk.LabelFrame(self, text="All Payments")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("Payment ID", "Bill ID", "Customer", "Amount (NGN)", "Date", "Method")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)
        self.tree.pack(fill="both", expand=True)

    def record_payment(self):
        try:
            bill_id = int(self.bill_id_entry.get())
            amount = float(self.amount_entry.get())
            method = self.method_combo.get()
            self.db.add_payment(bill_id, amount, date.today().isoformat(), method)
            messagebox.showinfo("Success", "Payment recorded and bill marked as Paid.")
            self.bill_id_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
            self.refresh_table()
        except ValueError:
            messagebox.showerror("Invalid Input", "Bill ID and amount must be numbers.")
        except BillingSystemError as e:
            messagebox.showerror("Error", str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.db.get_all_payments():
            payment_id, bill_id, name, amount, pdate, method = row
            self.tree.insert("", tk.END, values=(payment_id, bill_id, name, f"{amount:.2f}", pdate, method))


# ---------------------------------------------------------------------
class ReportTab(ttk.Frame):
    """Tab 5: Monthly consumption report."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._build_form()
        self._build_table()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Monthly Consumption Report")
        form.pack(fill="x", padx=10, pady=10)
        ttk.Label(form, text="Month (YYYY-MM):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.month_entry = ttk.Entry(form, width=15)
        self.month_entry.insert(0, date.today().strftime("%Y-%m"))
        self.month_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(form, text="Generate Report",
                   command=self.generate_report).grid(row=0, column=2, padx=10)

    def _build_table(self):
        table_frame = ttk.LabelFrame(self, text="Report")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("Customer ID", "Name", "Total Units Consumed")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        self.tree.pack(fill="both", expand=True)

    def generate_report(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        month = self.month_entry.get()
        for cid, name, total_units in self.db.monthly_consumption_report(month):
            self.tree.insert("", tk.END, values=(cid, name, total_units))


# ---------------------------------------------------------------------
class SearchTab(ttk.Frame):
    """Tab 6: Search for a customer by ID, name, or meter number."""

    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self._build_form()
        self._build_table()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Search Customer")
        form.pack(fill="x", padx=10, pady=10)
        ttk.Label(form, text="Keyword (ID, name, or meter no.):").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.keyword_entry = ttk.Entry(form, width=30)
        self.keyword_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(form, text="Search", command=self.search).grid(row=0, column=2, padx=10)

    def _build_table(self):
        table_frame = ttk.LabelFrame(self, text="Results")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("ID", "Name", "Address", "Phone", "Meter No.", "Type")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140)
        self.tree.pack(fill="both", expand=True)

    def search(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        keyword = self.keyword_entry.get()
        for row in self.db.search_customers(keyword):
            self.tree.insert("", tk.END, values=row)
