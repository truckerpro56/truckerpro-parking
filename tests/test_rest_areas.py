"""Tests for rest area directory."""
import pytest
from app.models.rest_area import RestArea


def _create_rest_area(db_session, **overrides):
    defaults = dict(
        name='Test Rest Area', slug='test-rest-area-i-35-tx',
        highway='I-35', state_province='TX', country='US',
        latitude=32.78, longitude=-96.80, data_source='test',
        has_restrooms=True, truck_parking=True, is_active=True,
    )
    defaults.update(overrides)
    ra = RestArea(**defaults)
    db_session.session.add(ra)
    db_session.session.commit()
    return ra


class TestRestAreaModel:
    def test_create(self, db):
        ra = _create_rest_area(db)
        assert ra.id is not None
        assert ra.name == 'Test Rest Area'


class TestRestAreaRoutes:
    def test_index_returns_200(self, stops_client, db):
        _create_rest_area(db)
        resp = stops_client.get('/rest-areas')
        assert resp.status_code == 200

    def test_state_page_returns_200(self, stops_client, db):
        _create_rest_area(db)
        resp = stops_client.get('/rest-areas/texas')
        assert resp.status_code == 200

    def test_detail_returns_200(self, stops_client, db):
        ra = _create_rest_area(db)
        resp = stops_client.get(f'/rest-areas/texas/{ra.slug}')
        assert resp.status_code == 200

    def test_nonexistent_returns_404(self, stops_client):
        resp = stops_client.get('/rest-areas/texas/nonexistent')
        assert resp.status_code == 404


class TestRestAreaImporter:
    def test_parse_usdot_feature(self):
        from app.import_stops.rest_areas_usdot import parse_usdot_feature
        feature = {
            'attributes': {
                'nhs_rest_s': 'Grand Bay Welcome Center',
                'highway_ro': 'I-10 EB',
                'state': 'AL',
                'municipali': 'Grand Bay',
                'mile_post': 5.2,
                'number_of_': 50,
            },
            'geometry': {'x': -88.34, 'y': 30.47}
        }
        result = parse_usdot_feature(feature)
        assert result['name'] == 'Grand Bay Welcome Center'
        assert result['highway'] == 'I-10 EB'
        assert result['state_province'] == 'AL'
        assert result['latitude'] == 30.47
        assert result['longitude'] == -88.34
        assert result['parking_spaces'] == 50
        assert result['is_welcome_center'] is True
        assert result['direction'] == 'EB'
