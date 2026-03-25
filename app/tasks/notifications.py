"""Notification Celery tasks — booking confirmations and owner alerts."""
from markupsafe import escape
from . import celery_app


@celery_app.task
def send_booking_confirmation(booking_ref, driver_email, location_name, start_dt, total_display):
    """Send booking confirmation email to the driver."""
    from app import create_app
    from app.services.email_service import send_email
    app = create_app()
    with app.app_context():
        html = f"""<h2>Booking Confirmed!</h2>
        <p>Your parking booking <strong>{escape(booking_ref)}</strong> at <strong>{escape(location_name)}</strong> is confirmed.</p>
        <p>Start: {escape(str(start_dt))}<br>Total: ${escape(str(total_display))} CAD</p>
        <p>&mdash; Truck Parking Club</p>"""
        send_email(driver_email, f"Booking Confirmed: {booking_ref}", html)


@celery_app.task
def send_owner_booking_alert(owner_email, booking_ref, location_name, driver_name, start_dt):
    """Send new booking alert email to the location owner."""
    from app import create_app
    from app.services.email_service import send_email
    app = create_app()
    with app.app_context():
        html = f"""<h2>New Booking!</h2>
        <p>Booking <strong>{escape(booking_ref)}</strong> at <strong>{escape(location_name)}</strong> by {escape(driver_name)}.</p>
        <p>Start: {escape(str(start_dt))}</p>
        <p>&mdash; Truck Parking Club</p>"""
        send_email(owner_email, f"New Booking: {booking_ref}", html)
