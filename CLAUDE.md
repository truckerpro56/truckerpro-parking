# CLAUDE.md — Truck Parking Club

## Overview
Standalone SaaS for Canadian truck parking directory and marketplace.
Extracted from truckerpro-web's /parkingclub module.
Domain: parking.truckerpro.ca

## Tech Stack
- Flask 2.3 / Python 3.11 / SQLAlchemy 2.0
- PostgreSQL 15 (Railway), Redis 7
- Stripe (payments), Google Maps (geo), Resend (email)
- Celery for background jobs
- Deployed on Railway via Docker

## Architecture
- Flask app factory in `app/__init__.py`
- Models in `app/models/` (User, ParkingLocation, ParkingBooking, ParkingReview, ParkingAvailability)
- API endpoints in `app/api/` (under /api/v1)
- Page routes in `app/routes/` (public, auth, owner)
- Business logic in `app/services/`
- Background tasks in `app/tasks/`

## Rules
- Use SQLAlchemy ORM queries, not raw SQL
- Use `current_app.config['KEY']` for config values, never hardcode
- Use `Decimal` for money display, store as integer cents in DB
- All rates stored in cents (e.g., daily_rate=2500 = $25.00)
- Canadian tax: GST/HST/PST/QST calculated via PROVINCIAL_TAX in constants.py
- Rate limit auth endpoints (login, signup)
- CSRF exempt the API blueprint only
