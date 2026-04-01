"""Notification Celery tasks — booking confirmations and owner alerts."""
from markupsafe import escape
from . import celery_app, get_flask_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation(self, booking_ref, driver_email, location_name, start_dt, total_display):
    """Send booking confirmation email to the driver."""
    app = get_flask_app()
    with app.app_context():
        try:
            from app.services.email_service import send_email
            html = f"""<h2>Booking Confirmed!</h2>
            <p>Your parking booking <strong>{escape(booking_ref)}</strong> at <strong>{escape(location_name)}</strong> is confirmed.</p>
            <p>Start: {escape(str(start_dt))}<br>Total: ${escape(str(total_display))} CAD</p>
            <p>&mdash; Truck Parking Club</p>"""
            send_email(driver_email, f"Booking Confirmed: {booking_ref}", html)
        except Exception as exc:
            raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_owner_booking_alert(self, owner_email, booking_ref, location_name, driver_name, start_dt):
    """Send new booking alert email to the location owner."""
    app = get_flask_app()
    with app.app_context():
        try:
            from app.services.email_service import send_email
            html = f"""<h2>New Booking!</h2>
            <p>Booking <strong>{escape(booking_ref)}</strong> at <strong>{escape(location_name)}</strong> by {escape(driver_name)}.</p>
            <p>Start: {escape(str(start_dt))}</p>
            <p>&mdash; Truck Parking Club</p>"""
            send_email(owner_email, f"New Booking: {booking_ref}", html)
        except Exception as exc:
            raise self.retry(exc=exc)
