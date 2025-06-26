from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    """Get current weather conditions for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # Get the current conditions from the nearest station
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch weather data for this location."

    # Get observation stations
    stations_url = points_data["properties"]["observationStations"]
    stations_data = await make_nws_request(stations_url)

    if not stations_data or not stations_data.get("features"):
        return "Unable to find nearby weather stations."

    # Get observations from the first available station
    station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
    observations_url = f"{NWS_API_BASE}/stations/{station_id}/observations/latest"
    
    observation_data = await make_nws_request(observations_url)
    
    if not observation_data:
        return "Unable to fetch current observations."

    props = observation_data["properties"]
    
    # Format temperature
    temp_c = props.get("temperature", {}).get("value")
    temp_f = None
    if temp_c:
        temp_f = (temp_c * 9/5) + 32

    # Format other data
    humidity = props.get("relativeHumidity", {}).get("value")
    wind_speed = props.get("windSpeed", {}).get("value")
    wind_direction = props.get("windDirection", {}).get("value")
    description = props.get("textDescription", "No description available")

    result = f"""
Current Weather Conditions:
Description: {description}
Temperature: {temp_c:.1f}°C ({temp_f:.1f}°F)
Humidity: {humidity}%
Wind Speed: {wind_speed} m/s
Wind Direction: {wind_direction}°
"""
    
    return result.strip()

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 