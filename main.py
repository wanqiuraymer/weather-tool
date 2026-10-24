import requests
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from pydantic import BaseModel,Field
import json
from pathlib import Path
load_dotenv()
lat=42.6056
lon=-83.1499
WEATHER_ENDPOINT = os.environ['API_ENDPOINT']
client = Anthropic()
parameters={
    "latitude": lat,
    "longitude": lon,
    "current": "temperature_2m,weather_code", 
}
try:
    response = requests.get(url=WEATHER_ENDPOINT, params=parameters)
    print(response.status_code)
except requests.exceptions.RequestException:
    print("Request failed, but the program didn't not crash")
response.raise_for_status()
weather_data = response.json()
temp_c= weather_data["current"]["temperature_2m"]
temp_f=temp_c* 9 / 5 + 32
weather_cd_str = str(weather_data["current"]["weather_code"])

with open(Path(__file__).parent / "weather_code.json") as f:
    weather_codes=json.load(f)
if weather_cd_str in weather_codes:  #weather_desc = weather_codes.get(weather_cd_str, "Unknown")
    weather_desc = weather_codes[weather_cd_str]
else:
    weather_desc="Unknown"
class Location(BaseModel):
    place: str = Field(description="show the place name and country name with the latitude and longitude")


claude_response=client.messages.parse(
    model="claude-haiku-5-5",
    system="you convert latitude and longitude to the place",
    messages=[{"role":"user", "content": f"Latitude {lat}, longitude {lon}"}],
    max_tokens=16000,
    output_format=Location
)
location_found=claude_response.parsed_output
print(f"📍 Location:{location_found.place}")
print(f"🌡️ Temperature: {temp_c}°C ({temp_f:.1f}°F)")
print(f"☀️ Condition: {weather_desc}")