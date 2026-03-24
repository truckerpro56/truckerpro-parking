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
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        options = dict(bind=connection)
        session = _db.create_scoped_session(options=options)
        _db.session = session
        yield _db
        transaction.rollback()
        connection.close()
        session.remove()
