#!/bin/bash

# clean_inactive_customers.sh
# Deletes customers with no orders in the last year
# Logs results to /tmp/customer_cleanup_log.txt

# Set the Django project path (UPDATE THIS TO YOUR ACTUAL PATH)
PROJECT_PATH="/home/abuaminuu/machine/alx_travel_app_0x02"
PYTHON_PATH="/usr/bin/python3"
MANAGE_PY="$PROJECT_PATH/manage.py"
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Navigate to project directory
cd "$PROJECT_PATH" || {
    echo "ERROR: Could not navigate to $PROJECT_PATH" >> "$LOG_FILE"
    exit 1
}

# Run Django shell command to delete inactive customers
echo "==========================================" >> "$LOG_FILE"
echo "Customer Cleanup Started at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

# Python command to delete inactive customers
$PYTHON_PATH "$MANAGE_PY" shell << 'EOF' >> "$LOG_FILE" 2>&1
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Order
import sys

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

try:
    # Find customers with no orders in the last year
    # First, get all customers
    all_customers = Customer.objects.all()
    
    # Find inactive customers (those with no orders OR last order > 1 year ago)
    deleted_count = 0
    kept_count = 0
    
    for customer in all_customers:
        # Check if customer has any orders
        has_orders = Order.objects.filter(customer=customer).exists()
        
        if not has_orders:
            # Customer has never placed an order
            print(f"Deleting customer {customer.id} - {customer.email}: No orders ever")
            customer.delete()
            deleted_count += 1
        else:
            # Check for recent orders (within last year)
            recent_orders = Order.objects.filter(
                customer=customer,
                order_date__gte=one_year_ago
            ).exists()
            
            if not recent_orders:
                # Customer has orders, but none in the last year
                print(f"Deleting customer {customer.id} - {customer.email}: No orders in last year")
                customer.delete()
                deleted_count += 1
            else:
                kept_count += 1
    
    # Log summary
    print(f"\n=== Cleanup Summary ===")
    print(f"Total customers processed: {all_customers.count()}")
    print(f"Customers deleted: {deleted_count}")
    print(f"Customers kept: {kept_count}")
    print("Cleanup completed successfully!")
    
except Exception as e:
    print(f"ERROR during cleanup: {str(e)}")
    sys.exit(1)

EOF

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Cleanup completed successfully at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
else
    echo "ERROR: Cleanup failed at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

