"""
models.py
---------
This file holds all the "things" (objects) our billing system deals with:
People, Customers, Meter Readings, Bills, and Payments.

BEGINNER NOTE:
Think of a "class" as a BLUEPRINT, and an "object" as a HOUSE built from
that blueprint. The blueprint (class) says "every house has a door, a
roof, and windows". Each actual house (object) you build from it has its
own specific door, roof, and windows, but they all follow the same plan.

This file demonstrates every OOP concept your rubric asks for:
  - Encapsulation      -> private attributes (self._name) + @property
  - Inheritance         -> ResidentialCustomer/CommercialCustomer/
                           IndustrialCustomer all inherit from Customer,
                           which inherits from Person
  - Polymorphism        -> each customer type has its OWN calculate_bill()
                           that behaves differently, but is called the
                           same way for all of them
  - Abstraction          -> Person and Customer are "abstract" classes:
                           you can never create a plain Person or a plain
                           Customer directly, only a specific kind
"""

from abc import ABC, abstractmethod
from datetime import date
from exceptions import InvalidInputError, InvalidMeterReadingError


# ---------------------------------------------------------------------
# ABSTRACTION + INHERITANCE (Level 1): Person
# ---------------------------------------------------------------------
class Person(ABC):
    """An abstract base class representing any human being in the system.

    'Abstract' means: you can NEVER type Person("John", ...) directly.
    It only exists so that other classes (like Customer) can inherit
    its shared features (name, address, phone). This avoids repeating
    the same code in every class that represents a person.
    """

    def __init__(self, name: str, address: str, phone: str):
        self.name = name        # goes through the @name.setter validation below
        self.address = address
        self.phone = phone

    # ---------------- ENCAPSULATION ----------------
    # We store the real value in a "private" variable (prefixed with _)
    # and only allow it to be read/changed through these controlled
    # "property" methods. This lets us validate data before accepting it,
    # instead of letting any part of the program set a blank name.
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value or not str(value).strip():
            raise InvalidInputError("Name cannot be empty.")
        self._name = str(value).strip()

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        if not value or not str(value).strip():
            raise InvalidInputError("Address cannot be empty.")
        self._address = str(value).strip()

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        if not value or not str(value).strip():
            raise InvalidInputError("Phone number cannot be empty.")
        self._phone = str(value).strip()

    @abstractmethod
    def get_details(self) -> str:
        """Every subclass MUST provide its own version of this method.
        This is enforced by Python because Person is an ABC (Abstract
        Base Class) with an @abstractmethod."""
        raise NotImplementedError


# ---------------------------------------------------------------------
# ABSTRACTION + INHERITANCE (Level 2): Customer
# ---------------------------------------------------------------------
class Customer(Person):
    """An abstract customer. A Customer IS-A Person (inheritance), plus
    it has extra billing-specific information: an ID and a meter number.

    Still abstract: you cannot create a plain Customer(). You must create
    a ResidentialCustomer, CommercialCustomer, or IndustrialCustomer.
    """

    def __init__(self, customer_id: str, name: str, address: str,
                 phone: str, meter_number: str, customer_type: str):
        super().__init__(name, address, phone)   # re-uses Person's code
        self.customer_id = customer_id
        self.meter_number = meter_number
        self._customer_type = customer_type

    @property
    def customer_id(self):
        return self._customer_id

    @customer_id.setter
    def customer_id(self, value):
        if not value:
            raise InvalidInputError("Customer ID cannot be empty.")
        self._customer_id = str(value).strip()

    @property
    def meter_number(self):
        return self._meter_number

    @meter_number.setter
    def meter_number(self, value):
        if not value:
            raise InvalidInputError("Meter number cannot be empty.")
        self._meter_number = str(value).strip()

    @property
    def customer_type(self):
        return self._customer_type

    # ---------------- POLYMORPHISM ----------------
    # Every subclass below overrides calculate_bill() with its OWN
    # pricing rules, but the rest of the program can call
    # customer.calculate_bill(units) on ANY customer object without
    # caring which exact subclass it is. That is polymorphism.
    @abstractmethod
    def calculate_bill(self, units_consumed: float) -> float:
        raise NotImplementedError

    def get_details(self) -> str:
        return (f"[{self.customer_type}] {self.customer_id} - {self.name} | "
                f"Meter: {self.meter_number} | {self.phone}")

    def __str__(self):
        return self.get_details()


class ResidentialCustomer(Customer):
    """Household customers. Cheaper rate, with a discounted rate for the
    first 50 units to keep basic household bills low."""

    LOW_RATE = 30.0     # Naira per unit for the first 50 units
    HIGH_RATE = 45.0    # Naira per unit after that

    def __init__(self, customer_id, name, address, phone, meter_number):
        super().__init__(customer_id, name, address, phone,
                          meter_number, customer_type="Residential")

    def calculate_bill(self, units_consumed: float) -> float:
        if units_consumed < 0:
            raise InvalidMeterReadingError("Units consumed cannot be negative.")
        if units_consumed <= 50:
            return round(units_consumed * self.LOW_RATE, 2)
        return round(50 * self.LOW_RATE + (units_consumed - 50) * self.HIGH_RATE, 2)


