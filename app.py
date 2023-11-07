from flask import Flask, render_template, request, jsonify
import folium
from folium import plugins
import json
import requests

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

app = Flask(__name__)
llm = OpenAI(openai_api_key="INSERT_YOUR_KEY")
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
    
    #return jsonify({'response': resp})
    print(resp)
    print(lat, long)
    #print("Address")
    #print(get_address(lat, long))
    #"location": get_address(lat, long)
    print("JSONIFYING")
    return jsonify({"response": resp})

def get_address(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    headers = {
        "User-Agent": "CSSchoolProject/1.0 (harishrsk11@gmail.com)",  # Replace "YourAppName" with the name of your app
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

if __name__ == '__main__':
    app.run(debug=True)