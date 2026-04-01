"""Transactional email via Resend."""
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def send_email(to, subject, html_body):
    """Send a transactional email using the Resend API.

    Returns True on success, False on failure or missing config.
    """
    api_key = current_app.config.get('RESEND_API_KEY')
    if not api_key:
        logger.warning("RESEND_API_KEY not set, skipping email to %s", to)
        return False
    try:
        import resend
        resend.api_key = api_key
        # Sanitize to prevent header injection
        clean_to = to.replace('\n', '').replace('\r', '').strip()
        clean_subject = subject.replace('\n', '').replace('\r', '').strip()
        resend.Emails.send({
            'from': 'Truck Parking Club <noreply@truckerpro.ca>',
            'to': [clean_to],
            'subject': clean_subject,
            'html': html_body,
        })
        return True
    except Exception as e:
        logger.error("Email send failed: %s", str(e)[:200])
        return False
