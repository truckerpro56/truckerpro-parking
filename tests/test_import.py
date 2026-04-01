"""Tests for CSV import pipeline."""
import os
import csv
import tempfile
import pytest
from app.models.truck_stop import TruckStop
from app.import_stops.base import upsert_truck_stop, generate_stop_slug
from app.import_stops.loves import parse_loves_row


def test_generate_stop_slug():
    slug = generate_stop_slug('loves', '521', 'Dallas', 'TX')
    assert slug == 'loves-521-dallas-tx'


def test_generate_stop_slug_spaces():
    slug = generate_stop_slug('pilot_flying_j', '18', 'New York', 'NY')
    assert slug == 'pilot-flying-j-18-new-york-ny'


def test_upsert_creates_new(db):
    data = {
        'brand': 'loves', 'brand_display_name': "Love's Travel Stops",
        'name': "Love's #999", 'slug': 'loves-999-test-tx',
        'store_number': '999', 'address': '123 Hwy',
        'city': 'Test', 'state_province': 'TX', 'country': 'US',
        'latitude': 32.0, 'longitude': -96.0, 'data_source': 'csv_import',
    }
    stop = upsert_truck_stop(data)
    db.session.commit()
    assert stop.id is not None
    assert TruckStop.query.filter_by(store_number='999').count() == 1


def test_upsert_updates_existing(db):
    data = {
        'brand': 'loves', 'brand_display_name': "Love's Travel Stops",
        'name': "Love's #888", 'slug': 'loves-888-test-tx',
        'store_number': '888', 'address': '123 Hwy',
        'city': 'Test', 'state_province': 'TX', 'country': 'US',
        'latitude': 32.0, 'longitude': -96.0, 'data_source': 'csv_import',
    }
    stop1 = upsert_truck_stop(data)
    db.session.commit()
    data['name'] = "Love's #888 Updated"
    data['has_showers'] = True
    stop2 = upsert_truck_stop(data)
    db.session.commit()
    assert stop1.id == stop2.id
    assert stop2.name == "Love's #888 Updated"
    assert TruckStop.query.filter_by(store_number='888', brand='loves').count() == 1


def test_parse_loves_row():
    row = {
        'Store Number': '521', 'Store Name': "Love's Travel Stop",
        'Address': '1234 I-35 Frontage Rd', 'City': 'Dallas',
        'State': 'TX', 'Zip': '75201', 'Country': 'US',
        'Latitude': '32.7767', 'Longitude': '-96.7970',
        'Phone': '(214) 555-0100', 'Has Diesel': 'Y',
        'Has Showers': 'Y', 'Number Of Showers': '8',
        'Has Scale': 'Y', 'Has Tire Care': 'Y', 'Has DEF': 'Y',
        'Truck Parking Spaces': '150',
    }
    data = parse_loves_row(row)
    assert data['brand'] == 'loves'
    assert data['store_number'] == '521'
    assert data['city'] == 'Dallas'
    assert data['latitude'] == 32.7767
    assert data['has_diesel'] is True
    assert data['has_showers'] is True
    assert data['shower_count'] == 8
    assert data['truck_spots'] == 150


class TestPilotParser:
    def test_parse_pilot_feature(self):
        from app.import_stops.pilot_api import parse_pilot_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-96.7970, 32.7767]},
            'properties': {
                'ref': '385',
                'name': 'Pilot Travel Center',
                'brand': 'Pilot',
                'addr:street_address': '123 Main St',
                'addr:city': 'Dallas',
                'addr:state': 'TX',
                'addr:postcode': '75201',
                'addr:country': 'US',
                'phone': '(214) 555-0100',
            }
        }
        result = parse_pilot_feature(feature)
        assert result['brand'] == 'pilot_flying_j'
        assert result['store_number'] == '385'
        assert result['city'] == 'Dallas'
        assert result['state_province'] == 'TX'
        assert result['latitude'] == 32.7767
        assert result['longitude'] == -96.7970
        assert result['has_diesel'] is True

    def test_parse_pilot_flying_j_brand(self):
        from app.import_stops.pilot_api import parse_pilot_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-80.0, 35.0]},
            'properties': {
                'ref': '100',
                'name': 'Flying J Travel Center',
                'brand': 'Flying J',
                'addr:city': 'Charlotte',
                'addr:state': 'NC',
            }
        }
        result = parse_pilot_feature(feature)
        assert result['brand_display_name'] == 'Flying J'

    def test_parse_pilot_one9_brand(self):
        from app.import_stops.pilot_api import parse_pilot_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-90.0, 40.0]},
            'properties': {
                'ref': '200',
                'name': 'ONE9 Fuel Network',
                'brand': 'ONE9',
                'addr:city': 'Springfield',
                'addr:state': 'IL',
            }
        }
        result = parse_pilot_feature(feature)
        assert result['brand_display_name'] == 'ONE9 by Pilot'

    def test_parse_pilot_canadian_location(self):
        from app.import_stops.pilot_api import parse_pilot_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-79.0, 43.0]},
            'properties': {
                'ref': '999',
                'name': 'Pilot Travel Center',
                'brand': 'Pilot',
                'addr:city': 'Toronto',
                'addr:state': 'ON',
                'addr:country': 'CA',
            }
        }
        result = parse_pilot_feature(feature)
        assert result['country'] == 'CA'

    def test_parse_pilot_no_name_uses_ref(self):
        from app.import_stops.pilot_api import parse_pilot_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-95.0, 30.0]},
            'properties': {
                'ref': '777',
                'brand': 'Pilot',
                'addr:city': 'Houston',
                'addr:state': 'TX',
            }
        }
        result = parse_pilot_feature(feature)
        assert '777' in result['name']


