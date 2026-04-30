"""Driver contribution endpoints — fuel prices, reviews, reports, photos."""
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError

from . import stops_api_bp
from ..extensions import db, limiter
from ..middleware import site_required
from ..models.user import User
from ..models.truck_stop import TruckStop
from ..models.fuel_price import FuelPrice
from ..models.truck_stop_review import TruckStopReview
from ..models.truck_stop_report import TruckStopReport
from ..models.stop_photo import StopPhoto
from ..stops.helpers import stop_canonical_url

logger = logging.getLogger(__name__)

ALLOWED_FUEL_TYPES = ('diesel', 'gas', 'def', 'cng', 'lng', 'biodiesel')
ALLOWED_REPORT_TYPES = ('parking_availability', 'fuel_price_correction', 'amenity_update',
                        'closure', 'hazard', 'hours_change', 'other')
ALLOWED_IMAGE_TYPES = ('image/jpeg', 'image/png', 'image/webp')
# Pillow's lowercase format names — used to verify magic bytes match content_type.
_PIL_FORMAT_TO_MIME = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'WEBP': 'image/webp',
}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_PHOTOS_PER_USER_PER_STOP = 5


def _verify_image_bytes(image_data, claimed_content_type):
    """Verify that image_data is actually an image of an allowed type.

    Returns the canonical MIME type derived from magic bytes. Raises ValueError
    on any mismatch, unrecognized format, or Pillow failure. This blocks:
      - non-image payloads with a forged Content-Type (e.g. HTML/SVG with
        Content-Type: image/jpeg)
      - SVG (not in the allow-list and prone to embedded JS)
      - corrupt/truncated images Pillow can't decode
    """
    from io import BytesIO
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise ValueError('Image verification unavailable') from exc
    try:
        with Image.open(BytesIO(image_data)) as img:
            img.verify()
        # verify() consumes the file; reopen for format access
        with Image.open(BytesIO(image_data)) as img:
            fmt = (img.format or '').upper()
    except (UnidentifiedImageError, Exception) as exc:
        raise ValueError(f'Not a valid image: {exc}') from exc
    real_mime = _PIL_FORMAT_TO_MIME.get(fmt)
    if not real_mime:
        raise ValueError(f'Unsupported image format: {fmt}')
    if claimed_content_type and claimed_content_type != real_mime:
        # Permit common JPEG content-type aliases
        aliases = {'image/jpg': 'image/jpeg', 'image/pjpeg': 'image/jpeg'}
        if aliases.get(claimed_content_type) != real_mime:
            raise ValueError('Content-Type does not match image bytes')
    return real_mime


AUTO_VERIFY_DRIFT_PCT = 0.08  # 8% — typical day-to-day fuel-price move
AUTO_VERIFY_USER_COOLDOWN_HOURS = 24

# Reviews can reference photo URLs (legacy field). To prevent third-party
# resource leaks (viewer IP fingerprinting, malicious payload hosting, link
# rot), we require URLs to live on a configured allowlist of hosts. Configured
# via PHOTO_URL_ALLOWED_HOSTS (comma-separated). Drivers should normally use
# the /photos upload endpoint (DB-stored) instead.
def _photo_url_allowed_hosts():
    raw = (current_app.config.get('PHOTO_URL_ALLOWED_HOSTS') or '').strip()
    if not raw:
        return ()
    return tuple(h.strip().lower() for h in raw.split(',') if h.strip())


def _sanitize_photo_urls(urls):
    """Filter incoming photo URL list to https + known-safe hosts only.

    With no allowlist configured, drops all URLs — drivers must use the
    DB-backed photo upload endpoint instead. Returns up to 20 entries,
    each <= 500 chars.
    """
    allowed = _photo_url_allowed_hosts()
    out = []
    for raw in urls[:20]:
        if not isinstance(raw, str):
            continue
        s = raw[:500]
        try:
            parsed = urlparse(s)
        except ValueError:
            continue
        if parsed.scheme != 'https':
            continue
        host = (parsed.netloc or '').lower().split(':', 1)[0]
        if not host:
            continue
        if not allowed:
            continue  # no allowlist → reject all external URLs
        # Match exact or subdomain
        if not any(host == a or host.endswith('.' + a) for a in allowed):
            continue
        out.append(s)
    return out


