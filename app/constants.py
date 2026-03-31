# app/constants.py
"""Shared constants for Truck Parking Club."""

PROVINCE_MAP = {
    'ontario': {'name': 'Ontario', 'code': 'ON'},
    'alberta': {'name': 'Alberta', 'code': 'AB'},
    'british-columbia': {'name': 'British Columbia', 'code': 'BC'},
    'manitoba': {'name': 'Manitoba', 'code': 'MB'},
    'quebec': {'name': 'Quebec', 'code': 'QC'},
    'saskatchewan': {'name': 'Saskatchewan', 'code': 'SK'},
    'new-brunswick': {'name': 'New Brunswick', 'code': 'NB'},
    'nova-scotia': {'name': 'Nova Scotia', 'code': 'NS'},
    'prince-edward-island': {'name': 'Prince Edward Island', 'code': 'PE'},
    'newfoundland-labrador': {'name': 'Newfoundland and Labrador', 'code': 'NL'},
    'northwest-territories': {'name': 'Northwest Territories', 'code': 'NT'},
    'yukon': {'name': 'Yukon', 'code': 'YT'},
    'nunavut': {'name': 'Nunavut', 'code': 'NU'},
}

PROVINCE_CODE_TO_SLUG = {v['code']: k for k, v in PROVINCE_MAP.items()}

PROVINCIAL_TAX = {
    'AB': {'type': 'GST', 'rate': 0.05},
    'BC': {'type': 'GST+PST', 'gst': 0.05, 'pst': 0.07, 'rate': 0.12},
    'MB': {'type': 'GST+PST', 'gst': 0.05, 'pst': 0.07, 'rate': 0.12},
    'NB': {'type': 'HST', 'rate': 0.15},
    'NL': {'type': 'HST', 'rate': 0.15},
    'NS': {'type': 'HST', 'rate': 0.15},
    'NT': {'type': 'GST', 'rate': 0.05},
    'NU': {'type': 'GST', 'rate': 0.05},
    'ON': {'type': 'HST', 'rate': 0.13},
    'PE': {'type': 'HST', 'rate': 0.15},
    'QC': {'type': 'GST+QST', 'gst': 0.05, 'qst': 0.09975, 'rate': 0.14975},
    'SK': {'type': 'GST+PST', 'gst': 0.05, 'pst': 0.06, 'rate': 0.11},
    'YT': {'type': 'GST', 'rate': 0.05},
}

LOCATION_TYPE_LABELS = {
    'truck_stop': 'Truck Stop',
    'rest_area': 'Rest Area',
    'private_yard': 'Private Yard',
    'warehouse': 'Warehouse',
    'repair_shop': 'Repair Shop',
    'towing_company': 'Towing Company',
    'cdl_school': 'CDL School',
    'storage_facility': 'Storage Facility',
    'farm_property': 'Farm Property',
    'industrial_lot': 'Industrial Lot',
    'other': 'Other',
}

AMENITY_LABELS = {
    'security_camera': {'label': 'Security Camera', 'icon': 'fas fa-video'},
    '24_7_access': {'label': '24/7 Access', 'icon': 'fas fa-clock'},
    'restrooms': {'label': 'Restrooms', 'icon': 'fas fa-restroom'},
    'showers': {'label': 'Showers', 'icon': 'fas fa-shower'},
    'wifi': {'label': 'Wi-Fi', 'icon': 'fas fa-wifi'},
    'food_nearby': {'label': 'Food Nearby', 'icon': 'fas fa-utensils'},
    'restaurant_onsite': {'label': 'Restaurant On-site', 'icon': 'fas fa-burger'},
    'truck_wash': {'label': 'Truck Wash', 'icon': 'fas fa-droplet'},
    'repair_shop': {'label': 'Repair Shop', 'icon': 'fas fa-wrench'},
    'cat_scale': {'label': 'CAT Scale', 'icon': 'fas fa-weight-scale'},
    'ev_charging': {'label': 'EV Charging', 'icon': 'fas fa-bolt'},
    'block_heater_plugin': {'label': 'Block Heater Plug-in', 'icon': 'fas fa-plug'},
    'heated_facility': {'label': 'Heated Facility', 'icon': 'fas fa-temperature-high'},
    'fenced': {'label': 'Fenced', 'icon': 'fas fa-shield-halved'},
    'gated': {'label': 'Gated', 'icon': 'fas fa-door-closed'},
    'lit_lot': {'label': 'Lit Lot', 'icon': 'fas fa-lightbulb'},
    'paved': {'label': 'Paved', 'icon': 'fas fa-road'},
    'gravel': {'label': 'Gravel', 'icon': 'fas fa-mountain'},
    'snow_removal': {'label': 'Snow Removal', 'icon': 'fas fa-snowplow'},
    'fuel_nearby': {'label': 'Fuel Nearby', 'icon': 'fas fa-gas-pump'},
}

# ── Truck Stops Directory ────────────────────────────────────

