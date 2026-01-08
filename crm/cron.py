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
