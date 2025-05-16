import os 
import requests
import multiprocessing
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import uvicorn

load_dotenv(override=True)
API_KEY = os.getenv("OPENWEATHER_API_KEY")

mcp = FastMCP(name="Weather MCP Server")
app = mcp.sse_app()

@mcp.tool(name="get_weather", description="Get weather information for a given location. The city, state and country, formatted like '<city>, <state>, <two letter country>'")
def get_weather(location: str) -> dict:
    """
    Usefull for getting thew current weather for a given location
    """
    if API_KEY is None:
        raise ValueError("API_KEY is not set. Please set the OPENWEATHER_API_KEY environment variable.")
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=imperial"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to get weather for {location}")
    

    return response.json()

@mcp.tool(name="get_weather_forecast", description="Get weather forecast for a given location and a specific number of days (default is 5 days). The city, state and country, formatted like '<city>, <state>, <two letter country>'")
def get_weather_forecast(location: str, number_of_days: int = 5) -> dict:
    """
    Useful for getting the weather forecast for a given location
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key is None:
        raise ValueError("Please provide an API key for OpenWeather in the environment variable OPENWEATHER_API_KEY")
    
    url = f"https://api.openweathermap.org/data/2.5/forecast/daily?q={location}&cnt={number_of_days}&appid={API_KEY}&units=imperial"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to get weather for {location}")

    return response.json()


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    if os.getenv("RUNNING_IN_PRODUCTION"):
        # Production mode with multiple workers for better performance
        uvicorn.run(
            "server:app",  # Pass as import string
            host="0.0.0.0",
            port=8080,
            workers=(multiprocessing.cpu_count() * 2) + 1,
            timeout_keep_alive=300  # Increased for SSE connections
        )
    else:
        # Development mode with a single worker for easier debugging
        uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)