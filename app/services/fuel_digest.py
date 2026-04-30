"""Weekly fuel price digest — builds and sends email with cheapest diesel by state."""
import logging
from datetime import datetime, timezone, timedelta
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func

from ..extensions import db
from ..models.user import User
from ..models.fuel_price import FuelPrice
from ..models.truck_stop import TruckStop

logger = logging.getLogger(__name__)

# Salt for the unsubscribe-link signed token. Tokens carry user_id (not email),
# so a leaked URL only unsubscribes that one user, never enumerates the table.
UNSUBSCRIBE_SALT = 'fuel-digest-unsubscribe-v1'
UNSUBSCRIBE_TOKEN_MAX_AGE_S = 60 * 60 * 24 * 90  # 90 days


def _unsubscribe_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=UNSUBSCRIBE_SALT)


def make_unsubscribe_token(user_id):
    """Issue a signed token embedded in fuel-digest unsubscribe links."""
    return _unsubscribe_serializer().dumps({'uid': int(user_id)})


def parse_unsubscribe_token(token, max_age_seconds=UNSUBSCRIBE_TOKEN_MAX_AGE_S):
    """Validate a token and return the embedded user_id, or None if invalid/expired."""
    if not token:
        return None
    try:
        data = _unsubscribe_serializer().loads(token, max_age=max_age_seconds)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    uid = data.get('uid')
    return int(uid) if isinstance(uid, int) else None


def get_cheapest_diesel_by_state(days=7, limit_per_state=3):
    """Get cheapest diesel prices per state from the last N days.
    Returns dict: {state_code: [{stop_name, city, price_cents, brand}, ...]}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Subquery: latest diesel price per truck stop
    results = db.session.query(
        TruckStop.state_province,
        TruckStop.name,
        TruckStop.city,
        TruckStop.brand_display_name,
        FuelPrice.price_cents,
        FuelPrice.created_at,
    ).join(TruckStop, FuelPrice.truck_stop_id == TruckStop.id
    ).filter(
        FuelPrice.fuel_type == 'diesel',
        FuelPrice.created_at >= cutoff,
        TruckStop.is_active == True,
    ).order_by(
        TruckStop.state_province, FuelPrice.price_cents
    ).all()

    by_state = {}
    for state, name, city, brand, price, created in results:
        if state not in by_state:
            by_state[state] = []
        if len(by_state[state]) < limit_per_state:
            by_state[state].append({
                'stop_name': name,
                'city': city,
                'brand': brand or '',
                'price_cents': price,
                'price_display': f"${price / 100:.3f}",
                'reported': created.strftime('%b %d') if created else '',
            })

    return by_state


def build_digest_html(prices_by_state, unsubscribe_url=''):
    """Build styled HTML email for the weekly fuel digest."""
    rows = ''
    for state in sorted(prices_by_state.keys()):
        prices = prices_by_state[state]
        rows += f'<tr><td colspan="4" style="padding:12px 0 4px;font-weight:700;font-size:14px;color:#0f172a;border-bottom:1px solid #e2e8f0">{state}</td></tr>'
        for p in prices:
            rows += (
                f'<tr>'
                f'<td style="padding:6px 0;font-size:13px;color:#334155">{p["stop_name"]}</td>'
                f'<td style="padding:6px 0;font-size:13px;color:#64748b">{p["city"]}</td>'
                f'<td style="padding:6px 0;font-size:16px;font-weight:800;color:#2563eb">{p["price_display"]}</td>'
                f'<td style="padding:6px 0;font-size:11px;color:#94a3b8">{p["reported"]}</td>'
                f'</tr>'
            )

    state_count = len(prices_by_state)
    total_prices = sum(len(v) for v in prices_by_state.values())
    date_str = datetime.now(timezone.utc).strftime('%B %d, %Y')

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<div style="max-width:600px;margin:0 auto;padding:24px 16px">

<div style="background:linear-gradient(135deg,#0f2440,#1e3a5f);border-radius:12px;padding:32px;text-align:center;margin-bottom:24px">
    <div style="font-size:24px;font-weight:800;color:#fff;margin-bottom:4px">&#9981; Weekly Fuel Report</div>
    <div style="font-size:14px;color:#94a3b8">{date_str} &mdash; {total_prices} prices across {state_count} states</div>
</div>

<div style="background:#fff;border-radius:12px;border:1px solid #e2e8f0;padding:24px;margin-bottom:24px">
    <div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:16px">Cheapest Diesel This Week</div>
    <table style="width:100%;border-collapse:collapse">
        <thead>
            <tr style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px">
                <th style="text-align:left;padding:0 0 8px">Stop</th>
                <th style="text-align:left;padding:0 0 8px">City</th>
                <th style="text-align:left;padding:0 0 8px">Price</th>
                <th style="text-align:left;padding:0 0 8px">Date</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
</div>

<div style="background:#fff;border-radius:12px;border:1px solid #e2e8f0;padding:24px;text-align:center;margin-bottom:24px">
    <div style="font-size:14px;font-weight:700;color:#0f172a;margin-bottom:8px">Help other drivers &mdash; report fuel prices!</div>
    <a href="https://stops.truckerpro.net" style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none">Submit a Price</a>
</div>

<div style="background:#0f2440;border-radius:12px;padding:24px;text-align:center;margin-bottom:16px">
    <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:4px">Manage your fleet with TruckerPro TMS</div>
    <div style="font-size:12px;color:#94a3b8;margin-bottom:12px">Dispatch, ELD, compliance, invoicing &mdash; all in one</div>
    <a href="https://www.truckerpro.ca/signup" style="display:inline-block;background:#2563eb;color:#fff;padding:8px 20px;border-radius:6px;font-size:13px;font-weight:600;text-decoration:none">Try Free</a>
</div>

<div style="text-align:center;font-size:11px;color:#94a3b8;padding:8px 0">
    <a href="https://stops.truckerpro.net" style="color:#2563eb">Truck Stops Directory</a> &middot;
    <a href="https://parking.truckerpro.ca" style="color:#2563eb">Truck Parking</a> &middot;
    <a href="https://border.truckerpro.ca" style="color:#2563eb">Border Clearing</a>
    <br><br>
    <a href="{unsubscribe_url}" style="color:#94a3b8">Unsubscribe from fuel price emails</a>
</div>

</div>
</body>
</html>'''
    return html


def send_fuel_digest(user, html):
    """Send fuel digest email to a user via Resend."""
    api_key = current_app.config.get('RESEND_API_KEY')
    if not api_key:
        return False
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            'from': 'Truck Stops Directory <noreply@truckerpro.ca>',
            'to': [user.email],
            'subject': 'Weekly Fuel Prices \u2014 Cheapest Diesel This Week',
            'html': html,
        })
        return True
    except Exception as e:
        logger.error("Failed to send fuel digest to %s: %s", user.email, str(e)[:200])
        return False
