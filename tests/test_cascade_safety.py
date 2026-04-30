"""Round-4 #J: regression checks against dangerous ORM cascades.

The previous configuration cascade-deleted bookings + reviews when their
parent (Location or User) was removed. That wipes financial records and
moderation history with a single misclick. These tests pin the safe
configuration so a future PR can't silently re-add the cascade.
"""
from app.models.user import User
from app.models.location import ParkingLocation


def _cascade(rel):
    """Return the cascade rules attached to a SQLAlchemy relationship attr."""
    return rel.property.cascade


def test_user_locations_does_not_delete_orphan():
    rules = _cascade(User.locations)
    assert not rules.delete_orphan, (
        "User.locations cascade='delete-orphan' would let account removal "
        "wipe an owner's listings without an explicit archival step."
    )
    assert not rules.delete


def test_user_bookings_does_not_delete_orphan():
    rules = _cascade(User.bookings)
    assert not rules.delete_orphan
    assert not rules.delete, (
        "Bookings link to Stripe payments — they must outlive the user "
        "row so the charge has a referenceable record for refund/audit."
    )


def test_user_reviews_does_not_delete_orphan():
    rules = _cascade(User.reviews)
    assert not rules.delete_orphan
    assert not rules.delete


def test_location_bookings_does_not_delete_orphan():
    rules = _cascade(ParkingLocation.bookings)
    assert not rules.delete_orphan, (
        "Location.bookings cascade='delete-orphan' would wipe paid driver "
        "bookings when the location is removed (e.g., owner cancels listing) "
        "and orphan the matching Stripe charges."
    )
    assert not rules.delete


def test_location_reviews_does_not_delete_orphan():
    rules = _cascade(ParkingLocation.reviews)
    assert not rules.delete_orphan
    assert not rules.delete


def test_location_availability_keeps_cascade():
    """Availability slots are pure scheduling data with no off-DB side
    effects; they should still cascade with their location."""
    rules = _cascade(ParkingLocation.availability)
    assert rules.delete_orphan
