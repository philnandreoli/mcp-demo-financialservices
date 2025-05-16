# Multiple Use MCP Demo

This repository demonstrates running multiple [MCP](https://pypi.org/project/mcp/) (Multi-Channel Processing) microservices using Docker Compose. It includes two services:

- **Weather MCP**: Provides weather and forecast data via OpenWeather API.
- **Stocks MCP**: Provides stock information, financials, and news via Polygon.io and Yahoo Finance.

## Project Structure

```
.
├── .env
├── .gitignore
├── docker-compose.yaml
├── mcp-stocks/
│   ├── .env
│   └── src/
│       ├── DOCKERFILE
│       ├── requirements.txt
│       └── server.py
└── mcp-weather/
    ├── .env
    └── src/
        ├── DOCKERFILE
        ├── requirements.txt
        └── server.py
```

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Environment Variables

Set API keys and endpoints in the root `.env` file:

```env
OPENWEATHER_API_KEY=your_openweather_api_key
POLYGON_BASE_URL=base_url_for_polygon
POLYGON_API_KEY=your_polygon_api_key
```

Each service also has its own `.env` file for local development.

## Usage

### Build and Run All Services

From the project root, run:

```sh
docker-compose up --build
```

- **Weather MCP**: [http://localhost:8080](http://localhost:8080)
- **Stocks MCP**: [http://localhost:8081](http://localhost:8081)

### Stopping Services

```sh
docker-compose down
```

## Service Details

### Weather MCP

- **API Key**: Requires `OPENWEATHER_API_KEY`
- **Endpoints**:
  - `/get_weather`: Get current weather for a location
  - `/get_weather_forecast`: Get weather forecast for a location

### Stocks MCP

- **API Keys**: Requires `POLYGON_API_KEY` and `POLYGON_BASE_URL`
- **Endpoints**:
  - `/get_stock_information`: Get stock info via Yahoo Finance
  - `/get_stock_financials`: Get stock financials via Polygon.io
  - `/get_stock_news`: Get news for a stock via Polygon.io

## Development

- Source code for each service is in its respective `src/` directory.
- Services use [FastMCP](https://pypi.org/project/mcp/) for API endpoints.
- Hot reload is enabled in development mode.

## License

MIT License
