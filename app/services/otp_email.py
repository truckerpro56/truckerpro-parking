"""Send OTP verification emails via Resend."""
import logging
from flask import current_app

logger = logging.getLogger(__name__)


def send_otp_email(email, code):
    """Send OTP code via Resend. Returns True on success."""
    api_key = current_app.config.get('RESEND_API_KEY')
    if not api_key:
        logger.warning("RESEND_API_KEY not configured, OTP not sent to %s", email)
        return False
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            'from': 'Truck Stops Directory <noreply@truckerpro.ca>',
            'to': [email],
            'subject': f'Your login code: {code}',
            'html': (
                f'<div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:40px 20px">'
                f'<h2 style="color:#0f172a;margin-bottom:8px">Your Login Code</h2>'
                f'<p style="color:#64748b;margin-bottom:24px">Enter this code to sign in to Truck Stops Directory:</p>'
                f'<div style="background:#f1f5f9;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">'
                f'<span style="font-size:2.5rem;font-weight:800;letter-spacing:8px;color:#2563eb">{code}</span>'
                f'</div>'
                f'<p style="color:#94a3b8;font-size:0.85rem">This code expires in 10 minutes. If you didn\'t request this, ignore this email.</p>'
                f'<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0">'
                f'<p style="color:#94a3b8;font-size:0.75rem">Truck Stops Directory — a <a href="https://www.truckerpro.ca" style="color:#2563eb">TruckerPro</a> product</p>'
                f'</div>'
            ),
        })
        return True
    except Exception as e:
        logger.error("Failed to send OTP email to %s: %s", email, str(e)[:200])
        return False
