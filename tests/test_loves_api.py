"""Tests for Loves API importer."""
from unittest.mock import patch, MagicMock
from app.import_stops.loves_api import parse_loves_api_store, fetch_loves_stores


def test_parse_loves_api_store():
    store = {
        'number': 521,
        'latitude': 32.7767,
        'longitude': -96.7970,
        'address1': '1234 I-35 Frontage Rd',
        'city': 'Dallas',
        'state': 'TX',
        'zip': '75201',
        'highway': 'I-35',
        'exitNumber': '42',
        'phoneNumber': '(214) 555-0100',
        'name': 'Site 521',
        'facilityId': 521,
        'isHotel': False,
        'isTrillium': False,
        'isPrivate': False,
    }
    data = parse_loves_api_store(store)
    assert data['brand'] == 'loves'
    assert data['store_number'] == '521'
    assert data['city'] == 'Dallas'
    assert data['state_province'] == 'TX'
    assert data['latitude'] == 32.7767
    assert data['longitude'] == -96.7970
    assert data['highway'] == 'I-35'
    assert data['exit_number'] == '42'
    assert data['phone'] == '(214) 555-0100'
    assert data['has_diesel'] is True
    assert data['data_source'] == 'api'
    assert data['country'] == 'US'


def test_parse_loves_api_store_nulls():
    store = {
        'number': 99,
        'latitude': 40.0,
        'longitude': -80.0,
        'address1': '123 Main St',
        'city': 'Town',
        'state': 'PA',
        'zip': '15001',
        'highway': None,
        'exitNumber': None,
        'phoneNumber': None,
        'name': 'Site 99',
        'facilityId': 99,
    }
    data = parse_loves_api_store(store)
    assert data['highway'] is None
    assert data['exit_number'] is None
    assert data['phone'] is None
    assert data['store_number'] == '99'


@patch('app.import_stops.loves_api.requests.get')
def test_fetch_loves_stores_mock(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'stores': [
            {'number': 1, 'latitude': 30.0, 'longitude': -90.0,
             'address1': '1 St', 'city': 'A', 'state': 'TX', 'zip': '70000'},
            {'number': 2, 'latitude': 31.0, 'longitude': -91.0,
             'address1': '2 St', 'city': 'B', 'state': 'LA', 'zip': '70001'},
        ]
    }
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp
    stores = fetch_loves_stores()
    assert len(stores) == 2
    mock_get.assert_called_once_with('https://www.loves.com/api/fetch_stores', timeout=30)


def test_api_import_cli(app, db):
    """Test CLI import with mocked API."""
    with patch('app.import_stops.loves_api.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'stores': [
                {'number': 777, 'latitude': 30.2672, 'longitude': -97.7431,
                 'address1': '555 Test Rd', 'city': 'Austin', 'state': 'TX',
                 'zip': '78701', 'highway': 'I-35', 'exitNumber': '233',
                 'phoneNumber': '(512) 555-0100', 'name': 'Site 777',
                 'facilityId': 777},
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        runner = app.test_cli_runner()
        result = runner.invoke(args=['import-stops', 'loves', '--source', 'api'])
        assert 'Imported 1' in result.output

        from app.models.truck_stop import TruckStop
        stop = TruckStop.query.filter_by(store_number='777', brand='loves').first()
        assert stop is not None
        assert stop.city == 'Austin'
        assert stop.data_source == 'api'
