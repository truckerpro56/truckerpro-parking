from decimal import Decimal


def test_calculate_tax_ontario():
    from app.services.booking_service import calculate_tax
    tax_amount, tax_type = calculate_tax(10000, 'ON')  # $100 subtotal
    assert tax_type == 'HST'
    assert tax_amount == 1300  # 13%


def test_calculate_tax_alberta():
    from app.services.booking_service import calculate_tax
    tax_amount, tax_type = calculate_tax(10000, 'AB')
    assert tax_type == 'GST'
    assert tax_amount == 500  # 5%


def test_calculate_tax_quebec():
    from app.services.booking_service import calculate_tax
    tax_amount, tax_type = calculate_tax(10000, 'QC')
    assert tax_type == 'GST+QST'
    assert tax_amount == 1498  # 14.975% rounded


def test_calculate_subtotal_daily():
    from app.services.booking_service import calculate_subtotal
    from datetime import datetime, timezone
    start = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 3, 14, 0, tzinfo=timezone.utc)
    subtotal = calculate_subtotal(2500, 'daily', start, end)  # $25/day x 2 days
    assert subtotal == 5000


def test_calculate_subtotal_hourly():
    from app.services.booking_service import calculate_subtotal
    from datetime import datetime, timezone
    start = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 4, 1, 17, 30, tzinfo=timezone.utc)
    subtotal = calculate_subtotal(500, 'hourly', start, end)  # $5/hr x 4 hrs (ceil)
    assert subtotal == 2000


def test_generate_booking_ref():
    from app.services.booking_service import generate_booking_ref
    ref = generate_booking_ref()
    assert ref.startswith('TPP-2026-')
    assert len(ref) == 17  # TPP-2026-XXXXXXXX