US_STATES = {
    'alabama': {'name': 'Alabama', 'code': 'AL'},
    'alaska': {'name': 'Alaska', 'code': 'AK'},
    'arizona': {'name': 'Arizona', 'code': 'AZ'},
    'arkansas': {'name': 'Arkansas', 'code': 'AR'},
    'california': {'name': 'California', 'code': 'CA'},
    'colorado': {'name': 'Colorado', 'code': 'CO'},
    'connecticut': {'name': 'Connecticut', 'code': 'CT'},
    'delaware': {'name': 'Delaware', 'code': 'DE'},
    'florida': {'name': 'Florida', 'code': 'FL'},
    'georgia': {'name': 'Georgia', 'code': 'GA'},
    'hawaii': {'name': 'Hawaii', 'code': 'HI'},
    'idaho': {'name': 'Idaho', 'code': 'ID'},
    'illinois': {'name': 'Illinois', 'code': 'IL'},
    'indiana': {'name': 'Indiana', 'code': 'IN'},
    'iowa': {'name': 'Iowa', 'code': 'IA'},
    'kansas': {'name': 'Kansas', 'code': 'KS'},
    'kentucky': {'name': 'Kentucky', 'code': 'KY'},
    'louisiana': {'name': 'Louisiana', 'code': 'LA'},
    'maine': {'name': 'Maine', 'code': 'ME'},
    'maryland': {'name': 'Maryland', 'code': 'MD'},
    'massachusetts': {'name': 'Massachusetts', 'code': 'MA'},
    'michigan': {'name': 'Michigan', 'code': 'MI'},
    'minnesota': {'name': 'Minnesota', 'code': 'MN'},
    'mississippi': {'name': 'Mississippi', 'code': 'MS'},
    'missouri': {'name': 'Missouri', 'code': 'MO'},
    'montana': {'name': 'Montana', 'code': 'MT'},
    'nebraska': {'name': 'Nebraska', 'code': 'NE'},
    'nevada': {'name': 'Nevada', 'code': 'NV'},
    'new-hampshire': {'name': 'New Hampshire', 'code': 'NH'},
    'new-jersey': {'name': 'New Jersey', 'code': 'NJ'},
    'new-mexico': {'name': 'New Mexico', 'code': 'NM'},
    'new-york': {'name': 'New York', 'code': 'NY'},
    'north-carolina': {'name': 'North Carolina', 'code': 'NC'},
    'north-dakota': {'name': 'North Dakota', 'code': 'ND'},
    'ohio': {'name': 'Ohio', 'code': 'OH'},
    'oklahoma': {'name': 'Oklahoma', 'code': 'OK'},
    'oregon': {'name': 'Oregon', 'code': 'OR'},
    'pennsylvania': {'name': 'Pennsylvania', 'code': 'PA'},
    'rhode-island': {'name': 'Rhode Island', 'code': 'RI'},
    'south-carolina': {'name': 'South Carolina', 'code': 'SC'},
    'south-dakota': {'name': 'South Dakota', 'code': 'SD'},
    'tennessee': {'name': 'Tennessee', 'code': 'TN'},
    'texas': {'name': 'Texas', 'code': 'TX'},
    'utah': {'name': 'Utah', 'code': 'UT'},
    'vermont': {'name': 'Vermont', 'code': 'VT'},
    'virginia': {'name': 'Virginia', 'code': 'VA'},
    'washington': {'name': 'Washington', 'code': 'WA'},
    'west-virginia': {'name': 'West Virginia', 'code': 'WV'},
    'wisconsin': {'name': 'Wisconsin', 'code': 'WI'},
    'wyoming': {'name': 'Wyoming', 'code': 'WY'},
}

US_STATE_CODE_TO_SLUG = {v['code']: k for k, v in US_STATES.items()}

ALL_REGIONS = {**US_STATES, **PROVINCE_MAP}
ALL_REGION_CODE_TO_SLUG = {**US_STATE_CODE_TO_SLUG, **PROVINCE_CODE_TO_SLUG}

BRAND_MAP = {
    'loves': {'name': "Love's Travel Stops", 'slug': 'loves'},
    'pilot_flying_j': {'name': 'Pilot Flying J', 'slug': 'pilot-flying-j'},
    'ta_petro': {'name': 'TA / Petro', 'slug': 'ta-petro'},
    'flying_j': {'name': 'Flying J', 'slug': 'flying-j'},
    'petro': {'name': 'Petro Stopping Centers', 'slug': 'petro'},
    'ambest': {'name': 'Ambest', 'slug': 'ambest'},
    'husky': {'name': 'Husky', 'slug': 'husky'},
    'esso': {'name': 'Esso', 'slug': 'esso'},
    'shell': {'name': 'Shell', 'slug': 'shell'},
    'independent': {'name': 'Independent', 'slug': 'independent'},
}

BRAND_SLUG_TO_KEY = {v['slug']: k for k, v in BRAND_MAP.items()}

MAJOR_FREIGHT_CORRIDORS = [
    'I-95', 'I-90', 'I-80', 'I-75', 'I-70', 'I-65', 'I-55', 'I-45',
    'I-40', 'I-35', 'I-30', 'I-25', 'I-20', 'I-15', 'I-10', 'I-5',
    '401', '400', 'QEW', 'Trans-Canada',
]

MAJOR_METROS = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Dallas', 'Atlanta',
    'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Memphis',
    'Nashville', 'Indianapolis', 'Louisville', 'Columbus', 'Charlotte',
    'Toronto', 'Montreal', 'Vancouver', 'Calgary', 'Edmonton', 'Winnipeg',
]
