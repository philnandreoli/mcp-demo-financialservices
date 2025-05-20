import os 
import pandas as pd
import requests
import multiprocessing
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from typing import Optional, List
import uvicorn
import yfinance as yf
from models.stock_technical_indicators import StockTechnicalIndicators
import numpy as np
from datetime import datetime, timedelta
import pytz

load_dotenv(override=True)
POLYGON_BASE_URL = os.getenv("POLYGON_BASE_URL")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

K_PERIOD=14
D_PERIOD=3

mcp = FastMCP(name="Stock Information MCP Server")
app = mcp.sse_app()


@mcp.tool(name="get-stock-information", description="Get stock information for a givent stock symbol")
def get_stock_information(ticker: str) -> dict:
    """
    Useful for getting the stock information for a given stock symbol
    """
    stock_info = yf.Ticker(ticker=ticker).get_info()

    if stock_info is None:
        raise ValueError(f"Failed to get stock information for {ticker}")

    return stock_info

@mcp.tool(name="get-stock-financials", description="Get stock financials for a given ticker symbol and filing date if it is provided")
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

@mcp.tool(name="get-stock-news", description="Get news for a given stock symbol")
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

@mcp.tool(name="get-stock-technical-indicators", description="Get technical indicators for a given stock symbol")
def get_stock_technical_indicators(ticker: str) -> List[StockTechnicalIndicators]:
    """
    Used for getting the technical indicators and historical data for a stock symbol.
    """
    try:
        prices = yf.Ticker(ticker).history(period="1y")
        calculate_macd(prices)
        calculate_stochastics(prices)
        calculate_moving_averages(prices)
        calculate_cross_signals(prices)
        calculate_rsi(prices)
        calculate_adr(prices)
        calculate_obv(prices)

        # Filter for the last 6 months
        tz = 'America/New_York'
        six_months_ago = datetime.now(pytz.timezone(tz)) - timedelta(days=6*30)
        prices = prices[prices.index >= six_months_ago] 
        format_prices(prices)

        stock_technical_indicators = prices.reset_index().to_dict(orient='records')
        technical_indicators: List[StockTechnicalIndicators] = [StockTechnicalIndicators(**item) for item in stock_technical_indicators]

        return technical_indicators
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return []



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


def calculate_macd(prices):
    prices.ta.macd(close="Close", fast=12, slow=26, signal=9, append=True)
    prices.rename(columns={"MACD_12_26_9": "macd", "MACDs_12_26_9": "macd_signal", "MACDh_12_26_9": "macd_histogram"}, inplace=True)

def calculate_stochastics(prices):
    prices["n_high"] = prices["High"].rolling(K_PERIOD).max()
    prices["n_low"] = prices["Low"].rolling(K_PERIOD).min()
    prices["K"] = (prices["Close"] - prices["n_low"]) * 100 / (prices["n_high"] - prices["n_low"])
    prices["D"] = prices['K'].rolling(D_PERIOD).mean()

def calculate_moving_averages(prices):
    prices["ma_50"] = prices["Close"].rolling(window=50).mean()
    prices["ma_200"] = prices["Close"].rolling(window=200).mean()

def calculate_cross_signals(prices):
    prices["death_cross_signal"] = prices['ma_50'] < prices['ma_200']
    prices["death_cross"] = prices["death_cross_signal"].diff()
    prices["golden_cross_signal"] = prices['ma_50'] > prices['ma_200']
    prices['golden_cross'] = prices['golden_cross_signal'].diff()

#Calculate Relative Strength Index
def calculate_rsi(prices):
    delta = prices["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(7).mean()
    avg_loss = loss.rolling(7).mean()
    rs = avg_gain / avg_loss
    prices["rsi"] = 100 - (100 / (1 + rs))

#Calculate Average Daily Range
def calculate_adr(prices):
    prices["dr"] = prices["High"] - prices["Low"]
    prices["adr"] = prices["dr"].rolling(7).mean()

#Calculate On-Balance Volume
def calculate_obv(prices):
    prices["obv"] = (np.sign(prices["Close"].diff()) * prices["Volume"]).fillna(0).cumsum()

def format_prices(prices):
    prices.index = prices.index.strftime("%Y-%m-%d")
    prices.drop(columns=["Dividends", "Stock Splits"], axis=1, inplace=True)
    prices.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
    prices.rename_axis("date", inplace=True)