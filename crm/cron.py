"""
crm/cron.py
Heartbeat and maintenance cron jobs for CRM application
"""
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os
import sys
from datetime import datetime
import logging
import json
from typing import Dict, Any

# Optional: GraphQL health check imports
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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

def check_graphql_endpoint() -> Dict[str, Any]:
    """
    Check if GraphQL endpoint is responsive
    Returns health status and response time
    """
    if not HAS_REQUESTS:
        return {"status": "skipped", "reason": "requests not installed"}
    
    try:
        import time
        start_time = time.time()
        
        # Simple GraphQL query to check health
        query = """
        query {
          __schema {
            types {
              name
            }
          }
        }
        """
        
        # Alternative: Query your hello field if it exists
        # query = "{ hello }"
        
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=5  # 5 second timeout
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        if response.status_code == 200:
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "status_code": response.status_code
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "status_code": response.status_code,
                "error": f"HTTP {response.status_code}"
            }
            
    except requests.exceptions.ConnectionError:
        return {"status": "unhealthy", "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "unhealthy", "error": "Timeout"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def log_crm_heartbeat():
    """
    Heartbeat function that runs every 5 minutes
    Logs CRM health status including GraphQL endpoint check
    """
    logger = setup_cron_logger()
    
    # Get current timestamp
    current_time = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Basic heartbeat message
        base_message = f"{current_time} CRM is alive"
        
        # Check GraphQL endpoint if requests is available
        graphql_status = check_graphql_endpoint()
        
        if graphql_status["status"] == "healthy":
            # Add GraphQL response time to log
            response_time = graphql_status.get("response_time_ms", "N/A")
            full_message = f"{base_message} | GraphQL: OK ({response_time}ms)"
        elif graphql_status["status"] == "skipped":
            full_message = f"{base_message} | GraphQL: Check skipped (install requests)"
        else:
            error_msg = graphql_status.get("error", "Unknown error")
            full_message = f"{base_message} | GraphQL: DOWN - {error_msg}"
        
        # Log the heartbeat
        logger.info(full_message)
        
        # Optional: Log additional system info
        log_system_info(logger)
        
        return True
        
    except Exception as e:
        error_message = f"{current_time} CRM heartbeat FAILED: {str(e)}"
        logger.error(error_message)
        return False

def log_system_info(logger: logging.Logger):
    """Log additional system information (optional)"""
    try:
        import psutil
        import django
        
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Django info
        django_version = django.get_version()
        
        logger.info(f"System Info | CPU: {cpu_percent}% | Memory: {memory.percent}% | Django: {django_version}")
        
    except ImportError:
        # psutil not installed, skip system info
        pass
    except Exception:
        # Silent fail for optional system info
        pass

# Additional cron jobs can be added below

def check_database_health():
    """Optional: Check database connectivity"""
    logger = setup_cron_logger()
    
    try:
        from django.db import connection
        from django.db.utils import OperationalError
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            logger.info("Database connection: OK")
            return True
        else:
            logger.error("Database connection: Unexpected response")
            return False
            
    except OperationalError as e:
        logger.error(f"Database connection FAILED: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Database check error: {str(e)}")
        return False

def cleanup_temp_files():
    """Optional: Clean up temporary files older than 7 days"""
    logger = setup_cron_logger()
    
    try:
        import os
        import time
        from datetime import datetime, timedelta
        
        temp_dir = '/tmp'
        cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days in seconds
        deleted_count = 0
        
        for filename in os.listdir(temp_dir):
            if filename.startswith('crm_') or filename.startswith('payment_'):
                filepath = os.path.join(temp_dir, filename)
                
                if os.path.isfile(filepath):
                    file_mtime = os.path.getmtime(filepath)
                    
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old temporary files")
            
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")

"""
crm/cron.py
Cron jobs for CRM application including low-stock updates
"""

from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import logging
import sys

def setup_low_stock_logger():
    """Setup logger for low-stock updates"""
    logger = logging.getLogger('low_stock_cron')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler for low-stock updates
    file_handler = logging.FileHandler('/tmp/low_stock_updates_log.txt', mode='a')
    file_handler.setLevel(logging.INFO)
    
    # Formatter with timestamp
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Also log to console for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def update_low_stock():
    """
    Cron job that runs every 12 hours
    Executes GraphQL mutation to update low-stock products
    """
    logger = setup_low_stock_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info("=" * 60)
    logger.info(f"LOW STOCK UPDATE STARTED - {timestamp}")
    logger.info("=" * 60)
    
    try:
        # Create GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            use_json=True,
            headers={"Content-Type": "application/json"},
            verify=True,
            retries=3,
        )
        
        client = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )
        
        # Define the GraphQL mutation
        mutation_string = """
        mutation UpdateLowStock($increment: Int, $threshold: Int) {
          updateLowStockProducts(
            increment: $increment, 
            threshold: $threshold
          ) {
            updatedProducts {
              id
              name
              stock
              price
            }
            message
            count
          }
        }
        """
        
        # Execute mutation with variables
        mutation = gql(mutation_string)
        
        # You can customize these values
        variables = {
            "increment": 10,      # Add 10 to stock
            "threshold": 10       # Products with stock < 10
        }
        
        result = client.execute(mutation, variable_values=variables)
        
        # Extract data from result
        mutation_result = result.get('updateLowStockProducts', {})
        updated_products = mutation_result.get('updatedProducts', [])
        message = mutation_result.get('message', 'No message returned')
        count = mutation_result.get('count', 0)
        
        # Log the result
        logger.info(f"Mutation Result: {message}")
        logger.info(f"Products Updated: {count}")
        
        if count > 0:
            logger.info("-" * 40)
            logger.info("Updated Products:")
            logger.info("-" * 40)
            
            for product in updated_products:
                logger.info(f"  • {product['name']}: Now has {product['stock']} units (${product['price']})")
        
        logger.info("=" * 60)
        logger.info(f"LOW STOCK UPDATE COMPLETED - {timestamp}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        error_message = f"ERROR during low-stock update: {str(e)}"
        logger.error(error_message)
        return False

# Alternative: Simple version using requests library
def update_low_stock_simple():
    """
    Alternative implementation using requests library
    """
    import requests
    import json
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "/tmp/low_stock_updates_log.txt"
    
    # GraphQL mutation
    mutation = """
    mutation {
      updateLowStockProducts {
        updatedProducts {
          id
          name
          stock
        }
        message
        count
      }
    }
    """
    
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": mutation},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Check for GraphQL errors
        if 'errors' in data:
            error_msg = data['errors'][0]['message'] if data['errors'] else 'Unknown error'
            with open(log_file, 'a') as f:
                f.write(f"{timestamp} - GraphQL Error: {error_msg}\n")
            return False
        
        # Extract mutation result
        result = data.get('data', {}).get('updateLowStockProducts', {})
        message = result.get('message', '')
        count = result.get('count', 0)
        updated_products = result.get('updatedProducts', [])
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} - {message}\n")
            
            if count > 0:
                f.write(f"{timestamp} - Updated {count} product(s):\n")
                for product in updated_products:
                    f.write(f"{timestamp} - • {product['name']}: stock = {product['stock']}\n")
            else:
                f.write(f"{timestamp} - No products needed restocking\n")
        
        return True
        
    except requests.exceptions.ConnectionError:
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} - ERROR: Cannot connect to GraphQL endpoint\n")
        return False
    except requests.exceptions.Timeout:
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} - ERROR: Request timeout\n")
        return False
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"{timestamp} - ERROR: {str(e)}\n")
        return False