class CommercialCustomer(Customer):
    """Shops, offices, small businesses. Flat, higher rate per unit."""

    RATE_PER_UNIT = 75.0

    def __init__(self, customer_id, name, address, phone, meter_number):
        super().__init__(customer_id, name, address, phone,
                          meter_number, customer_type="Commercial")

    def calculate_bill(self, units_consumed: float) -> float:
        if units_consumed < 0:
            raise InvalidMeterReadingError("Units consumed cannot be negative.")
        return round(units_consumed * self.RATE_PER_UNIT, 2)


class IndustrialCustomer(Customer):
    """Factories / heavy users. Lower per-unit rate but a fixed monthly
    demand charge for using the heavy-duty connection."""

    RATE_PER_UNIT = 60.0
    DEMAND_CHARGE = 5000.0

    def __init__(self, customer_id, name, address, phone, meter_number):
        super().__init__(customer_id, name, address, phone,
                          meter_number, customer_type="Industrial")

    def calculate_bill(self, units_consumed: float) -> float:
        if units_consumed < 0:
            raise InvalidMeterReadingError("Units consumed cannot be negative.")
        return round(units_consumed * self.RATE_PER_UNIT + self.DEMAND_CHARGE, 2)


def create_customer(customer_type: str, customer_id, name, address, phone, meter_number):
    """A small 'factory' function: given a type as text (e.g. from the
    database or a dropdown menu), it builds the correct class of object.
    This is what lets the rest of the program stay simple - it just calls
    create_customer(...) and doesn't need a big if/else everywhere."""
    mapping = {
        "Residential": ResidentialCustomer,
        "Commercial": CommercialCustomer,
        "Industrial": IndustrialCustomer,
    }
    if customer_type not in mapping:
        raise InvalidInputError(f"Unknown customer type: {customer_type}")
    cls = mapping[customer_type]
    return cls(customer_id, name, address, phone, meter_number)


# ---------------------------------------------------------------------
# MeterReading
# ---------------------------------------------------------------------
class MeterReading:
    """Represents one meter reading event for a customer."""

    def __init__(self, reading_id, customer_id, previous_reading: float,
                 current_reading: float, reading_date: str = None):
        self.reading_id = reading_id
        self.customer_id = customer_id
        if current_reading < previous_reading:
            raise InvalidMeterReadingError(
                "Current reading cannot be less than the previous reading."
            )
        self._previous_reading = float(previous_reading)
        self._current_reading = float(current_reading)
        self.reading_date = reading_date or date.today().isoformat()

    @property
    def units_consumed(self) -> float:
        return round(self._current_reading - self._previous_reading, 2)

    @property
    def previous_reading(self):
        return self._previous_reading

    @property
    def current_reading(self):
        return self._current_reading

    def __str__(self):
        return (f"Reading#{self.reading_id} | Customer {self.customer_id} | "
                f"{self._previous_reading} -> {self._current_reading} "
                f"= {self.units_consumed} units on {self.reading_date}")


# ---------------------------------------------------------------------
# Bill
# ---------------------------------------------------------------------
class Bill:
    """Represents one generated bill for a customer's meter reading."""

    def __init__(self, bill_id, customer_id, reading_id, amount: float,
                 bill_date: str = None, status: str = "Unpaid"):
        self.bill_id = bill_id
        self.customer_id = customer_id
        self.reading_id = reading_id
        if amount < 0:
            raise InvalidInputError("Bill amount cannot be negative.")
        self.amount = round(float(amount), 2)
        self.bill_date = bill_date or date.today().isoformat()
        self.status = status  # "Paid" or "Unpaid"

    def __str__(self):
        return (f"Bill#{self.bill_id} | Customer {self.customer_id} | "
                f"NGN {self.amount:.2f} | {self.status} | {self.bill_date}")


# ---------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------
class Payment:
    """Represents a payment made by a customer against a bill."""

    def __init__(self, payment_id, bill_id, amount_paid: float,
                 payment_date: str = None, method: str = "Cash"):
        self.payment_id = payment_id
        self.bill_id = bill_id
        if amount_paid <= 0:
            raise InvalidInputError("Payment amount must be greater than zero.")
        self.amount_paid = round(float(amount_paid), 2)
        self.payment_date = payment_date or date.today().isoformat()
        self.method = method

    def __str__(self):
        return (f"Payment#{self.payment_id} | Bill {self.bill_id} | "
                f"NGN {self.amount_paid:.2f} | {self.method} | {self.payment_date}")
