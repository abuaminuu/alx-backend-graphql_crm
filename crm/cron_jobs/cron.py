import os
import sys
from datetime import datetime
import logging
import json
from typing import Dict, Any

# REQUIRED: gql imports at the TOP LEVEL (not inside try-except)
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

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
            
        else:
            error_msg = graphql_status.get("error", "Unknown error")
            error_type = graphql_status.get("error_type", "")
            
            if error_type:
                error_msg = f"{error_type}: {error_msg}"
                
            full_message = f"{base_message} | GraphQL: DOWN - {error_msg}"
        
        # Log the heartbeat
        logger.info(full_message)
        
        return True
        
    except Exception as e:
        error_message = f"{current_time} CRM heartbeat FAILED: {str(e)}"
        logger.error(error_message)
        return False

"""
crm/cron.py
Heartbeat and maintenance cron jobs for CRM application
"""