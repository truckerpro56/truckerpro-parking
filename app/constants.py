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
