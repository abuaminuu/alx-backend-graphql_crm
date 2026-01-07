#!/usr/bin/env python3
"""
send_order_reminders.py
Queries GraphQL API for orders from the last 7 days
and logs reminders for pending orders.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the project to Python path (UPDATE THIS PATH)
project_path = "/home/abuaminuu/machine/alx_travel_app_0x02"
sys.path.insert(0, project_path)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

# Now import Django modules
import django
django.setup()

# Import your GraphQL client library
try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
    HAS_GQL = True
except ImportError:
    HAS_GQL = False
    print("Warning: gql library not installed. Install with: pip install gql")
    sys.exit(1)

# Configuration
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"
DAYS_BACK = 7

def setup_logging():
    """Configure logging to both file and console"""
    # File logging
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_graphql_client() -> Client:
    """Create and return a GraphQL client"""
    # Configure HTTP transport
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
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
        fetch_schema_from_transport=False,
    )
    
    return client

def query_recent_orders(client: Client, days_back: int = 7) -> List[Dict[str, Any]]:
    """
    Query GraphQL API for orders from the last N days
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Define the GraphQL query
    query_string = """
    query GetRecentOrders($startDate: String!, $endDate: String!) {
      allOrders(
        where: {
          orderDate_Gte: $startDate,
          orderDate_Lte: $endDate,
          status: "pending"
        },
        orderBy: "-orderDate"
      ) {
        edges {
          node {
            id
            orderDate
            status
            totalAmount
            customer {
              id
              name
              email
              phone
            }
            products {
              name
              price
            }
          }
        }
      }
    }
    """
    
    # Prepare variables
    variables = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
    }
    
    try:
        # Execute query
        query = gql(query_string)
        result = client.execute(query, variable_values=variables)
        
        # Extract orders from result
        orders = []
        if result and 'allOrders' in result:
            for edge in result['allOrders']['edges']:
                orders.append(edge['node'])
        
        return orders
        
    except Exception as e:
        logging.error(f"GraphQL query failed: {str(e)}")
        raise

def process_order_reminders(orders: List[Dict[str, Any]], logger: logging.Logger):
    """
    Process orders and log reminders
    """
    logger.info("=" * 60)
    logger.info(f"ORDER REMINDERS PROCESSING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    if not orders:
        logger.info("No pending orders found from the last 7 days.")
        return
    
    logger.info(f"Found {len(orders)} pending order(s) from the last 7 days:")
    logger.info("-" * 60)
    
    for i, order in enumerate(orders, 1):
        customer = order.get('customer', {})
        order_date = order.get('orderDate', 'Unknown')
        order_id = order.get('id', 'Unknown')
        
        # Log order details
        logger.info(f"Order #{i}:")
        logger.info(f"  ID: {order_id}")
        logger.info(f"  Date: {order_date}")
        logger.info(f"  Status: {order.get('status', 'Unknown')}")
        logger.info(f"  Total: ${order.get('totalAmount', 0)}")
        logger.info(f"  Customer: {customer.get('name', 'Unknown')}")
        logger.info(f"  Email: {customer.get('email', 'No email')}")
        logger.info(f"  Phone: {customer.get('phone', 'No phone')}")
        
        # List products
        products = order.get('products', [])
        if products:
            logger.info("  Products:")
            for product in products:
                logger.info(f"    - {product.get('name')}: ${product.get('price')}")
        
        logger.info("-" * 40)
        
        # TODO: In a real system, you would send email/SMS reminders here
        # send_email_reminder(customer['email'], order_id, order_date)
        # send_sms_reminder(customer['phone'], order_id)
    
    logger.info(f"Total: {len(orders)} order(s) needing reminders")
    logger.info("=" * 60)

def alternative_django_orm_method():
    """
    Alternative method using Django ORM directly (if GraphQL is not working)
    """
    try:
        from crm.models import Order, Customer
        from django.utils import timezone
        from datetime import timedelta
        
        logger = logging.getLogger()
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=DAYS_BACK)
        
        # Query using Django ORM
        recent_orders = Order.objects.filter(
            order_date__gte=start_date,
            order_date__lte=end_date,
            status='pending'
        ).select_related('customer').prefetch_related('products')
        
        if recent_orders.exists():
            logger.info(f"Found {recent_orders.count()} pending order(s) via Django ORM:")
            
            for order in recent_orders:
                logger.info(f"Order ID: {order.id}")
                logger.info(f"Customer: {order.customer.name}")
                logger.info(f"Email: {order.customer.email}")
                logger.info(f"Date: {order.order_date}")
                logger.info("-" * 40)
        else:
            logger.info("No pending orders found via Django ORM.")
            
    except Exception as e:
        logger.error(f"Django ORM method failed: {str(e)}")

def main():
    """Main execution function"""
    logger = setup_logging()
    
    logger.info("Starting order reminder processing...")
    
    try:
        # Method 1: GraphQL API (Primary)
        if HAS_GQL:
            logger.info(f"Connecting to GraphQL endpoint: {GRAPHQL_ENDPOINT}")
            
            # Create GraphQL client
            client = get_graphql_client()
            
            # Query for recent orders
            orders = query_recent_orders(client, DAYS_BACK)
            
            # Process and log reminders
            process_order_reminders(orders, logger)
            
        else:
            # Method 2: Django ORM fallback
            logger.warning("gql library not available, falling back to Django ORM")
            alternative_django_orm_method()
        
        # Print success message to console
        print("Order reminders processed!")
        
        logger.info("Order reminder processing completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in order reminder processing: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
