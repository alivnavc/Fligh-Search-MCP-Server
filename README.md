# Flight Search MCP Server

A Model Context Protocol (MCP) server that provides real-time flight search capabilities using SerpAPI. This server offers comprehensive flight data including prices, airlines, departure/arrival times, booking links, and airport information.

## Features

- **Real-time Flight Search**: Find available flights with prices, airlines, and booking links
- **Airport Information**: Search for airports by name, city, or IATA code
- **Price Trends**: Get price insights and trend analysis for optimal booking times
- **MCP Protocol**: Standardized MCP interface for easy integration with AI agents
- **HTTP Transport**: Runs on HTTP with streamable transport for reliable connections

## Prerequisites

- Python 3.8 or higher
- SerpAPI account and API key
- uv package manager (recommended) or pip

## Installation

### Using uv (Recommended)

1. **Clone or download the project**
2. **Install dependencies:**
   ```bash
   uv sync
   ```

### Using pip

1. **Clone or download the project**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with your SerpAPI key:

```env
SERPAPI_KEY=your_serpapi_key_here
```

### Getting a SerpAPI Key

1. Sign up at [SerpAPI](https://serpapi.com/)
2. Get your API key from the dashboard
3. Add it to your `.env` file

## Usage

### Starting the Server

Using uv:
```bash
uv run flight_search_mcp.py
```

Using python directly:
```bash
python flight_search_mcp.py
```

The server will start on `http://localhost:8001/mcp`

### Available Tools

#### 1. search_flights

Search for available flights between airports.

**Parameters:**
- `source` (string): Departure airport IATA code (e.g., "BOM", "JFK")
- `destination` (string): Arrival airport IATA code (e.g., "DEL", "LAX")
- `departure_date` (string): Departure date in YYYY-MM-DD format
- `return_date` (string, optional): Return date in YYYY-MM-DD format
- `currency` (string, optional): Currency for pricing (default: "USD")

**Example JSON-RPC call:**
```json
{
    "jsonrpc": "2.0",
    "id": "flight-search-1",
    "method": "tools/call",
    "params": {
        "name": "search_flights",
        "arguments": {
            "source": "BOM",
            "destination": "DEL",
            "departure_date": "2025-11-15",
            "return_date": "2025-11-20",
            "currency": "USD"
        }
    }
}
```

**Returns:** Top 5 cheapest flights with detailed information including prices, airlines, departure/arrival times, booking links, and flight segments.

#### 2. search_airports

Search for airports by name, city, or IATA code.

**Parameters:**
- `query` (string): Search query for airports (e.g., "Mumbai airport", "BOM", "New York")

**Example JSON-RPC call:**
```json
{
    "jsonrpc": "2.0",
    "id": "airport-search-1",
    "method": "tools/call",
    "params": {
        "name": "search_airports",
        "arguments": {
            "query": "Mumbai airport"
        }
    }
}
```

**Returns:** Airport information including names, descriptions, links, and IATA codes.

#### 3. get_flight_prices

Get price trends for flights between airports over a date range.

**Parameters:**
- `source` (string): Departure airport IATA code
- `destination` (string): Arrival airport IATA code
- `start_date` (string): Start date for price search (YYYY-MM-DD)
- `end_date` (string): End date for price search (YYYY-MM-DD)
- `currency` (string, optional): Currency for pricing (default: "USD")

**Example JSON-RPC call:**
```json
{
    "jsonrpc": "2.0",
    "id": "price-trends-1",
    "method": "tools/call",
    "params": {
        "name": "get_flight_prices",
        "arguments": {
            "source": "BOM",
            "destination": "DEL",
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "currency": "USD"
        }
    }
}
```

**Returns:** Price insights and trend analysis to help find the best time to book flights.

#### 4. health_check

Simple health check to verify the MCP server is running.

**Parameters:** None

**Example JSON-RPC call:**
```json
{
    "jsonrpc": "2.0",
    "id": "health-1",
    "method": "tools/call",
    "params": {
        "name": "health_check",
        "arguments": {}
    }
}
```

**Returns:** Server status and health information.

#### 5. server_info

Get information about the MCP server.

**Parameters:** None

**Example JSON-RPC call:**
```json
{
    "jsonrpc": "2.0",
    "id": "info-1",
    "method": "tools/call",
    "params": {
        "name": "server_info",
        "arguments": {}
    }
}
```

**Returns:** Server information including available tools and version.

## Testing

### List Available Tools

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Test Flight Search

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"test-1","method":"tools/call","params":{"name":"search_flights","arguments":{"source":"BOM","destination":"DEL","departure_date":"2025-01-15"}}}'
```

### Test Health Check

```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"health-1","method":"tools/call","params":{"name":"health_check","arguments":{}}}'
```
