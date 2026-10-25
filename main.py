import requests
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from pydantic import BaseModel,Field
import json
from pathlib import Path
import csv
from datetime import datetime
load_dotenv()

WEATHER_ENDPOINT = os.environ['API_ENDPOINT']
client = Anthropic()
user_input=input("What city do you want to look up?\n").strip()
if not user_input:
    print("Please enter a city name.")
    exit()
class Location(BaseModel):
    found: bool = Field(description="false if the input is not a recognizable real place")
    place: str = Field(description="full place name, e.g. 'Paris, France'; empty if not found")
    ambiguous: bool = Field(description="true if several well-known places share this name")
    lat: float = Field(ge=-90, le=90, description=f"show the latitude of a place in decimal degrees")
    lon: float = Field(ge=-180, le=180, description=f"show the longitude of a place in decimal degrees")
system=(
    "Find the latitude and longitude of the place the user names. "
    "If it isn't a real place, set found to false and use 0 for lat and lon. "
    "If the name is ambiguous, pick the best-known one and set ambiguous to true."
)

claude_response=client.messages.parse(
    model="claude-haiku-5-5",
    system=system,
    messages=[{"role":"user", "content": f"find the lat and lon of {user_input}"}],
    max_tokens=2000,
    output_format=Location
)
location_found=claude_response.parsed_output
if location_found is None or not location_found.found:
    print("Sorry, I couldn't find that place. Try a city name like 'Tokyo'.")
    exit()
if location_found.ambiguous:
    print(f"Assuming you meant {location_found.place}. Add a state or country to be more specific.")
parameters={
    "latitude": location_found.lat,
    "longitude": location_found.lon,
    "current": "temperature_2m,weather_code", 
}
try:
    response = requests.get(url=WEATHER_ENDPOINT, params=parameters)
    print(response.status_code)
    response.raise_for_status()
except requests.exceptions.RequestException:
    print("Request failed, but the program didn't crash")
    exit()

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
row={
    "city": user_input,
    "latitude": location_found.lat,
    "longitude": location_found.lon,
    "temperature_f":f"{temp_f:.1f}",
    "weather_condition":weather_desc,
    "fetched_at": datetime.now().strftime("%m-%d-%Y %H:%M"),
}

file_exists=os.path.exists("weather_log.csv")
with open("weather_log.csv",mode="a", newline="") as f:
    writer=csv.DictWriter(f, fieldnames=row.keys())
    if not file_exists:
        writer.writeheader()
    writer.writerow(row)
print(f"📍 Location: {location_found.place}")
print(f"🌡️ Temperature: {temp_c}°C ({temp_f:.1f}°F)")
print(f"☀️ Condition: {weather_desc}")