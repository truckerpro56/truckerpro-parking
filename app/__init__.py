from flask import Flask
from .config import Config, TestConfig
from .extensions import db, socketio, limiter, csrf, login_manager


def create_app(config_class=None):
    app = Flask(__name__)
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet',
                      message_queue=app.config.get('CELERY_BROKER_URL'))
    limiter.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'pages.login'

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from .routes import pages_bp
    app.register_blueprint(pages_bp)

    csrf.exempt(api_bp)

    with app.app_context():
        db.create_all()

    return app
