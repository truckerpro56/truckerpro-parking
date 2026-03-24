"""Booking pricing, tax calculation, and availability checks."""
import math
import uuid
from datetime import datetime, timezone
from app.constants import PROVINCIAL_TAX

COMMISSION_RATE = 0.10  # 10%


def calculate_tax(subtotal_cents, province_code):
    """Calculate tax amount in cents. Returns (tax_cents, tax_type)."""
    tax_info = PROVINCIAL_TAX.get(province_code, {'rate': 0.05, 'type': 'GST'})
    tax_amount = round(subtotal_cents * tax_info['rate'])
    return tax_amount, tax_info['type']


def calculate_subtotal(rate_cents, booking_type, start_dt, end_dt):
    """Calculate subtotal in cents based on rate and duration."""
    if booking_type == 'hourly':
        hours = max(1, math.ceil((end_dt - start_dt).total_seconds() / 3600))
        return rate_cents * hours
    elif booking_type == 'daily':
        days = max(1, math.ceil((end_dt - start_dt).total_seconds() / 86400))
        return rate_cents * days
    elif booking_type == 'weekly':
        weeks = max(1, math.ceil((end_dt - start_dt).days / 7))
        return rate_cents * weeks
    else:  # monthly
        months = max(1, math.ceil((end_dt - start_dt).days / 30))
        return rate_cents * months


def calculate_commission(subtotal_cents):
    """Calculate platform commission in cents."""
    return round(subtotal_cents * COMMISSION_RATE)


def generate_booking_ref():
    """Generate unique booking reference like TPP-2026-A1B2C3D4."""
    year = datetime.now(timezone.utc).year
    suffix = uuid.uuid4().hex[:8].upper()
    return f"TPP-{year}-{suffix}"