class TestTaPetroParser:
    def test_parse_ta_feature(self):
        from app.import_stops.ta_petro_api import parse_ta_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-87.6298, 41.8781]},
            'properties': {
                'ref': '019',
                'name': 'TA Chicago',
                'brand': 'TA',
                'addr:street_address': '456 Truck Rd',
                'addr:city': 'Chicago',
                'addr:state': 'IL',
                'addr:postcode': '60601',
                'fuel:diesel': 'yes',
                'fuel:adblue_at_pump': 'yes',
            }
        }
        result = parse_ta_feature(feature)
        assert result['brand'] == 'ta_petro'
        assert result['store_number'] == '019'
        assert result['city'] == 'Chicago'
        assert result['has_diesel'] is True
        assert result['has_def'] is True

    def test_parse_petro_brand(self):
        from app.import_stops.ta_petro_api import parse_ta_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-104.9, 39.7]},
            'properties': {
                'ref': '050',
                'name': 'Petro Denver',
                'brand': 'Petro',
                'addr:city': 'Denver',
                'addr:state': 'CO',
            }
        }
        result = parse_ta_feature(feature)
        assert result['brand_display_name'] == 'Petro Stopping Centers'

    def test_parse_ta_express_brand(self):
        from app.import_stops.ta_petro_api import parse_ta_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-118.0, 34.0]},
            'properties': {
                'ref': '300',
                'name': 'TA Express Los Angeles',
                'brand': 'TA Express',
                'addr:city': 'Los Angeles',
                'addr:state': 'CA',
            }
        }
        result = parse_ta_feature(feature)
        assert result['brand_display_name'] == 'TA Express'

    def test_parse_ta_no_def(self):
        from app.import_stops.ta_petro_api import parse_ta_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-73.0, 40.7]},
            'properties': {
                'ref': '025',
                'name': 'TA New York',
                'brand': 'TA',
                'addr:city': 'Newark',
                'addr:state': 'NJ',
                'fuel:diesel': 'yes',
            }
        }
        result = parse_ta_feature(feature)
        assert result['has_def'] is False

    def test_parse_ta_coordinates(self):
        from app.import_stops.ta_petro_api import parse_ta_feature
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-87.6298, 41.8781]},
            'properties': {
                'ref': '001',
                'brand': 'TA',
                'addr:city': 'Chicago',
                'addr:state': 'IL',
            }
        }
        result = parse_ta_feature(feature)
        assert result['latitude'] == 41.8781
        assert result['longitude'] == -87.6298


def test_loves_csv_import_cli(app, db):
    tmpdir = tempfile.mkdtemp()
    csv_path = os.path.join(tmpdir, 'loves_test.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Store Number', 'Store Name', 'Address', 'City', 'State',
            'Zip', 'Country', 'Latitude', 'Longitude', 'Phone',
            'Has Diesel', 'Has Showers', 'Number Of Showers',
            'Has Scale', 'Has Tire Care', 'Has DEF', 'Truck Parking Spaces',
        ])
        writer.writeheader()
        writer.writerow({
            'Store Number': '777', 'Store Name': "Love's Travel Stop",
            'Address': '555 Test Rd', 'City': 'Austin', 'State': 'TX',
            'Zip': '78701', 'Country': 'US', 'Latitude': '30.2672',
            'Longitude': '-97.7431', 'Phone': '(512) 555-0100',
            'Has Diesel': 'Y', 'Has Showers': 'Y', 'Number Of Showers': '6',
            'Has Scale': 'N', 'Has Tire Care': 'Y', 'Has DEF': 'Y',
            'Truck Parking Spaces': '80',
        })
    runner = app.test_cli_runner()
    result = runner.invoke(args=['import-stops', 'loves', '--file', csv_path])
    assert 'Imported 1' in result.output
    stop = TruckStop.query.filter_by(store_number='777', brand='loves').first()
    assert stop is not None
    assert stop.city == 'Austin'
    os.unlink(csv_path)
    os.rmdir(tmpdir)
