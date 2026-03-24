"""Notification Celery tasks — booking confirmations and owner alerts."""
from . import celery_app


@celery_app.task
def send_booking_confirmation(booking_ref, driver_email, location_name, start_dt, total_display):
    """Send booking confirmation email to the driver."""
    from app import create_app
    from app.services.email_service import send_email
    app = create_app()
    with app.app_context():
        html = f"""<h2>Booking Confirmed!</h2>
        <p>Your parking booking <strong>{booking_ref}</strong> at <strong>{location_name}</strong> is confirmed.</p>
        <p>Start: {start_dt}<br>Total: ${total_display} CAD</p>
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
        <p>Booking <strong>{booking_ref}</strong> at <strong>{location_name}</strong> by {driver_name}.</p>
        <p>Start: {start_dt}</p>
        <p>&mdash; Truck Parking Club</p>"""
        send_email(owner_email, f"New Booking: {booking_ref}", html)
