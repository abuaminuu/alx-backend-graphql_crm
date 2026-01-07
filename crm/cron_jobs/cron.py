"""
crm/cron.py
Heartbeat and maintenance cron jobs for CRM application
Using gql library for GraphQL queries
"""

######
import requests
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Update low stock products and log the updates
def update_low_stock():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "/tmp/low_stock_updates_log.txt"

    mutation = """
    mutation {
      updateLowStockProducts {
        updatedProducts {
          id
          name
          stock
        }
        message
      }
    }
    """

    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": mutation},
            timeout=10
        )
        data = response.json()
        updates = data.get("data", {}).get("updateLowStockProducts", {})

        with open(log_file, "a") as f:
            f.write(f"{timestamp} - {updates.get('message')}\n")
            for product in updates.get("updatedProducts", []):
                f.write(f"{timestamp} - {product['name']} restocked to {product['stock']}\n")

    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{timestamp} - Error: {e}\n")

# Log CRM heartbeat
def log_crm_heartbeat():
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive\n"

    # Append to heartbeat log
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(log_message)

    # Optional: query GraphQL hello field to verify endpoint
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5
        )
        data = response.json()
        hello_value = data.get("data", {}).get("hello", "")
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{timestamp} GraphQL hello response: {hello_value}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{timestamp} GraphQL check failed: {e}\n")
######
import os
import sys
from datetime import datetime
import logging
import json
from typing import Dict, Any
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


# Import gql library for GraphQL queries
try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
    HAS_GQL = True
except ImportError:
    HAS_GQL = False

# Setup logging
def setup_cron_logger():
    """Configure logger for cron jobs"""
    log_file = '/tmp/crm_heartbeat_log.txt'
    
    # Create logger
    logger = logging.getLogger('crm_cron')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler (append mode)
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    
    # Formatter with timestamp
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d/%m/%Y-%H:%M:%S')
    file_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(file_handler)
    
    # Also log to console for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def create_graphql_client() -> Client:
    """
    Create and return a GraphQL client using gql library
    """
    try:
        # Configure HTTP transport for GraphQL
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            use_json=True,
            headers={
                "Content-Type": "application/json",
            },
            verify=True,
            retries=3,
        )
        
        # Create client
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        
        return client
        
    except Exception as e:
        raise Exception(f"Failed to create GraphQL client: {str(e)}")

def query_graphql_hello() -> Dict[str, Any]:
    """
    Query the GraphQL hello field to verify endpoint responsiveness
    Returns health status and response time
    """
    if not HAS_GQL:
        return {"status": "skipped", "reason": "gql library not installed"}
    
    import time
    
    try:
        start_time = time.time()
        
        # Create GraphQL client
        client = create_graphql_client()
        
        # Define the GraphQL query for hello field
        query_string = """
        query {
          hello
        }
        """
        
        # Execute query
        query = gql(query_string)
        result = client.execute(query)
        
        response_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        # Check if hello field exists in response
        if 'hello' in result:
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "message": result['hello']
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "error": "hello field not in response",
                "response": result
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }

def log_crm_heartbeat():
    """
    Heartbeat function that runs every 5 minutes
    Logs CRM health status including GraphQL endpoint check using gql library
    """
    logger = setup_cron_logger()
    
    # Get current timestamp
    current_time = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Basic heartbeat message
        base_message = f"{current_time} CRM is alive"
        
        # Check GraphQL endpoint using gql library
        graphql_status = query_graphql_hello()
        
        if graphql_status["status"] == "healthy":
            # Add GraphQL response time and message to log
            response_time = graphql_status.get("response_time_ms", "N/A")
            hello_message = graphql_status.get("message", "")
            full_message = f"{base_message} | GraphQL: OK ({response_time}ms) - '{hello_message}'"
            
        elif graphql_status["status"] == "skipped":
            full_message = f"{base_message} | GraphQL: Check skipped - install gql library"
            
        else:
            error_msg = graphql_status.get("error", "Unknown error")
            error_type = graphql_status.get("error_type", "")
            
            if error_type:
                error_msg = f"{error_type}: {error_msg}"
                
            full_message = f"{base_message} | GraphQL: DOWN - {error_msg}"
        
        # Log the heartbeat
        logger.info(full_message)
        
        # Optional: Log system info (without breaking the required format)
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            logger.info(f"System Info | CPU: {cpu_percent}% | Memory: {memory.percent}%")
        except ImportError:
            pass  # psutil not installed, skip system info
            
        return True
        
    except Exception as e:
        error_message = f"{current_time} CRM heartbeat FAILED: {str(e)}"
        logger.error(error_message)
        return False

# Alternative GraphQL query methods for flexibility

def query_graphql_schema():
    """
    Alternative method: Query GraphQL schema to verify endpoint
    This doesn't require a specific 'hello' field
    """
    if not HAS_GQL:
        return {"status": "skipped", "reason": "gql library not installed"}
    
    import time
    
    try:
        start_time = time.time()
        
        # Create GraphQL client
        client = create_graphql_client()
        
        # Query the schema (works even without hello field)
        query_string = """
        query {
          __schema {
            queryType {
              name
            }
          }
        }
        """
        
        # Execute query
        query = gql(query_string)
        result = client.execute(query)
        
        response_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        if '__schema' in result:
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "schema_exists": True
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "error": "Schema query failed",
                "response": result
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }

def test_all_graphql_endpoints():
    """
    Comprehensive GraphQL endpoint testing
    Tries multiple queries to ensure endpoint is fully responsive
    """
    logger = setup_cron_logger()
    
    tests = [
        ("Hello field", query_graphql_hello),
        ("Schema query", query_graphql_schema),
    ]
    
    all_passed = True
    results = []
    
    for test_name, test_function in tests:
        result = test_function()
        results.append((test_name, result))
        
        if result["status"] != "healthy":
            all_passed = False
    
    # Log results
    current_time = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    if all_passed:
        logger.info(f"{current_time} All GraphQL tests PASSED")
    else:
        logger.warning(f"{current_time} Some GraphQL tests FAILED")
        
    for test_name, result in results:
        status = "✓" if result["status"] == "healthy" else "✗"
        logger.info(f"  {status} {test_name}: {result.get('message', result.get('error', 'No details'))}")
    
    return all_passed

# Additional utility function for manual testing
def manual_graphql_test():
    """
    Manual test function that can be called from Django shell
    """
    print("Testing GraphQL endpoint with gql library...")
    
    # Check if gql is installed
    if not HAS_GQL:
        print("ERROR: gql library not installed.")
        print("Install it with: pip install gql")
        return False
    
    try:
        # Test 1: Hello field
        print("\n1. Testing hello field query:")
        hello_result = query_graphql_hello()
        print(f"   Status: {hello_result['status']}")
        
        if hello_result['status'] == 'healthy':
            print(f"   Response: {hello_result.get('message', 'No message')}")
            print(f"   Time: {hello_result.get('response_time_ms', 'N/A')}ms")
        else:
            print(f"   Error: {hello_result.get('error', 'Unknown error')}")
        
        # Test 2: Schema query (fallback)
        print("\n2. Testing schema query:")
        schema_result = query_graphql_schema()
        print(f"   Status: {schema_result['status']}")
        
        if schema_result['status'] == 'healthy':
            print(f"   Schema accessible: Yes")
            print(f"   Time: {schema_result.get('response_time_ms', 'N/A')}ms")
        else:
            print(f"   Error: {schema_result.get('error', 'Unknown error')}")
        
        return hello_result['status'] == 'healthy' or schema_result['status'] == 'healthy'
        
    except Exception as e:
        print(f"ERROR during test: {str(e)}")
        return False
