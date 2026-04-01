"""Celery task for weekly fuel price digest."""
import logging
from . import celery_app, get_flask_app

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.send_weekly_fuel_digests')
def send_weekly_fuel_digests():
    """Send fuel digest emails to all subscribed users. Called by Celery Beat."""
    app = get_flask_app()
    with app.app_context():
        from ..models.user import User
        from ..services.fuel_digest import get_cheapest_diesel_by_state, build_digest_html, send_fuel_digest

        prices = get_cheapest_diesel_by_state(days=7)
        if not prices:
            logger.info("No diesel prices in the last 7 days, skipping digest")
            return

        subscribers = User.query.filter_by(fuel_email_subscribed=True, is_active=True).all()
        logger.info("Sending fuel digest to %d subscribers", len(subscribers))

        sent = 0
        for user in subscribers:
            # Filter to user's preferred states if set
            user_prices = prices
            if user.fuel_email_states:
                user_prices = {k: v for k, v in prices.items() if k in user.fuel_email_states}
            if not user_prices:
                user_prices = prices  # Fallback to all if no matches

            unsubscribe_url = f"https://stops.truckerpro.net/profile/unsubscribe-fuel?email={user.email}"
            html = build_digest_html(user_prices, unsubscribe_url)
            if send_fuel_digest(user, html):
                sent += 1

        logger.info("Fuel digest sent to %d/%d subscribers", sent, len(subscribers))
