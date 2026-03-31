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
