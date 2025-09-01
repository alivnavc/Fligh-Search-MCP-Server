from fastmcp import FastMCP, Context
import requests
import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server with more stable configuration
mcp = FastMCP("Flight Search MCP Server",stateless_http=True)

# Add a simple health check
@mcp.tool(
    name="health_check",
    description="Simple health check to verify the MCP server is running"
)
async def health_check(ctx: Context = None) -> Dict[str, Any]:
    """Simple health check endpoint"""
    try:
        if ctx:
            await ctx.info("Health check requested")
        return {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "Flight Search MCP Server is running"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Add server info
@mcp.tool(
    name="server_info",
    description="Get information about the MCP server"
)
async def server_info(ctx: Context = None) -> Dict[str, Any]:
    """Get server information"""
    try:
        if ctx:
            await ctx.info("Server info requested")
        return {
            "success": True,
            "server_name": "Flight Search MCP Server",
            "version": "1.0.0",
            "tools": [
                "search_flights",
                "search_airports", 
                "get_flight_prices",
                "health_check",
                "server_info"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Server info error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def format_datetime(iso_string):
    """Format datetime string for display"""
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")  # Example: Mar-06, 2025 | 6:20 PM
    except:
        return "N/A"

def process_flight_data(flight_data: Dict[str, Any], source: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Process and enhance flight data from SerpAPI based on actual response structure
    """
    try:
        flights = []
        
        # Get best flights from the response (primary flights)
        best_flights = flight_data.get("best_flights", [])
        
        # Get other flights if best_flights is empty
        if not best_flights:
            best_flights = flight_data.get("other_flights", [])
        
        for flight in best_flights:
            # Extract airline name from flight segments
            airline_name = "Unknown Airline"
            if flight.get("flights") and len(flight["flights"]) > 0:
                airline_name = flight["flights"][0].get("airline", "Unknown Airline")
            
            # Format price with currency
            price = flight.get("price", 0)
            price_formatted = f"${price:,.0f}" if price else "Price not available"
            
            # Format duration
            duration_minutes = flight.get("total_duration", 0)
            duration_formatted = format_duration(duration_minutes)
            
            # Generate booking link
            booking_link = generate_booking_link(flight, source, destination, departure_date, return_date)
            
            # Process flight segments according to actual SerpAPI structure
            flight_segments = []
            for segment in flight.get("flights", []):
                segment_info = {
                    "airline": segment.get("airline", "Unknown"),
                    "flight_number": segment.get("flight_number", "N/A"),
                    "departure_airport": {
                        "name": segment.get("departure_airport", {}).get("name", "Unknown"),
                        "id": segment.get("departure_airport", {}).get("id", ""),
                        "time": format_time(segment.get("departure_airport", {}).get("time", ""))
                    },
                    "arrival_airport": {
                        "name": segment.get("arrival_airport", {}).get("name", "Unknown"),
                        "id": segment.get("arrival_airport", {}).get("id", ""),
                        "time": format_time(segment.get("arrival_airport", {}).get("time", ""))
                    },
                    "duration": format_duration(segment.get("duration", 0)),
                    "aircraft": segment.get("airplane", "Unknown"),
                    "travel_class": segment.get("travel_class", ""),
                    "airline_logo": segment.get("airline_logo", ""),
                    "extensions": segment.get("extensions", []),
                    "legroom": segment.get("legroom", ""),
                    "overnight": segment.get("overnight", False),
                    "often_delayed": segment.get("often_delayed_by_over_30_min", False)
                }
                flight_segments.append(segment_info)
            
            # Process layovers if any
            layovers = []
            for layover in flight.get("layovers", []):
                layover_info = {
                    "duration": format_duration(layover.get("duration", 0)),
                    "name": layover.get("name", ""),
                    "id": layover.get("id", ""),
                    "overnight": layover.get("overnight", False)
                }
                layovers.append(layover_info)
            
            # Calculate number of stops (layovers)
            num_stops = len(layovers)
            
            # Create enhanced flight object
            enhanced_flight = {
                "airline": airline_name,
                "price": price,
                "price_formatted": price_formatted,
                "total_duration": duration_minutes,
                "duration_formatted": duration_formatted,
                "stops": num_stops,
                "departure_token": flight.get("departure_token", ""),
                "booking_token": flight.get("booking_token", ""),
                "type": flight.get("type", ""),
                "airline_logo": flight.get("airline_logo", ""),
                "extensions": flight.get("extensions", []),
                "carbon_emissions": flight.get("carbon_emissions", {}),
                "flights": flight_segments,
                "layovers": layovers,
                "booking_link": booking_link,
                "booking_info": {
                    "can_book": True,
                    "booking_method": "google_travel" if flight.get("departure_token") else "airline_website",
                    "price_currency": "USD",
                    "booking_notes": "Click the booking link to proceed with ticket purchase"
                }
            }
            
            flights.append(enhanced_flight)
        
        # Sort by price (cheapest first)
        flights.sort(key=lambda x: x.get("price", float("inf")))
        
        # Take top 5 cheapest
        top_flights = flights[:5]
        
        # Get price insights if available
        price_insights = flight_data.get("price_insights", {})
        
        return {
            "success": True,
            "flights": top_flights,
            "search_params": {
                "source": source,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "currency": "USD"
            },
            "total_flights": len(top_flights),
            "search_timestamp": datetime.now().isoformat(),
            "price_insights": price_insights,
            "booking_instructions": "Click on any booking link to proceed with ticket purchase. Links will redirect to Google Travel or airline websites for booking."
        }
        
    except Exception as e:
        logger.error(f"Error processing flight data: {e}")
        return {
            "success": False,
            "error": f"Error processing flight data: {str(e)}",
            "flights": [],
            "search_params": {
                "source": source,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "currency": "USD"
            },
            "total_flights": 0,
            "search_timestamp": datetime.now().isoformat()
        }

def format_duration(minutes: int) -> str:
    """Format duration from minutes to readable format"""
    if not minutes:
        return "Unknown"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours > 0 and remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{remaining_minutes}m"

def format_time(time_str: str) -> str:
    """Format time string to readable format"""
    if not time_str:
        return "Unknown"
    
    try:
        # Handle different time formats from SerpAPI
        if "|" in time_str:
            return time_str  # Already formatted
        elif "T" in time_str:
            # ISO format
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            return dt.strftime("%b-%d, %Y | %I:%M %p")
        else:
            return time_str
    except:
        return time_str

def generate_booking_link(flight_data: Dict[str, Any], source: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> str:
    """
    Generate a proper booking link for the flight
    
    Parameters:
    - flight_data: Flight information from SerpAPI
    - source: Departure airport code
    - destination: Arrival airport code
    - departure_date: Departure date
    - return_date: Return date (optional)
    
    Returns:
    - Booking URL that redirects to actual booking page
    """
    try:
        # Method 1: Use Google Travel booking link if available
        if flight_data.get("booking_token"):
            return f"https://www.google.com/travel/flights?tfs={flight_data['booking_token']}"
        
        # Method 2: Use departure token for Google Travel
        if flight_data.get("departure_token"):
            return f"https://www.google.com/travel/flights?tfs={flight_data['departure_token']}"
        
        # Method 3: Generate a proper Google Flights URL with parameters
        google_flights_base = "https://www.google.com/travel/flights"
        
        # Build query parameters
        params = []
        params.append(f"hl=en")
        params.append(f"curr=USD")
        params.append(f"f=0")  # One way
        params.append(f"tfs=CAEQAxoaagwIAhIIL20vMDJqNnQSCjIwMjUtMDMtMTUaGhIKMjAyNS0wMy0yMBAC")
        
        # Add source and destination
        params.append(f"q=Flights%20from%20{source}%20to%20{destination}")
        
        # Add dates
        params.append(f"d1={departure_date}")
        if return_date:
            params.append(f"d2={return_date}")
            params.append(f"f=1")  # Round trip
        
        # Join parameters
        query_string = "&".join(params)
        return f"{google_flights_base}?{query_string}"
        
        # Method 4: Generate a direct airline booking link
        airline = flight_data.get("airline", "").lower()
        flight_number = flight_data.get("flights", [{}])[0].get("flight_number", "")
        
        # Airline-specific booking URLs with proper parameters
        airline_booking_urls = {
            "air india": f"https://www.airindia.com/search?from={source}&to={destination}&date={departure_date}",
            "indigo": f"https://www.goindigo.in/search?from={source}&to={destination}&date={departure_date}",
            "spicejet": f"https://www.spicejet.com/search?from={source}&to={destination}&date={departure_date}",
            "vistara": f"https://www.airvistara.com/search?from={source}&to={destination}&date={departure_date}",
            "american airlines": f"https://www.aa.com/booking/flights?from={source}&to={destination}&date={departure_date}",
            "delta": f"https://www.delta.com/flight-search?from={source}&to={destination}&date={departure_date}",
            "united": f"https://www.united.com/ual/en/us/flight-search?from={source}&to={destination}&date={departure_date}",
            "southwest": f"https://www.southwest.com/air/booking/select.html?int=HOMEQBOMAIR&from={source}&to={destination}&date={departure_date}",
            "jetblue": f"https://www.jetblue.com/booking/flights?from={source}&to={destination}&date={departure_date}",
            "alaska": f"https://www.alaskaair.com/booking?from={source}&to={destination}&date={departure_date}"
        }
        
        # Add return date if provided
        if return_date:
            for airline_key, url in airline_booking_urls.items():
                airline_booking_urls[airline_key] = url + f"&return={return_date}"
        
        # Find matching airline
        for airline_key, booking_url in airline_booking_urls.items():
            if airline_key in airline:
                return booking_url
        
        # Method 5: Use a generic flight search engine
        if return_date:
            return f"https://www.kayak.com/flights/{source}-{destination}/{departure_date}/{return_date}"
        else:
            return f"https://www.kayak.com/flights/{source}-{destination}/{departure_date}"
        
    except Exception as e:
        logger.error(f"Error generating booking link: {e}")
        # Fallback to a simple Google Flights search
        if return_date:
            return f"https://www.google.com/travel/flights?hl=en&curr=USD&q=Flights%20from%20{source}%20to%20{destination}%20on%20{departure_date}%20return%20{return_date}"
        else:
            return f"https://www.google.com/travel/flights?hl=en&curr=USD&q=Flights%20from%20{source}%20to%20{destination}%20on%20{departure_date}"

@mcp.tool(
    name="search_flights",
    description=(
        "Search for available flights between airports using SerpAPI. "
        "Returns top 5 cheapest flights with detailed information including prices, airlines, "
        "departure/arrival times, booking links, and flight segments. "
        "Parameters: source (IATA code), destination (IATA code), departure_date (YYYY-MM-DD), "
        "return_date (optional, YYYY-MM-DD), currency (default: USD)."
    )
)
async def search_flights(
    source: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    currency: str = "USD",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Search for flights between airports using SerpAPI
    
    Parameters:
    - source: Departure airport IATA code (e.g., BOM, JFK)
    - destination: Arrival airport IATA code (e.g., DEL, LAX)
    - departure_date: Departure date in YYYY-MM-DD format
    - return_date: Return date in YYYY-MM-DD format (optional)
    - currency: Currency for pricing (default: USD)
    - ctx: MCP context for logging
    
    Returns:
    Dict containing flight search results with prices, airlines, times, and booking links
    """
    try:
        # Check if context is available before using it
        if ctx:
            await ctx.info(f"Searching flights: {source} -> {destination} on {departure_date}")
        
        # Validate inputs
        if not source or not destination or not departure_date:
            if ctx:
                await ctx.error("Missing required parameters")
            return {
                "success": False,
                "error": "Missing required parameters: source, destination, and departure_date are required.",
                "flights": []
            }
        
        # Get SerpAPI key from environment
        serpapi_key = os.getenv("SERPAPI_KEY")
        if not serpapi_key:
            if ctx:
                await ctx.error("SerpAPI key not configured")
            return {
                "success": False,
                "error": "SerpAPI key not configured. Please set SERPAPI_KEY environment variable.",
                "flights": []
            }
        
        # Prepare search parameters
        params = {
            "engine": "google_flights",
            "departure_id": source.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date,
            "currency": currency,
            "hl": "en",
            "api_key": serpapi_key
        }
        
        # Add return date if provided
        if return_date:
            params["return_date"] = return_date
            params["type"] = "1"  # Round trip
        else:
            params["type"] = "2"  # One way
        
        if ctx:
            await ctx.info(f"Making SerpAPI request with parameters: {params}")
        
        # Make direct HTTP request to SerpAPI with timeout
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        # response.raise_for_status()
        results = response.json()
        
        if ctx:
            await ctx.info(f"Received response from SerpAPI")
        
        # Check for API errors
        if "error" in results:
            if ctx:
                await ctx.error(f"SerpAPI error: {results['error']}")
            return {
                "success": False,
                "error": f"SerpAPI error: {results['error']}",
                "flights": []
            }
        
        # Extract best flights from results
        best_flights = results.get("best_flights", [])
        
        # Process and enhance flight data using the new processing function
        if best_flights:
            return process_flight_data(results, source, destination, departure_date, return_date)
        
        # If no flights found, return error instead of mock data
        if ctx:
            await ctx.warning("No flights found in SerpAPI response")
        return {
            "success": False,
            "error": "No flights found for the specified route and dates. Please try different dates or airports.",
            "flights": [],
            "search_params": {
                "source": source,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "currency": currency
            },
            "total_flights": 0,
            "search_timestamp": datetime.now().isoformat()
        }
        
    except requests.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        if ctx:
            await ctx.error(f"{error_msg}\n{traceback.format_exc()}")
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg,
            "flights": [],
            "search_params": {
                "source": source,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "currency": currency
            }
        }
    except Exception as e:
        error_msg = f"Error searching flights: {str(e)}"
        if ctx:
            await ctx.error(f"{error_msg}\n{traceback.format_exc()}")
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg,
            "flights": [],
            "search_params": {
                "source": source,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "currency": currency
            }
        }



@mcp.tool(
    name="search_airports",
    description=(
        "Search for airports by name, city, or IATA code using SerpAPI. "
        "Returns airport information including names, descriptions, links, and IATA codes. "
        "Useful for finding airport codes when planning flights. "
        "Parameters: query (airport name, city, or IATA code)."
    )
)
async def search_airports(
    query: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Search for airports by name, city, or IATA code
    
    Parameters:
    - query: Search query for airports
    - ctx: MCP context for logging
    
    Returns:
    Dict containing airport search results
    """
    try:
        if ctx:
            await ctx.info(f"Searching airports for query: {query}")
        
        serpapi_key = os.getenv("SERPAPI_KEY")
        if not serpapi_key:
            if ctx:
                await ctx.error("SerpAPI key not configured")
            return {
                "success": False,
                "error": "SerpAPI key not configured. Please set SERPAPI_KEY environment variable.",
                "airports": []
            }
        
        # Check if query is a 3-letter IATA code
        if len(query) == 3 and query.isalpha():
            # Use google_flights engine for IATA codes
            params = {
                "engine": "google_flights",
                "departure_id": query.upper(),
                "arrival_id": "",
                "outbound_date": "2025-12-01",
                "currency": "USD",
                "hl": "en",
                "api_key": serpapi_key
            }
        else:
            # Use Google search for city names and other queries
            params = {
                "engine": "google",
                "q": f"{query} airport IATA code information",
                "api_key": serpapi_key
            }
        
        if ctx:
            await ctx.info(f"Searching for airports: {query}")
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        
        # Return the complete SerpAPI response as is
        if ctx:
            await ctx.info(f"Returning complete SerpAPI response")
        
        return {
            "success": True,
            "serpapi_response": results,
            "query": query,
            "search_timestamp": datetime.now().isoformat()
        }
        
    except requests.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        await ctx.error(f"{error_msg}\n{traceback.format_exc()}")
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg,
            "airports": [],
            "query": query
        }
    except Exception as e:
        error_msg = f"Error searching airports: {str(e)}"
        await ctx.error(f"{error_msg}\n{traceback.format_exc()}")
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg,
            "airports": [],
            "query": query
        }

@mcp.tool(
    name="get_flight_prices",
    description=(
        "Get price trends for flights between airports over a date range using SerpAPI. "
        "Returns price insights and trend analysis to help users find the best time to book flights. "
        "Parameters: source (IATA code), destination (IATA code), start_date (YYYY-MM-DD), "
        "end_date (YYYY-MM-DD), currency (default: USD)."
    )
)
async def get_flight_prices(
    source: str,
    destination: str,
    start_date: str,
    end_date: str,
    currency: str = "USD",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get price trends for flights between airports over a date range
    
    Parameters:
    - source: Departure airport IATA code
    - destination: Arrival airport IATA code
    - start_date: Start date for price search (YYYY-MM-DD)
    - end_date: End date for price search (YYYY-MM-DD)
    - currency: Currency for pricing (default: USD)
    - ctx: MCP context for logging
    
    Returns:
    Dict containing price trend information
    """
    try:
        if ctx:
            await ctx.info(f"Getting price trends: {source} -> {destination} from {start_date} to {end_date}")
        
        serpapi_key = os.getenv("SERPAPI_KEY")
        if not serpapi_key:
            if ctx:
                await ctx.error("SerpAPI key not configured")
            return {
                "success": False,
                "error": "SerpAPI key not configured. Please set SERPAPI_KEY environment variable.",
                "price_trends": []
            }
        
        # Search for price trends
        params = {
            "engine": "google_flights",
            "departure_id": source.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": start_date,
            "return_date": end_date,
            "currency": currency,
            "hl": "en",
            "api_key": serpapi_key
        }
        
        if ctx:
            await ctx.info(f"Searching for price trends")
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        
        # Return the complete SerpAPI response as is
        if ctx:
            await ctx.info(f"Returning complete SerpAPI response")
        
        return {
            "success": True,
            "serpapi_response": results,
            "search_params": {
                "source": source,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "currency": currency
            },
            "search_timestamp": datetime.now().isoformat()
        }
        
    except requests.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        await ctx.error(f"{error_msg}\n{traceback.format_exc()}")
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg,
            "price_trends": [],
            "search_params": {
                "source": source,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "currency": currency
            }
        }
    except Exception as e:
        error_msg = f"Error getting flight prices: {str(e)}"
        await ctx.error(f"{error_msg}\n{traceback.format_exc()}")
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg,
            "price_trends": [],
            "search_params": {
                "source": source,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "currency": currency
            }
        }

def main():
    """Main function to run the MCP server"""
    logger.info("Starting Flight Search MCP Server...")
    logger.info("Server will be available on port 8001")
    logger.info("Tools available:")
    logger.info("   - search_flights: Search for available flights")
    logger.info("   - search_airports: Search for airports")
    logger.info("   - get_flight_prices: Get price trends")
    
    try:
        # Use simpler configuration to avoid connection issues
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8001,
            path="/mcp",
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Flight Search MCP Server shutdown complete")

if __name__ == "__main__":
    main() 