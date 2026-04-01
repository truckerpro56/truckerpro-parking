"""Owner dashboard routes — stats, listings, recent bookings."""
from datetime import datetime, timezone
from flask import render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from . import pages_bp
from ..extensions import db
from ..models.location import ParkingLocation
from ..models.booking import ParkingBooking
from ..models.review import ParkingReview
from ..services.geo_service import format_price


@pages_bp.route('/owner/dashboard')
@login_required
def owner_dashboard():
    """Property owner dashboard with locations, stats, and recent bookings."""
    if current_user.role not in ('owner', 'admin'):
        abort(403)
    # Get owner's locations
    locations = ParkingLocation.query.filter_by(
        owner_id=current_user.id,
    ).order_by(ParkingLocation.name).all()

    location_ids = [loc.id for loc in locations]

    stats = {'total_bookings': 0, 'revenue_month': 0, 'revenue_month_display': '0.00', 'avg_rating': 0}
    recent_bookings = []

    if location_ids:
        # Total bookings
        total_bookings = db.session.query(
            func.count(ParkingBooking.id),
        ).filter(
            ParkingBooking.location_id.in_(location_ids),
        ).scalar() or 0
        stats['total_bookings'] = total_bookings

        # Monthly revenue (current month only)
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_month = db.session.query(
            func.coalesce(func.sum(ParkingBooking.total_amount), 0),
        ).filter(
            ParkingBooking.location_id.in_(location_ids),
            ParkingBooking.created_at >= month_start,
        ).scalar() or 0
        stats['revenue_month'] = revenue_month
        stats['revenue_month_display'] = format_price(revenue_month)

        # Average rating
        avg_rating = db.session.query(
            func.coalesce(func.avg(ParkingReview.rating), 0),
        ).filter(
            ParkingReview.location_id.in_(location_ids),
        ).scalar()
        stats['avg_rating'] = round(float(avg_rating or 0), 1)

        # Recent bookings (last 10)
        booking_rows = db.session.query(
            ParkingBooking, ParkingLocation.name,
        ).join(
            ParkingLocation, ParkingBooking.location_id == ParkingLocation.id,
        ).filter(
            ParkingBooking.location_id.in_(location_ids),
        ).order_by(
            ParkingBooking.created_at.desc(),
        ).limit(10).all()

        for booking, loc_name in booking_rows:
            driver = booking.driver
            recent_bookings.append({
                'ref': booking.booking_ref,
                'start': booking.start_datetime,
                'end': booking.end_datetime,
                'total_display': format_price(booking.total_amount),
                'status': booking.status,
                'location': loc_name,
                'driver': driver.name if driver else 'Driver',
            })

    owner_locations = []
    for loc in locations:
        owner_locations.append({
            'id': loc.id,
            'name': loc.name,
            'slug': loc.slug,
            'city': loc.city,
            'province': loc.province,
            'total_spots': loc.total_spots,
            'is_active': loc.is_active,
            'is_verified': loc.is_verified,
        })

    return render_template('owner/dashboard.html',
        locations=owner_locations,
        stats=stats,
        recent_bookings=recent_bookings,
    )
