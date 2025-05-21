import os
import pathlib
import asyncio

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings
from dotenv import load_dotenv

load_dotenv(override=True)

async def main():
    async with (
        MCPServerSse(
            name="Stock Sse Server",
            params={
                "url": os.getenv("MCP_STOCKS_URL"),
                "client_session_timeout_seconds": 300
            }
        ) as stock_server,
        MCPServerSse(
            name="Weather sse server",
            params={
                "url": os.getenv("MCP_WEATHER_URL"),
                "client_session_timeout_seconds": 300
            }
        ) as weather_server
    ):
        agent = Agent(
            name="Assistant",
            model="gpt-4.1",
            instructions="Use the weaather and stock plugins to answer the user questions.  Please provide the date and time of the information you are providing if it is available.",
            mcp_servers=[stock_server, weather_server],
            model_settings=ModelSettings(temperature=0.0) 
        )

        result = await Runner.run(starting_agent=agent, input="What is Microsoft and Nvidia's stock price and RSI?") 

        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())