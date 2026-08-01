"""
exceptions.py
-------------
Custom exceptions for the Electricity Billing Management System.

Why custom exceptions?
In real software, we don't just want the program to crash with a generic
error. We want to know EXACTLY what went wrong (a duplicate customer? an
invalid reading? a missing record?) so the GUI can show a helpful message
instead of a scary red error screen.
"""


class BillingSystemError(Exception):
    """Base class for all errors in this application.

    Every other custom error below 'inherits' from this one. That means
    if some part of the program wants to catch ANY billing-related error,
    it can just catch BillingSystemError and it will catch all of them.
    This itself is an example of INHERITANCE.
    """
    pass


class InvalidInputError(BillingSystemError):
    """Raised when the user types something that doesn't make sense,
    e.g. leaving the name field empty, or typing letters into a number
    field."""
    pass


class DuplicateCustomerError(BillingSystemError):
    """Raised when someone tries to register a customer whose meter
    number already exists in the system."""
    pass


class CustomerNotFoundError(BillingSystemError):
    """Raised when we search for a customer that does not exist."""
    pass


class InvalidMeterReadingError(BillingSystemError):
    """Raised when a new meter reading is less than the previous one
    (a meter can only count up, never down)."""
    pass


class BillNotFoundError(BillingSystemError):
    """Raised when we try to pay or fetch a bill that does not exist."""
    pass


class PaymentError(BillingSystemError):
    """Raised when a payment amount is invalid, e.g. negative, zero,
    or more than what is owed in a way the system does not allow."""
    pass
