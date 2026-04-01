import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Provide a clean DB for each test by rolling back after each test."""
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Clean up all rows inserted during the test
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture(scope='function')
def stops_client(app):
    """Test client that sends Host header for stops.truckerpro.net domain."""
    app.config['STOPS_DOMAIN'] = 'stops.localhost'
    c = app.test_client()

    class StopsClient:
        """Wrapper that adds Host header to all requests."""
        def __init__(self, client):
            self._client = client

        def get(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Host'] = 'stops.localhost'
            return self._client.get(*args, **kwargs)

        def post(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Host'] = 'stops.localhost'
            return self._client.post(*args, **kwargs)

        def session_transaction(self):
            return self._client.session_transaction()

    return StopsClient(c)
