#!/usr/bin/env python3
"""One-off script: fetch Love's stores from API and POST to admin endpoint."""
import json
import requests
import re

LOVES_API_URL = 'https://www.loves.com/api/fetch_stores'
ADMIN_URL = 'https://stops.truckerpro.net/api/v1/admin/truck-stops'
ADMIN_KEY = 'f02692e7a9a59241f451fd21b1dbd35dc4945125af6edd4291403adb441274af'
BATCH_SIZE = 20


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def generate_slug(brand, store_number, city, state):
    parts = [brand.replace('_', '-')]
    if store_number:
        parts.append(store_number)
    parts.extend([city, state])
    return slugify(' '.join(parts))


def parse_store(store):
    number = str(store.get('number', '')).strip()
    city = (store.get('city') or '').strip()
    state = (store.get('state') or '').strip()
    lat = store.get('latitude')
    lng = store.get('longitude')
    if not lat or not lng:
        return None
    return {
        'brand': 'loves',
        'brand_display_name': "Love's Travel Stops",
        'name': f"Love's Travel Stop #{number}",
        'store_number': number,
        'address': (store.get('address1') or '').strip(),
        'city': city,
        'state_province': state,
        'postal_code': (store.get('zip') or '').strip(),
        'country': 'US',
        'latitude': lat,
        'longitude': lng,
        'highway': (store.get('highway') or '').strip() or None,
        'exit_number': (store.get('exitNumber') or '').strip() or None,
        'phone': (store.get('phoneNumber') or '').strip() or None,
        'has_diesel': True,
        'data_source': 'api',
        'slug': generate_slug('loves', number, city, state),
    }


def main():
    print("Fetching Love's stores from API...")
    resp = requests.get(LOVES_API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    stores = data.get('stores', [])
    print(f"Got {len(stores)} stores from API.")

    parsed = []
    for s in stores:
        p = parse_store(s)
        if p:
            parsed.append(p)
    print(f"Parsed {len(parsed)} valid stores (with coordinates).")

    total = 0
    for i in range(0, len(parsed), BATCH_SIZE):
        batch = parsed[i:i + BATCH_SIZE]
        resp = requests.post(
            ADMIN_URL,
            json=batch,
            headers={
                'X-Admin-Key': ADMIN_KEY,
                'Content-Type': 'application/json',
            },
            timeout=60,
        )
        if resp.status_code == 200:
            result = resp.json()
            total += result.get('count', 0)
            print(f"  Batch {i // BATCH_SIZE + 1}: {result.get('count', 0)} imported")
        else:
            print(f"  Batch {i // BATCH_SIZE + 1} FAILED: {resp.status_code} {resp.text[:200]}")

    print(f"\nDone! Total imported: {total}")


if __name__ == '__main__':
    main()