def _should_auto_verify_price(truck_stop_id, fuel_type, price_cents,
                              reporter_user_id=None):
    """Decide whether a driver-submitted fuel price gets auto-verified.

    Hardened against drift poisoning:
      - Require an existing verified anchor.
      - Tight 8% drift band (was 20% — 20% allows two-step ~44% walks).
      - Anchor must come from a *different* user, so a single bad actor
        cannot self-confirm by submitting twice.
      - Same user cannot drive a verified price for the same (stop, fuel)
        more than once per 24h window.
    """
    last = FuelPrice.query.filter_by(
        truck_stop_id=truck_stop_id, fuel_type=fuel_type, is_verified=True
    ).order_by(FuelPrice.created_at.desc()).first()
    if not last:
        return False
    if reporter_user_id is not None and last.reported_by == reporter_user_id:
        return False  # same-user self-confirmation
    threshold = last.price_cents * AUTO_VERIFY_DRIFT_PCT
    if abs(price_cents - last.price_cents) > threshold:
        return False
    if reporter_user_id is not None:
        cooldown_start = datetime.now(timezone.utc) - timedelta(hours=AUTO_VERIFY_USER_COOLDOWN_HOURS)
        prior_by_user = FuelPrice.query.filter(
            FuelPrice.truck_stop_id == truck_stop_id,
            FuelPrice.fuel_type == fuel_type,
            FuelPrice.reported_by == reporter_user_id,
            FuelPrice.is_verified == True,  # noqa: E712
            FuelPrice.created_at >= cooldown_start,
        ).first()
        if prior_by_user is not None:
            return False
    return True


