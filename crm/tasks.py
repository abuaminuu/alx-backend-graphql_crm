"""
crm/tasks.py
Celery tasks for CRM application
"""

import os
import sys
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Any
import requests
from celery import shared_task
from celery.utils.log import get_task_logger

# Add project to path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

# Import GraphQL client
try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
    HAS_GQL = True
except ImportError:
    HAS_GQL = False

logger = get_task_logger(__name__)

def setup_report_logger():
    """Setup logger for CRM reports"""
    log_file = '/tmp/crm_report_log.txt'
    
    # Create logger
    report_logger = logging.getLogger('crm_report')
    report_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    report_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    report_logger.addHandler(file_handler)
    
    return report_logger

def create_graphql_client() -> Client:
    """Create GraphQL client"""
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        use_json=True,
        headers={"Content-Type": "application/json"},
        verify=True,
        retries=3,
        timeout=30,
    )
    
    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )
    
    return client

# based on tasks requirements
def generate_crm_report():
    report_logger = setup_report_logger()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        logger.info(f"Starting CRM report generation at {timestamp}")
        report_logger.info("=" * 70)
        report_logger.info(f"CRM WEEKLY REPORT - {timestamp}")
        report_logger.info("=" * 70)
        
        if not HAS_GQL:
            error_msg = "gql library not installed. Install with: pip install gql"
            report_logger.error(f"ERROR: {error_msg}")
            raise ImportError(error_msg)
        
        # Calculate date range (last 7 days if not specified)
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Format dates for GraphQL query
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Create GraphQL client
        client = create_graphql_client()
        
        # Query 1: Get customer statistics
        customer_query = gql("""
            query GetCustomerStats {
              allCustomers {
                totalCount
              }
            }
        """)
        
        # Query 2: Get order statistics with revenue
        order_query = gql("""
            query GetOrderStats($startDate: String!, $endDate: String!) {
              allOrders(
                where: {
                  orderDate_Gte: $startDate,
                  orderDate_Lte: $endDate
                }
              ) {
                totalCount
                edges {
                  node {
                    totalAmount
                    orderDate
                    customer {
                      name
                      email
                    }
                    products {
                      name
                      price
                    }
                  }
                }
              }
            }
        """)
        
        # Execute queries
        customer_result = client.execute(customer_query)
        order_result = client.execute(order_query, variable_values={
            "startDate": start_date_str,
            "endDate": end_date_str
        })
        
        # Parse results
        total_customers = customer_result.get('allCustomers', {}).get('totalCount', 0)
        total_orders = order_result.get('allOrders', {}).get('totalCount', 0)
        
        # Calculate total revenue
        total_revenue = 0
        orders = order_result.get('allOrders', {}).get('edges', [])
        top_customers = {}
        
        for order in orders:
            node = order.get('node', {})
            total_revenue += float(node.get('totalAmount', 0))
            
            # Track top customers
            customer = node.get('customer', {})
            customer_email = customer.get('email', 'Unknown')
            customer_name = customer.get('name', 'Unknown')
            
            if customer_email in top_customers:
                top_customers[customer_email]['total_spent'] += float(node.get('totalAmount', 0))
                top_customers[customer_email]['order_count'] += 1
            else:
                top_customers[customer_email] = {
                    'name': customer_name,
                    'total_spent': float(node.get('totalAmount', 0)),
                    'order_count': 1
                }
        
        # Format revenue
        formatted_revenue = f"${total_revenue:,.2f}"
        
        # Log the main report
        report_logger.info(f"Report Period: {start_date_str} to {end_date_str}")
        report_logger.info(f"Total Customers: {total_customers}")
        report_logger.info(f"Total Orders: {total_orders}")
        report_logger.info(f"Total Revenue: {formatted_revenue}")
        
        # Calculate averages
        if total_orders > 0:
            avg_order_value = total_revenue / total_orders
            report_logger.info(f"Average Order Value: ${avg_order_value:,.2f}")
        
        # Top customers section
        if top_customers:
            report_logger.info("-" * 70)
            report_logger.info("TOP 5 CUSTOMERS BY REVENUE:")
            report_logger.info("-" * 70)
            
            sorted_customers = sorted(
                top_customers.items(),
                key=lambda x: x[1]['total_spent'],
                reverse=True
            )[:5]
            
            for i, (email, data) in enumerate(sorted_customers, 1):
                report_logger.info(f"{i}. {data['name']} ({email}):")
                report_logger.info(f"   • Total Spent: ${data['total_spent']:,.2f}")
                report_logger.info(f"   • Orders: {data['order_count']}")
        
        # Product analysis (optional)
        report_logger.info("-" * 70)
        report_logger.info("PRODUCT ANALYSIS:")
        report_logger.info("-" * 70)
        
        # You could add product-specific queries here
        product_query = gql("""
            query GetTopProducts {
              allProducts(orderBy: "-price", first: 5) {
                edges {
                  node {
                    name
                    price
                    stock
                  }
                }
              }
            }
        """)
        
        try:
            product_result = client.execute(product_query)
            products = product_result.get('allProducts', {}).get('edges', [])
            
            if products:
                report_logger.info("Top 5 Products by Price:")
                for product in products:
                    node = product.get('node', {})
                    report_logger.info(f"  • {node.get('name')}: ${node.get('price')} (Stock: {node.get('stock')})")
            else:
                report_logger.info("No product data available")
                
        except Exception as e:
            report_logger.info(f"Product analysis skipped: {str(e)}")
        
        # Report summary
        report_logger.info("=" * 70)
        report_logger.info("REPORT SUMMARY")
        report_logger.info(f"Generated at: {timestamp}")
        report_logger.info(f"Period: {start_date_str} to {end_date_str}")
        report_logger.info(f"Total: {total_customers} customers, {total_orders} orders, {formatted_revenue} revenue")
        report_logger.info("=" * 70)
        
        # Return result for potential API consumption
        return {
            'timestamp': timestamp,
            'period': {'start': start_date_str, 'end': end_date_str},
            'metrics': {
                'total_customers': total_customers,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'avg_order_value': avg_order_value if total_orders > 0 else 0
            },
            'top_customers': list(sorted_customers)[:5] if top_customers else []
        }
        
    except Exception as e:
        error_msg = f"Failed to generate CRM report: {str(e)}"
        logger.error(error_msg)
        report_logger.error(f"ERROR: {error_msg}")
        
        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            report_logger.error("Max retries exceeded. Report generation failed.")
        
        return {'error': str(e), 'timestamp': timestamp}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_crm_report(self, start_date=None, end_date=None):
    """
    Generate weekly CRM report using GraphQL queries
    """
    report_logger = setup_report_logger()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        logger.info(f"Starting CRM report generation at {timestamp}")
        report_logger.info("=" * 70)
        report_logger.info(f"CRM WEEKLY REPORT - {timestamp}")
        report_logger.info("=" * 70)
        
        if not HAS_GQL:
            error_msg = "gql library not installed. Install with: pip install gql"
            report_logger.error(f"ERROR: {error_msg}")
            raise ImportError(error_msg)
        
        # Calculate date range (last 7 days if not specified)
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Format dates for GraphQL query
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Create GraphQL client
        client = create_graphql_client()
        
        # Query 1: Get customer statistics
        customer_query = gql("""
            query GetCustomerStats {
              allCustomers {
                totalCount
              }
            }
        """)
        
        # Query 2: Get order statistics with revenue
        order_query = gql("""
            query GetOrderStats($startDate: String!, $endDate: String!) {
              allOrders(
                where: {
                  orderDate_Gte: $startDate,
                  orderDate_Lte: $endDate
                }
              ) {
                totalCount
                edges {
                  node {
                    totalAmount
                    orderDate
                    customer {
                      name
                      email
                    }
                    products {
                      name
                      price
                    }
                  }
                }
              }
            }
        """)
        
        # Execute queries
        customer_result = client.execute(customer_query)
        order_result = client.execute(order_query, variable_values={
            "startDate": start_date_str,
            "endDate": end_date_str
        })
        
        # Parse results
        total_customers = customer_result.get('allCustomers', {}).get('totalCount', 0)
        total_orders = order_result.get('allOrders', {}).get('totalCount', 0)
        
        # Calculate total revenue
        total_revenue = 0
        orders = order_result.get('allOrders', {}).get('edges', [])
        top_customers = {}
        
        for order in orders:
            node = order.get('node', {})
            total_revenue += float(node.get('totalAmount', 0))
            
            # Track top customers
            customer = node.get('customer', {})
            customer_email = customer.get('email', 'Unknown')
            customer_name = customer.get('name', 'Unknown')
            
            if customer_email in top_customers:
                top_customers[customer_email]['total_spent'] += float(node.get('totalAmount', 0))
                top_customers[customer_email]['order_count'] += 1
            else:
                top_customers[customer_email] = {
                    'name': customer_name,
                    'total_spent': float(node.get('totalAmount', 0)),
                    'order_count': 1
                }
        
        # Format revenue
        formatted_revenue = f"${total_revenue:,.2f}"
        
        # Log the main report
        report_logger.info(f"Report Period: {start_date_str} to {end_date_str}")
        report_logger.info(f"Total Customers: {total_customers}")
        report_logger.info(f"Total Orders: {total_orders}")
        report_logger.info(f"Total Revenue: {formatted_revenue}")
        
        # Calculate averages
        if total_orders > 0:
            avg_order_value = total_revenue / total_orders
            report_logger.info(f"Average Order Value: ${avg_order_value:,.2f}")
        
        # Top customers section
        if top_customers:
            report_logger.info("-" * 70)
            report_logger.info("TOP 5 CUSTOMERS BY REVENUE:")
            report_logger.info("-" * 70)
            
            sorted_customers = sorted(
                top_customers.items(),
                key=lambda x: x[1]['total_spent'],
                reverse=True
            )[:5]
            
            for i, (email, data) in enumerate(sorted_customers, 1):
                report_logger.info(f"{i}. {data['name']} ({email}):")
                report_logger.info(f"   • Total Spent: ${data['total_spent']:,.2f}")
                report_logger.info(f"   • Orders: {data['order_count']}")
        
        # Product analysis (optional)
        report_logger.info("-" * 70)
        report_logger.info("PRODUCT ANALYSIS:")
        report_logger.info("-" * 70)
        
        # You could add product-specific queries here
        product_query = gql("""
            query GetTopProducts {
              allProducts(orderBy: "-price", first: 5) {
                edges {
                  node {
                    name
                    price
                    stock
                  }
                }
              }
            }
        """)
        
        try:
            product_result = client.execute(product_query)
            products = product_result.get('allProducts', {}).get('edges', [])
            
            if products:
                report_logger.info("Top 5 Products by Price:")
                for product in products:
                    node = product.get('node', {})
                    report_logger.info(f"  • {node.get('name')}: ${node.get('price')} (Stock: {node.get('stock')})")
            else:
                report_logger.info("No product data available")
                
        except Exception as e:
            report_logger.info(f"Product analysis skipped: {str(e)}")
        
        # Report summary
        report_logger.info("=" * 70)
        report_logger.info("REPORT SUMMARY")
        report_logger.info(f"Generated at: {timestamp}")
        report_logger.info(f"Period: {start_date_str} to {end_date_str}")
        report_logger.info(f"Total: {total_customers} customers, {total_orders} orders, {formatted_revenue} revenue")
        report_logger.info("=" * 70)
        
        # Return result for potential API consumption
        return {
            'timestamp': timestamp,
            'period': {'start': start_date_str, 'end': end_date_str},
            'metrics': {
                'total_customers': total_customers,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'avg_order_value': avg_order_value if total_orders > 0 else 0
            },
            'top_customers': list(sorted_customers)[:5] if top_customers else []
        }
        
    except Exception as e:
        error_msg = f"Failed to generate CRM report: {str(e)}"
        logger.error(error_msg)
        report_logger.error(f"ERROR: {error_msg}")
        
        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            report_logger.error("Max retries exceeded. Report generation failed.")
        
        return {'error': str(e), 'timestamp': timestamp}

@shared_task
def generate_daily_summary():
    """Generate daily summary report"""
    report_logger = setup_report_logger()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        report_logger.info(f"DAILY SUMMARY - {yesterday_str}")
        report_logger.info(f"Generated at: {timestamp}")
        
        # You can add daily-specific queries here
        # For now, just log a placeholder
        report_logger.info("Daily summary placeholder - implement specific queries as needed")
        
        return {'status': 'success', 'date': yesterday_str}
        
    except Exception as e:
        report_logger.error(f"Daily summary failed: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@shared_task
def test_celery_setup():
    """Test task to verify Celery is working"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open('/tmp/crm_report_log.txt', 'a') as f:
        f.write(f"{timestamp} - Celery test task executed successfully\n")
    
    return {'status': 'success', 'timestamp': timestamp}
