"""Tests for weigh station directory."""
import pytest
from app.models.weigh_station import WeighStation


def _create_weigh_station(db_session, **overrides):
    defaults = dict(
        name='Weigh Station WIM001', slug='weigh-station-wim001-tx',
        station_id='WIM001', highway='I-35', state_province='TX', country='US',
        latitude=30.25, longitude=-97.75, data_source='bts',
        annual_truck_count=125000, days_active=365,
        is_permanent=True, station_type='weigh_station', is_active=True,
    )
    defaults.update(overrides)
    ws = WeighStation(**defaults)
    db_session.session.add(ws)
    db_session.session.commit()
    return ws


class TestWeighStationModel:
    def test_create(self, db):
        ws = _create_weigh_station(db)
        assert ws.id is not None
        assert ws.name == 'Weigh Station WIM001'
        assert ws.station_id == 'WIM001'
        assert ws.annual_truck_count == 125000

    def test_defaults(self, db):
        ws = _create_weigh_station(db)
        assert ws.is_permanent is True
        assert ws.has_bypass is False
        assert ws.station_type == 'weigh_station'
        assert ws.country == 'US'


class TestWeighStationRoutes:
    def test_index_returns_200(self, stops_client, db):
        _create_weigh_station(db)
        resp = stops_client.get('/weigh-stations')
        assert resp.status_code == 200
        assert b'Weigh Stations' in resp.data

    def test_index_shows_state(self, stops_client, db):
        _create_weigh_station(db)
        resp = stops_client.get('/weigh-stations')
        assert resp.status_code == 200
        assert b'texas' in resp.data.lower() or b'Texas' in resp.data

    def test_state_page_returns_200(self, stops_client, db):
        _create_weigh_station(db)
        resp = stops_client.get('/weigh-stations/texas')
        assert resp.status_code == 200
        assert b'Weigh Station' in resp.data

    def test_state_page_shows_station(self, stops_client, db):
        ws = _create_weigh_station(db)
        resp = stops_client.get('/weigh-stations/texas')
        assert resp.status_code == 200
        assert ws.name.encode() in resp.data

    def test_detail_returns_200(self, stops_client, db):
        ws = _create_weigh_station(db)
        resp = stops_client.get(f'/weigh-stations/texas/{ws.slug}')
        assert resp.status_code == 200
        assert ws.name.encode() in resp.data

    def test_detail_shows_station_id(self, stops_client, db):
        ws = _create_weigh_station(db)
        resp = stops_client.get(f'/weigh-stations/texas/{ws.slug}')
        assert resp.status_code == 200
        assert b'WIM001' in resp.data

    def test_nonexistent_detail_returns_404(self, stops_client):
        resp = stops_client.get('/weigh-stations/texas/nonexistent-station')
        assert resp.status_code == 404

    def test_nonexistent_state_returns_404(self, stops_client):
        resp = stops_client.get('/weigh-stations/not-a-real-state')
        assert resp.status_code == 404

    def test_sitemap_returns_200(self, stops_client, db):
        _create_weigh_station(db)
        resp = stops_client.get('/sitemap-weigh-stations.xml')
        assert resp.status_code == 200
        assert b'weigh-stations' in resp.data


class TestWeighStationImporter:
    def test_parse_bts_feature(self):
        from app.import_stops.weigh_stations_bts import parse_bts_feature
        feature = {
            'properties': {
                'station_id': 'WIM001',
                'state': 'TX',
                'functional_class': '1',
                'Counts_Year': 125000,
                'Num_Days_Active': 365,
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [-97.75, 30.25],
            },
        }
        result = parse_bts_feature(feature)
        assert result['station_id'] == 'WIM001'
        assert result['state_province'] == 'TX'
        assert result['latitude'] == 30.25
        assert result['longitude'] == -97.75
        assert result['annual_truck_count'] == 125000
        assert result['days_active'] == 365
        assert result['functional_class'] == '1'
        assert result['data_source'] == 'bts'
        assert result['country'] == 'US'

    def test_parse_bts_feature_fips_fallback(self):
        from app.import_stops.weigh_stations_bts import parse_bts_feature
        feature = {
            'properties': {
                'station_id': 'WIM002',
                'state': '',
                'State_FIPS': 48,  # Texas
                'Counts_Year': 0,
                'Num_Days_Active': 0,
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [-97.0, 31.0],
            },
        }
        result = parse_bts_feature(feature)
        assert result['state_province'] == 'TX'
        assert result['annual_truck_count'] is None
        assert result['days_active'] is None

    def test_parse_bts_feature_no_station_id(self):
        from app.import_stops.weigh_stations_bts import parse_bts_feature
        feature = {
            'properties': {
                'station_id': '',
                'state': 'CA',
                'Counts_Year': None,
                'Num_Days_Active': None,
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [-119.0, 36.0],
            },
        }
        result = parse_bts_feature(feature)
        assert 'CA' in result['name']
        assert result['station_id'] is None
        assert result['annual_truck_count'] is None
