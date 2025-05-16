import os 
import requests
import multiprocessing
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from typing import Optional
import uvicorn
import yfinance as yf

load_dotenv(override=True)
POLYGON_BASE_URL = os.getenv("POLYGON_BASE_URL")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

mcp = FastMCP(name="Stock Information MCP Server")
app = mcp.sse_app()


@mcp.tool(name="get_stock_inforation", description="Get stock information for a givent stock symbol")
def get_stock_information(ticker: str) -> dict:
    """
    Useful for getting the stock information for a given stock symbol
    """
    stock_info = yf.Ticker(ticker=ticker).get_info()

    if stock_info is None:
        raise ValueError(f"Failed to get stock information for {ticker}")

    return stock_info

@mcp.tool(name="get_stock_financials", description="Get stock financials for a given ticker symbol and filing date if it is provided")
def get_stock_financials(ticker: str, filing_date: Optional[str]) -> dict:
    """
    Useful for getting the stock financials for a given stock symbol
    """
    if not POLYGON_API_KEY:
        raise ValueError("No API key found for Polygon.io")
    if not POLYGON_BASE_URL:
        raise ValueError("No API endpoint found for Polygon.io")
    
    url = f"{POLYGON_BASE_URL}vX/reference/financials?ticker={ticker}&apiKey={POLYGON_API_KEY}"

    if filing_date:
        url += f"&filing_date={filing_date}"

    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to get stock news for {ticker}")
    
    return response.json()

@mcp.tool(name="get_stock_news", description="Get news for a given stock symbol")
def get_stock_news(ticker: str) -> dict:
    """
    Useful for getting the news for a given stock symbol
    """
    if not POLYGON_API_KEY:
        raise ValueError("POLYGON_API_KEY is not set. Please set the POLYGON_API_KEY environment variable.")
    if not POLYGON_BASE_URL:
        raise ValueError("POLYGON_API_ENDPOINT is not set. Please set the POLYGON_API_ENDPOINT environment variable.")
    
    url = f"{POLYGON_BASE_URL}v2/reference/news?ticker={ticker}&apiKey={POLYGON_API_KEY}"

    response = requests.get(url)

    if response.status_code != 200:
        raise ValueError(f"Failed to get stock news for {ticker}")
    
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