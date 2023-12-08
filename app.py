from flask import Flask, render_template, request, jsonify
import folium
from folium import plugins
import json
import requests

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

import psycopg2
from flask import Flask, render_template, jsonify, request
import json
import postgis_conn as pcon

app = Flask(__name__)
llm = OpenAI(openai_api_key="OPEN AI API KEY")
chat_model = ChatOpenAI()

@app.route('/')
def index():
    m = folium.Map(
        location=[34, -118],
        zoom_start=13,
        tiles='Stamen Terrain'
    )

    folium.Circle(
        radius=100,
        location=[34, -118],
        popup='Los Angeles City',
        color='crimson',
        fill=False,
    ).add_to(m)

    m = m._repr_html_()

    return render_template('index.html', map=m)


@app.route('/askai', methods=['POST'])
def process_message():
    req = request.json
    chat = req.get('message')
    lat = req.get('lat')
    long = req.get('lng')
    address = get_address(lat, long)
    resp = askai(chat, lat, long, address)

    print(resp)
    print(lat, long)
    
    return jsonify({"response": resp})

def get_address(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    headers = {
        "User-Agent": "CSSchoolProject/1.0 (harishrsk11@gmail.com)", 
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    print("data: ", data)
    return data.get("display_name", "")


def askai(message, latitude, longitude, address):
    prompt = """{0}. {1}. Location details - latitude: {2}, longitude: {3}. 
            Please provide a response in the following JSON format: 
            {{"message": "Textual description or information about the location.", 
            "pins": {{"Place Name 1": [longitude1, latitude1], "Place Name 2": [longitude2, latitude2, ], ...}}}}. 
            If the user's query pertains to location-specific data like schools nearby or landmarks, 
            populate the "pins" with relevant details, always providing latitude first and then longitude.
            If the user is not specifically asking about locations but needs general information or guidance, 
            respond within the "message" key. 
            If no valid results or specific information is available, the message should be: 
            "Sorry, I cannot help with your request at the moment." and leave the "pins" empty. 
            Note: The response must strictly adhere to the JSON format with proper double quotes and delimiters."""


    """
    resp = {
        "message": f"{message}",
        "pins": {
        "Landmark1": [37.7749, -122.4194],
        "Landmark2": [34.0522, -118.2437],
        "Landmark3": [40.7128, -74.0060]
            }
        }
    """
    
    resp = llm.predict(prompt.format(message, latitude, longitude, address))
    #print(resp)
    #return json.loads(resp)
    
    resp = resp.replace("\n", " ").replace("\t", " ")  # replace newlines and tabs with spaces

    try:
        return json.loads(resp)
    except json.decoder.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        print("Response content:", resp)
        return {"error": "Failed to parse response"}

@app.route('/data/points')
def data_points():
    #return jsonify(pcon.points())
    return []

@app.route('/points')
def points():
    points_geojson = pcon.points()    
    return jsonify(points_geojson)

@app.route('/nearby_locations')
def nearby_locations():
    latv = request.args.get('lat', type=float)
    lonv = request.args.get('lon', type=float)

    locations = pcon.locations(latv, lonv)
    return jsonify(locations)

@app.route('/data/nearby_aqi')
def aqi_data():
    print("aqi_data")
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=float)
    data = pcon.get_aqi_locations(lat, lon, radius)
    print(data)
    return jsonify(data)

@app.route('/data/nearby_fatal_accidents')
def nearby_fatal_accidents():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=float)
    data = pcon.get_fatal_accident_locations(lat, lon, radius)
    print("Data returned from database:", data)  # Debugging line
    return jsonify(data)

@app.route('/data/nearby_housing')
def nearby_housing():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=float)
    result = pcon.get_housing_data(lat, lon, radius)
    return jsonify(result)

@app.route('/data/filtered_housing')
def get_filtered_housing():
    # Retrieve filter parameters from query string
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    aqi_filter = request.args.get('aqi', '')
    accident_risk_filter = request.args.get('accidentRisk', '')
    radius = request.args.get('radius', '')
    acc_level = accident_risk_filter
    print(lat, lon, radius, acc_level)
    aqi_thresholds = {
        'good': 50,
        'moderate': 100
    }

    accident_risk_thresholds = {
        'low': 2,
        'medium': 3,
        'high': 10 
    }

    data = pcon.filtered_housing(lat, lon, aqi_thresholds[aqi_filter], 
                                 accident_risk_thresholds[accident_risk_filter], acc_level, radius)

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)