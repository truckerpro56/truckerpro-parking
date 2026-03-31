import click
from flask import Flask
from .config import Config, TestConfig
from .extensions import db, socketio, limiter, csrf, login_manager
from .middleware import init_host_routing


def create_app(config_class=None):
    app = Flask(__name__)
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    if app.config.get('TESTING'):
        socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')
    else:
        socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet',
                          message_queue=app.config.get('CELERY_BROKER_URL'))
    limiter.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'pages.login'

    init_host_routing(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from .routes import pages_bp
    app.register_blueprint(pages_bp)

    from .stops_api import stops_api_bp
    app.register_blueprint(stops_api_bp, url_prefix='/api/v1')
    csrf.exempt(stops_api_bp)

    from .stops import stops_public_bp
    app.register_blueprint(stops_public_bp)

    csrf.exempt(api_bp)

    with app.app_context():
        db.create_all()

    @app.cli.command('seed')
    def seed_command():
        """Seed the database with initial data."""
        from .seed.locations import seed_locations
        seed_locations()
        print('Seeded.')

    @app.cli.command('import-stops')
    @click.argument('brand')
    @click.option('--file', 'file_path', required=True, help='Path to CSV file')
    def import_stops_command(brand, file_path):
        """Import truck stops from a CSV file."""
        import csv
        from .import_stops.base import upsert_truck_stop, generate_stop_slug

        brand_parsers = {
            'loves': 'app.import_stops.loves:parse_loves_row',
        }
        parser_path = brand_parsers.get(brand)
        if not parser_path:
            print(f"Unknown brand: {brand}. Available: {', '.join(brand_parsers.keys())}")
            return

        module_path, func_name = parser_path.rsplit(':', 1)
        import importlib
        mod = importlib.import_module(module_path)
        parse_row = getattr(mod, func_name)

        count = 0
        with open(file_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data = parse_row(row)
                if not data.get('latitude') or not data.get('longitude'):
                    print(f"Skipping {data.get('store_number', '?')} — no coordinates")
                    continue
                data['slug'] = generate_stop_slug(
                    data['brand'], data.get('store_number', ''),
                    data['city'], data['state_province'],
                )
                upsert_truck_stop(data)
                count += 1
            db.session.commit()
        print(f"Imported {count} {brand} stops.")

    @app.cli.command('compute-border-distances')
    def compute_border_distances_command():
        """Recompute border distances for all truck stops."""
        from .models.truck_stop import TruckStop
        from .services.border_crossings import compute_border_distance
        stops = TruckStop.query.all()
        for stop in stops:
            compute_border_distance(stop)
        db.session.commit()
        print(f"Updated border distances for {len(stops)} stops.")

    return app
