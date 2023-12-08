import psycopg2
import json

conn = psycopg2.connect(
        host="172.16.8.190",
        database="demo",
        user='test',
        password='123456')
        
def points():
    cursor = conn.cursor()
    cursor.execute("SELECT better_lat, better_long, company FROM locations;")
    points = cursor.fetchall()

    points_geojson = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            },
            "properties": {
                "description": name
            }
        } for lat, lon, name in points
    ]
    cursor.close()
    return points_geojson



def ppoints():
    cursor = conn.cursor()

    # Query for fatal_accidents data
    cursor.execute("SELECT ST_Y(location::geometry) AS latitude, ST_X(location::geometry) AS longitude, objectid FROM fatal_accidents;")
    fatal_accidents_points = cursor.fetchall()

    # Query for aqi data
    cursor.execute("SELECT latitude, longitude, county FROM aqi;")
    aqi_points = cursor.fetchall()

    fatal_accidents_geojson = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            },
            "properties": {
                "description": "Fatal Accident ID: " + str(objectid)
            }
        }
        for lat, lon, objectid in fatal_accidents_points
        if lat is not None and lon is not None
    ]

    aqi_geojson = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            },
            "properties": {
                "description": "AQI Location: " + county
            }
        }
        for lat, lon, county in aqi_points
        if lat is not None and lon is not None
    ]

    cursor.close()

    # Combine all points into a single GeoJSON feature collection
    all_points_geojson = {
        "type": "FeatureCollection",
        "features": fatal_accidents_geojson + aqi_geojson
    }
    print(fatal_accidents_geojson)
    return all_points_geojson



def locations(lat, lon):
    cursor = conn.cursor()

    query = """
    :geography, 5000);
    """
    cursor.execute(query, (lon, lat))
    results = cursor.fetchall()

    cursor.close()

    locations = []
    for company, location_json in results:
        location = json.loads(location_json)
        locations.append({
            "company": company,
            "latitude": location['coordinates'][1],
            "longitude": location['coordinates'][0]
        })
    print(locations)
    return locations

def get_aqi_locations(lat, lon, radius=50000):
    radius=50000
    print(lat, lon)
    with conn.cursor() as cursor:
        query = """
        SELECT latitude, longitude, county, aqi_median
        FROM aqi_2022
        WHERE ST_DWithin(location, ST_MakePoint(%s, %s)::geography, %s);
        """
        cursor.execute(query, (lon, lat, radius))
        results = cursor.fetchall()
    
    aqi = [
        {"latitude": lat, "longitude": lon, "county": county, "aqi_median": aqi_median}
        for lat, lon, county, aqi_median in results
    ]
    print("aqi: ", aqi)
    return aqi

def get_fatal_accident_locations(lat, lon, radius=100000):
    with conn.cursor() as cursor:
        query = """
        SELECT ST_Y(location::geometry) AS latitude, 
           ST_X(location::geometry) AS longitude, 
           objectid, 
           fatals
        FROM fatal_accidents
        WHERE ST_DWithin(location, ST_MakePoint(%s, %s)::geography, %s);
        """
        cursor.execute(query, (lon, lat, radius))
        results = cursor.fetchall()
        
    fatals = [
        {"latitude": lat, "longitude": lon, "objectid": obj_id, "fatals": fatals}
        for lat, lon, obj_id, fatals in results
    ]
    print(fatals)
    return fatals


def get_housing_data(lat, lon, radius=1000):
    query = """
    SELECT total_rooms, total_bedrooms, median_house_value, ST_Y(location::geometry) AS latitude, 
           ST_X(location::geometry) AS longitude
    FROM housing_test
    WHERE ST_DWithin(location, ST_MakePoint(%s, %s)::geography, %s);
    """
    
    cur = conn.cursor()
    cur.execute(query, (lon, lat, radius))
    houses = cur.fetchall()

    houses_json = [
        {
            "total_rooms": total_rooms,
            "total_bedrooms": total_bedrooms,
            "median_house_value": median_house_value,
            "latitude": latitude,
            "longitude": longitude
        }
        for total_rooms, total_bedrooms, median_house_value, latitude, longitude in houses
    ]
    
    print(houses_json)
    return houses_json


def filtered_housing(lat, lon, aqi_filter, accident_risk_filter, acc_level, radius):
    #print(lat, lon, radius)
    
    #query = """
    #SELECT latitude, longitude, median_house_value FROM housing_test h 
    #WHERE ST_DWithin(h.location, ST_MakePoint(%s, %s)::geography, %s)
    #AND (SELECT MIN(aqi_median) FROM aqi_2022 WHERE ST_DWithin(aqi_2022.location, ST_MakePoint(%s, %s)::geography, 50000)) <= %s 
    #AND (SELECT MAX(fatals) FROM fatal_accidents WHERE ST_DWithin(fatal_accidents.location, ST_MakePoint(%s, %s)::geography, %s)) <= %s;
    #"""
    # acc_level == "low" | "mediums":

    query = """
    SELECT h.latitude, h.longitude, h.median_house_value 
    FROM housing_test h 
    WHERE ST_DWithin(h.location, ST_MakePoint(%s, %s)::geography, %s)
    AND (SELECT MAX(aqi_median) FROM aqi_2022 WHERE ST_DWithin(aqi_2022.location, ST_MakePoint(%s, %s)::geography, 50000)) <= %s
    AND (SELECT AVG(fatals) FROM fatal_accidents WHERE ST_DWithin(fatal_accidents.location, ST_MakePoint(%s, %s)::geography, %s)) <= %s;
    """

    cur = conn.cursor()
    print(query % (lon, lat, radius, lon, lat, aqi_filter, lon, lat, radius, accident_risk_filter))
    cur.execute(query, (lon, lat, radius, lon, lat, aqi_filter, lon, lat, radius, accident_risk_filter))
    results = cur.fetchall()

    houses_json = [
        {
            "median_house_value": median_house_value,
            "latitude": latitude,
            "longitude": longitude
        }
        for latitude, longitude, median_house_value, in results
    ]
    print(houses_json)
    return houses_json