@stops_api_bp.route('/truck-stops/<int:stop_id>/fuel-prices', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def submit_fuel_price(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json() or {}
    fuel_type = data.get('fuel_type')
    price_cents = data.get('price_cents')
    currency = data.get('currency', 'USD')
    if not fuel_type or price_cents is None:
        return jsonify({'error': 'fuel_type and price_cents required'}), 400
    if fuel_type not in ALLOWED_FUEL_TYPES:
        return jsonify({'error': f'fuel_type must be one of: {", ".join(ALLOWED_FUEL_TYPES)}'}), 400
    try:
        price_cents = int(price_cents)
    except (ValueError, TypeError):
        return jsonify({'error': 'price_cents must be a number'}), 400
    if price_cents < 1 or price_cents > 99999:
        return jsonify({'error': 'price_cents must be between 1 and 99999'}), 400
    is_verified = _should_auto_verify_price(
        stop_id, fuel_type, price_cents,
        reporter_user_id=current_user.id,
    )
    fp = FuelPrice(
        truck_stop_id=stop_id, fuel_type=fuel_type,
        price_cents=price_cents, currency=currency,
        reported_by=current_user.id, source='driver',
        is_verified=is_verified,
    )
    db.session.add(fp)
    db.session.commit()
    # Award points for fuel price contribution (atomic to prevent race conditions)
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 5
        )
    )
    db.session.commit()
    if is_verified:
        from ..tasks.indexnow_task import enqueue_indexnow
        enqueue_indexnow('stops.truckerpro.net', [stop_canonical_url(stop)])
    return jsonify({'id': fp.id, 'is_verified': fp.is_verified}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reviews', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("5/minute")
def submit_review(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json() or {}
    rating = data.get('rating')
    review_text = data.get('review_text', '')
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({'error': 'rating must be a number'}), 400
    if rating < 1 or rating > 5:
        return jsonify({'error': 'rating must be 1-5'}), 400
    review_text = str(review_text)[:2000]
    existing = TruckStopReview.query.filter_by(
        truck_stop_id=stop_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({'error': 'You already reviewed this stop'}), 409
    photos = data.get('photos', [])
    if not isinstance(photos, list):
        photos = []
    photos = _sanitize_photo_urls(photos)
    review = TruckStopReview(
        truck_stop_id=stop_id, user_id=current_user.id,
        rating=rating, review_text=review_text,
        photos=photos,
    )
    db.session.add(review)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        # Only the unique-review constraint should surface as a 409 to the
        # user. Any other constraint violation (FK to truck_stop, rating
        # CHECK, etc.) is a different bug; return 400 with a generic message
        # and log so we don't lie to the user about why the request failed.
        msg = str(getattr(exc, 'orig', exc))
        if 'uq_ts_review_user_stop' in msg or 'truck_stop_id, user_id' in msg:
            return jsonify({'error': 'You already reviewed this stop'}), 409
        logger.warning('Unexpected IntegrityError on submit_review: %s', msg[:200])
        return jsonify({'error': 'Could not save review'}), 400
    # Award points for review contribution (atomic to prevent race conditions)
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 10
        )
    )
    db.session.commit()
    if review.is_approved:
        from ..tasks.indexnow_task import enqueue_indexnow
        enqueue_indexnow('stops.truckerpro.net', [stop_canonical_url(stop)])
    return jsonify({'id': review.id, 'is_approved': review.is_approved}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/reports', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def submit_report(stop_id):
    stop = TruckStop.query.get_or_404(stop_id)
    data = request.get_json() or {}
    report_type = data.get('report_type')
    report_data = data.get('data')
    if not report_type or not report_data:
        return jsonify({'error': 'report_type and data required'}), 400
    if report_type not in ALLOWED_REPORT_TYPES:
        return jsonify({'error': f'report_type must be one of: {", ".join(ALLOWED_REPORT_TYPES)}'}), 400
    expires_at = None
    if report_type == 'parking_availability':
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
    report = TruckStopReport(
        truck_stop_id=stop_id, user_id=current_user.id,
        report_type=report_type, data=report_data,
        expires_at=expires_at,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({'id': report.id}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/photos', methods=['POST'])
@site_required('stops')
@login_required
@limiter.limit("10/minute")
def upload_photo(stop_id):
    """Upload a photo for a truck stop."""
    stop = TruckStop.query.get_or_404(stop_id)

    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400

    file = request.files['photo']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return jsonify({'error': 'Only JPEG, PNG, and WebP images allowed'}), 400

    chunks = []
    total_size = 0
    while True:
        chunk = file.read(8192)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_IMAGE_SIZE:
            return jsonify({'error': 'Image must be under 2MB'}), 400
        chunks.append(chunk)
    image_data = b''.join(chunks)

    # Magic-byte verification: the client-supplied Content-Type is a hint, not
    # a fact. Decode the bytes and confirm the format matches the allow-list.
    try:
        verified_mime = _verify_image_bytes(image_data, file.content_type)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    # Check per-user limit
    existing_count = StopPhoto.query.filter_by(
        truck_stop_id=stop_id, user_id=current_user.id
    ).count()
    if existing_count >= MAX_PHOTOS_PER_USER_PER_STOP:
        return jsonify({'error': f'Maximum {MAX_PHOTOS_PER_USER_PER_STOP} photos per stop'}), 400

    caption = request.form.get('caption', '').strip()[:200]

    photo = StopPhoto(
        truck_stop_id=stop_id,
        user_id=current_user.id,
        filename=file.filename[:255],
        content_type=verified_mime,  # canonical MIME from magic bytes, not client claim
        image_data=image_data,
        caption=caption,
    )
    db.session.add(photo)

    # Award points (atomic to prevent race conditions)
    db.session.execute(
        update(User).where(User.id == current_user.id).values(
            contribution_points=db.func.coalesce(User.contribution_points, 0) + 15
        )
    )
    db.session.commit()

    return jsonify({'id': photo.id, 'points_awarded': 15}), 201


@stops_api_bp.route('/truck-stops/<int:stop_id>/photos', methods=['GET'])
@site_required('stops')
def get_stop_photos(stop_id):
    """Get list of photo metadata for a truck stop (not the image data)."""
    photos = StopPhoto.query.filter_by(
        truck_stop_id=stop_id, is_approved=True
    ).order_by(StopPhoto.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'caption': p.caption,
        'user_id': p.user_id,
        'created_at': p.created_at.isoformat() if p.created_at else None,
    } for p in photos])
