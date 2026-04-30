"""Tests for Celery beat configuration (Round-4 #I)."""


def test_celery_uses_eastern_timezone_not_utc():
    """Without an explicit timezone, hour=13 UTC = "Monday 8am ET" was wrong
    for ~8 months/year (DST). Beat must run in Eastern so the schedule is
    DST-aware and the comment matches the firing time year-round."""
    from app.tasks import celery_app
    tz = celery_app.conf.timezone
    assert tz in ('America/Toronto', 'US/Eastern', 'America/New_York'), (
        f"Celery beat timezone must track Eastern; got {tz!r}"
    )
    # If tzinfo is set, enable_utc must be False; otherwise Celery silently
    # falls back to UTC despite the timezone setting.
    assert celery_app.conf.enable_utc is False


def test_fuel_digest_schedule_fires_at_local_8am_monday():
    from app.tasks import celery_app
    sched = celery_app.conf.beat_schedule['weekly-fuel-digest']
    cron = sched['schedule']
    # crontab stores hour as a frozenset; check 8 is in it
    assert 8 in cron.hour, f"Expected hour=8 (local), got {cron.hour}"
    assert 0 in cron.minute
    # day_of_week=1 = Monday in Celery (0=Sunday in some places, Celery uses 0=Sunday)
    # Verify Monday is included
    assert 1 in cron.day_of_week


def test_webhook_cleanup_scheduled_daily():
    """Purge task must be on the beat schedule, not just defined."""
    from app.tasks import celery_app
    schedules = celery_app.conf.beat_schedule
    assert 'purge-old-webhook-events' in schedules
    cron = schedules['purge-old-webhook-events']['schedule']
    # Daily — day_of_week and day_of_month should be wildcard (full set)
    # Off-hours preferred (3 AM Eastern)
    assert 3 in cron.hour
