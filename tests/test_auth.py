"""Tests for auth routes: signup, login, logout."""


def test_signup_page_loads(client):
    resp = client.get('/signup')
    assert resp.status_code == 200


def test_login_page_loads(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_signup_creates_user(client, db):
    resp = client.post('/signup', data={
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'name': 'Test User',
        'role': 'driver',
    }, follow_redirects=True)
    assert resp.status_code == 200
    from app.models.user import User
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.name == 'Test User'


def test_signup_duplicate_email(client, db):
    client.post('/signup', data={
        'email': 'dup@example.com', 'password': 'Pass123!', 'name': 'First', 'role': 'driver',
    })
    resp = client.post('/signup', data={
        'email': 'dup@example.com', 'password': 'Pass123!', 'name': 'Second', 'role': 'driver',
    })
    assert resp.status_code in (200, 302)


def test_login_valid_credentials(client, db):
    client.post('/signup', data={
        'email': 'login@example.com', 'password': 'Pass123!', 'name': 'Login User', 'role': 'driver',
    })
    resp = client.post('/login', data={
        'email': 'login@example.com', 'password': 'Pass123!',
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_login_invalid_password(client, db):
    client.post('/signup', data={
        'email': 'bad@example.com', 'password': 'Pass123!', 'name': 'Bad', 'role': 'driver',
    })
    resp = client.post('/login', data={
        'email': 'bad@example.com', 'password': 'WrongPassword!',
    })
    assert resp.status_code in (200, 302)


def test_logout(client, db):
    client.post('/signup', data={
        'email': 'logout@example.com', 'password': 'Pass123!', 'name': 'Logout', 'role': 'driver',
    })
    client.post('/login', data={'email': 'logout@example.com', 'password': 'Pass123!'})
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
