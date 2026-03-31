"""Love's Travel Stops CSV column mapper."""


def _yn_to_bool(val):
    return str(val).strip().upper() in ('Y', 'YES', 'TRUE', '1')


def _safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_loves_row(row):
    return {
        'brand': 'loves',
        'brand_display_name': "Love's Travel Stops",
        'name': f"Love's {row.get('Store Name', 'Travel Stop')} #{row['Store Number']}",
        'store_number': str(row['Store Number']).strip(),
        'address': row.get('Address', '').strip(),
        'city': row.get('City', '').strip(),
        'state_province': row.get('State', '').strip(),
        'postal_code': row.get('Zip', '').strip(),
        'country': row.get('Country', 'US').strip() or 'US',
        'latitude': _safe_float(row.get('Latitude')),
        'longitude': _safe_float(row.get('Longitude')),
        'phone': row.get('Phone', '').strip() or None,
        'has_diesel': _yn_to_bool(row.get('Has Diesel', 'Y')),
        'has_showers': _yn_to_bool(row.get('Has Showers', 'N')),
        'shower_count': _safe_int(row.get('Number Of Showers')),
        'has_scale': _yn_to_bool(row.get('Has Scale', 'N')),
        'has_tire_service': _yn_to_bool(row.get('Has Tire Care', 'N')),
        'has_def': _yn_to_bool(row.get('Has DEF', 'N')),
        'truck_spots': _safe_int(row.get('Truck Parking Spaces')),
        'total_parking_spots': _safe_int(row.get('Truck Parking Spaces')),
        'data_source': 'csv_import',
    }
