import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# get API keys from your API website
RSA_API_KEY = ""

app = Flask(__name__)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA L2: Python Saas.</h2></p>"

def verify_token(json_data):
    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

def get_weather(location: str, date: str):
    url_base_url = "https://api.weatherapi.com/v1"
    url_endpoint = "history.json"

    print(date)
    querry_params = f"?key={RSA_API_KEY}&q={location}&dt={date}"

    url = f"{url_base_url}/{url_endpoint}{querry_params}"
    print(url)
    payload = {}
    headers = {"Authorization": RSA_API_KEY}

    response = requests.request("GET", url, headers=headers, data=payload)
    # get necessary data from payload
    response_json = json.loads(response.text)
    if response_json.get('error'):
        return response_json

    weather = response_json.get("forecast").get("forecastday")[0]

    return weather

def select_weather_fields(weather_response, include_hours):
    # write an error if the weather api gives an error
    if weather_response.get("error"):
        return weather_response

    # otherwise build a model
    day = weather_response.get("day")
    weather_fields = {
        "temp_c": day.get("avgtemp_c"),
        "maxtemp_c": day.get("maxtemp_c"),
        "mintemp_c": day.get("mintemp_c"),
        "maxwind_mph": day.get("maxwind_mph"),
        "maxwind_kph": day.get("maxwind_kph"),
        "avghumidity": day.get("avghumidity"),
        "totalprecip_mm": day.get("totalprecip_mm"),
        "condition": day.get("condition").get("text")
    }
    if include_hours:
        weather_fields["hours"] = weather_response.get("hour")

    return weather_fields


@app.route(
    "/content/api/v1/integration/weather",
    methods=["POST"],
)
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()
    verify_token(json_data)

    date = "" # if no date is provided - use current day
    if json_data.get("date"):
        date = json_data.get("date")
    else:
        date = dt.datetime.today().strftime('%Y-%m-%d')

    location = ""
    if json_data.get("location"):
        location = json_data.get("location")

    get_hours = False
    if json_data.get("get_hours"):
        get_hours = json_data.get("get_hours")

    weather_response = get_weather(location, date)

    end_dt = dt.datetime.now()

    result = {
        "requester_name": json_data.get("requester_name"),
        "timestamp": end_dt,
        "location": location,
        "date": date,
        "weather": select_weather_fields(weather_response, get_hours),
    }

    return result
