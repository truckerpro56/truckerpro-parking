"""Notification Celery tasks — booking confirmations and owner alerts."""
import logging
from markupsafe import escape
from . import celery_app, get_flask_app

logger = logging.getLogger(__name__)


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


def enqueue_booking_notifications(booking):
    """Fire-and-forget dispatch of confirmation + owner alert for a paid booking.

    Safe to call from web request — swallows broker errors so a missing Redis
    or unavailable Celery worker never blocks the booking response.
    """
    try:
        from ..extensions import db
        from ..models.user import User
        from ..models.location import ParkingLocation
        loc = db.session.get(ParkingLocation, booking.location_id) if booking.location_id else None
        driver = db.session.get(User, booking.driver_id) if booking.driver_id else None
        owner = db.session.get(User, loc.owner_id) if (loc and loc.owner_id) else None
        start_iso = booking.start_datetime.isoformat() if booking.start_datetime else ''
        loc_name = loc.name if loc else ''
        if driver and driver.email:
            send_booking_confirmation.delay(
                booking.booking_ref,
                driver.email,
                loc_name,
                start_iso,
                f"{booking.total_amount / 100:.2f}",
            )
        if owner and owner.email:
            driver_label = (
                (driver.name if driver else None)
                or (driver.email if driver else None)
                or 'Guest'
            )
            send_owner_booking_alert.delay(
                owner.email,
                booking.booking_ref,
                loc_name,
                driver_label,
                start_iso,
            )
    except Exception as e:
        logger.warning("Booking notification dispatch failed: %s", str(e)[:200])
