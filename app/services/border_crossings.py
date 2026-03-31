"""US-Canada border crossing coordinates and distance computation."""
from ..services.geo_service import haversine_distance

# Major US-Canada border crossings: (name, latitude, longitude)
BORDER_CROSSINGS = [
    ('Pacific Highway (Surrey/Blaine)', 49.0024, -122.7571),
    ('Douglas (Surrey/Blaine)', 49.0024, -122.7543),
    ('Aldergrove (Langley/Lynden)', 49.0003, -122.4637),
    ('Huntingdon (Abbotsford/Sumas)', 49.0017, -122.2648),
    ('Osoyoos (Osoyoos/Oroville)', 49.0000, -119.4382),
    ('Kingsgate (Kingsgate/Eastport)', 49.0002, -116.1815),
    ('Boundary Bay (Delta/Point Roberts)', 49.0015, -123.0569),
    ('Coutts (Coutts/Sweetgrass)', 49.0000, -111.9614),
    ('Carway (Carway/Piegan)', 49.0000, -113.3944),
    ('Chief Mountain (Waterton/Babb)', 49.0000, -113.6600),
    ('North Portal (North Portal/Portal)', 49.0000, -102.5530),
    ('Regway (Regway/Raymond)', 49.0000, -104.6036),
    ('Emerson (Emerson/Pembina)', 49.0006, -97.2384),
    ('Boissevain (Boissevain/Dunseith)', 49.0000, -100.0574),
    ('Sprague (Sprague/Lancaster)', 49.0000, -95.5903),
    ('Fort Frances (Fort Frances/International Falls)', 48.6010, -93.4105),
    ('Pigeon River (Thunder Bay/Grand Portage)', 48.0000, -89.5845),
    ('Sault Ste. Marie (SSM ON/SSM MI)', 46.5126, -84.3476),
    ('Blue Water Bridge (Point Edward/Port Huron)', 42.9990, -82.4218),
    ('Ambassador Bridge (Windsor/Detroit)', 42.3113, -83.0756),
    ('Detroit-Windsor Tunnel (Windsor/Detroit)', 42.3224, -83.0442),
    ('Queenston-Lewiston Bridge (Niagara/Lewiston)', 43.1534, -79.0474),
    ('Rainbow Bridge (Niagara Falls)', 43.0886, -79.0683),
    ('Peace Bridge (Fort Erie/Buffalo)', 42.9063, -78.9047),
    ('Whirlpool Bridge (Niagara Falls)', 43.1117, -79.0633),
    ('Thousand Islands Bridge (Lansdowne/Alexandria Bay)', 44.3581, -75.9778),
    ('Prescott-Ogdensburg Bridge (Prescott/Ogdensburg)', 44.7217, -75.4703),
    ('Cornwall (Cornwall/Massena)', 44.9976, -74.7694),
    ('Lacolle (Lacolle/Champlain)', 45.0086, -73.3726),
    ('St-Armand/Philipsburg (Philipsburg/Highgate Springs)', 45.0061, -73.0839),
    ('Stanstead (Stanstead/Derby Line)', 45.0060, -72.1008),
    ('Rock Island (Stanstead/Derby Line)', 45.0087, -72.0953),
    ('Hereford Road (East Hereford/Beecher Falls)', 45.0000, -71.4902),
    ('Armstrong (Armstrong/Fort Covington)', 45.0050, -74.2233),
    ('St. Stephen (St. Stephen/Calais)', 45.1915, -67.2799),
    ('Woodstock (Woodstock/Houlton)', 46.1501, -67.5792),
    ('Edmundston (Edmundston/Madawaska)', 47.3655, -68.3249),
    ('St. Leonard (St. Leonard/Van Buren)', 47.1657, -67.9245),
    ('Campobello Island (Campobello/Lubec)', 44.8894, -66.9522),
    ('Yarmouth Ferry (Yarmouth/Bar Harbor)', 43.8361, -66.1174),
    ('Windygates (Windygates/Hannah)', 49.0000, -98.0574),
    ('Snowflake (Snowflake/Hannah)', 49.0000, -98.3036),
    ('Del Bonita (Del Bonita/Del Bonita)', 49.0000, -112.5000),
    ('Aden (Aden/Wild Horse)', 49.0000, -110.0000),
    ('Lansdowne (Lansdowne/Cape Vincent)', 44.3581, -76.2000),
    ('Rainy River (Rainy River/Baudette)', 48.7200, -94.5700),
    ('Roosville (Grasmere/Roosville)', 49.0000, -115.0670),
    ('Nelway (Nelway/Metaline Falls)', 49.0000, -117.2664),
    ('Cascade (Cascade/Laurier)', 49.0000, -118.2131),
    ('Midway (Midway/Ferry)', 49.0000, -118.7700),
    ('Nighthawk (Nighthawk/Oroville)', 49.0000, -119.6000),
    ('BC Ferries (Sidney/Anacortes)', 48.6431, -123.3965),
    ('Wolfe Island Ferry (Kingston/Cape Vincent)', 44.1876, -76.4312),
]


def find_nearest_crossing(latitude, longitude):
    """Find nearest border crossing. Returns (crossing_name, distance_km)."""
    nearest_name = None
    nearest_dist = float('inf')
    for name, lat, lng in BORDER_CROSSINGS:
        dist = haversine_distance(latitude, longitude, lat, lng)
        if dist < nearest_dist:
            nearest_dist = dist
            nearest_name = name
    return nearest_name, round(nearest_dist, 1)


def compute_border_distance(truck_stop):
    """Compute and set nearest border crossing on a TruckStop. Does NOT commit."""
    name, dist = find_nearest_crossing(truck_stop.latitude, truck_stop.longitude)
    truck_stop.nearest_border_crossing = name
    truck_stop.border_distance_km = dist
