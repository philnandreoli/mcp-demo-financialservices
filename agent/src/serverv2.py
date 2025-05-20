import os
import pathlib
import asyncio

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings
from dotenv import load_dotenv

load_dotenv("C:\\Users\\phandreo\\source\\mcp-demo\\multiple-use-demo\\agent\\src\\.env")

async def main():
    async with (
        MCPServerSse(
            name="Stock Sse Server",
            params={
                "url": "https://andrmcpdemoacastocks001.ashystone-5e0a4002.eastus2.azurecontainerapps.io/sse",
                "client_session_timeout_seconds": 300
            }
        ) as stock_server,
        MCPServerSse(
            name="Weather sse server",
            params={
                "url": "https://andrmcpdemoacaweather001.ashystone-5e0a4002.eastus2.azurecontainerapps.io/sse",
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