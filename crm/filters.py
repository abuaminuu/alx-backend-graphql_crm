# crm/filters.py
import django_filters as filters
from django.db.models import Q
import re
from .models import Customer, Product, Order

class CustomerFilter(filters.FilterSet):
    # Basic filters
    name = filters.CharFilter(lookup_expr='icontains', help_text="Filter by customer name (case-insensitive)")
    email = filters.CharFilter(lookup_expr='icontains', help_text="Filter by email (case-insensitive)")
    phone = filters.CharFilter(lookup_expr='icontains', help_text="Filter by phone number")
    
    # Date range filters
    created_at = filters.DateFromToRangeFilter(
        help_text="Filter by creation date range (format: YYYY-MM-DD)"
    )
    created_at_gte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filter customers created on or after this date"
    )
    created_at_lte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filter customers created on or before this date"
    )
    
    # Custom filter: Phone pattern (starts with +1)
    phone_starts_with_plus_one = filters.BooleanFilter(
        method='filter_phone_starts_with_plus_one',
        help_text="Filter customers with phone numbers starting with +1"
    )
    
    # Custom filter: Search across multiple fields
    search = filters.CharFilter(
        method='filter_search',
        help_text="Search across name, email, and phone fields"
    )
    
    # Ordering
    order_by = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('email', 'email'),
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
        ),
        help_text="Order results by field (prefix with '-' for descending)"
    )
    
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains', 'istartswith', 'iendswith'],
            'email': ['exact', 'icontains', 'startswith'],
        }
    
    def filter_phone_starts_with_plus_one(self, queryset, name, value):
        """Filter customers with phone numbers starting with +1"""
        if value:
            return queryset.filter(phone__startswith='+1')
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple customer fields"""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(email__icontains=value) |
                Q(phone__icontains=value)
            )
        return queryset

class ProductFilter(filters.FilterSet):
    # Basic filters
    name = filters.CharFilter(lookup_expr='icontains', help_text="Filter by product name")
    
    # Price range filters
    price = filters.RangeFilter(help_text="Filter by price range (min and max)")
    price_gte = filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        help_text="Filter products with price greater than or equal to"
    )
    price_lte = filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        help_text="Filter products with price less than or equal to"
    )
    
    # Stock filters
    stock = filters.RangeFilter(help_text="Filter by stock quantity range")
    stock_gte = filters.NumberFilter(
        field_name='stock',
        lookup_expr='gte',
        help_text="Filter products with stock greater than or equal to"
    )
    stock_lte = filters.NumberFilter(
        field_name='stock',
        lookup_expr='lte',
        help_text="Filter products with stock less than or equal to"
    )
    
    # Custom filter: Low stock (stock < 10)
    low_stock = filters.BooleanFilter(
        method='filter_low_stock',
        help_text="Filter products with low stock (less than 10)"
    )
    
    # Custom filter: Out of stock
    out_of_stock = filters.BooleanFilter(
        method='filter_out_of_stock',
        help_text="Filter products that are out of stock"
    )
    
    # Custom filter: Price category
    price_category = filters.ChoiceFilter(
        method='filter_price_category',
        choices=[
            ('budget', 'Budget (< $50)'),
            ('mid', 'Mid-range ($50 - $200)'),
            ('premium', 'Premium (> $200)'),
        ],
        help_text="Filter by price category"
    )
    
    # Search across multiple fields
    search = filters.CharFilter(
        method='filter_search',
        help_text="Search across name and description"
    )
    
    # Ordering
    order_by = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('price', 'price'),
            ('stock', 'stock'),
            ('created_at', 'created_at'),
        ),
        help_text="Order results by field"
    )
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'price': ['exact', 'gte', 'lte', 'range'],
            'stock': ['exact', 'gte', 'lte', 'range'],
        }
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock (less than 10)"""
        if value:
            return queryset.filter(stock__lt=10, stock__gt=0)
        return queryset
    
    def filter_out_of_stock(self, queryset, name, value):
        """Filter products that are out of stock"""
        if value:
            return queryset.filter(stock=0)
        return queryset
    
    def filter_price_category(self, queryset, name, value):
        """Filter by price category"""
        if value == 'budget':
            return queryset.filter(price__lt=50)
        elif value == 'mid':
            return queryset.filter(price__gte=50, price__lte=200)
        elif value == 'premium':
            return queryset.filter(price__gt=200)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across product name"""
        if value:
            return queryset.filter(name__icontains=value)
        return queryset

class OrderFilter(filters.FilterSet):
    # Basic filters
    total_amount = filters.RangeFilter(help_text="Filter by order total amount range")
    total_amount_gte = filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        help_text="Filter orders with total amount greater than or equal to"
    )
    total_amount_lte = filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        help_text="Filter orders with total amount less than or equal to"
    )
    
    # Date range filters
    order_date = filters.DateFromToRangeFilter(
        help_text="Filter by order date range"
    )
    order_date_gte = filters.DateFilter(
        field_name='order_date',
        lookup_expr='gte',
        help_text="Filter orders on or after this date"
    )
    order_date_lte = filters.DateFilter(
        field_name='order_date',
        lookup_expr='lte',
        help_text="Filter orders on or before this date"
    )
    
    # Related field filters
    customer_name = filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains',
        help_text="Filter by customer name (case-insensitive)"
    )
    
    customer_email = filters.CharFilter(
        field_name='customer__email',
        lookup_expr='icontains',
        help_text="Filter by customer email"
    )
    
    product_name = filters.CharFilter(
        method='filter_product_name',
        help_text="Filter orders containing products with this name"
    )
    
    # Custom filter: Orders containing specific product ID
    product_id = filters.UUIDFilter(
        method='filter_product_id',
        help_text="Filter orders containing a specific product by ID"
    )
    
    # Custom filter: High value orders
    high_value = filters.BooleanFilter(
        method='filter_high_value',
        help_text="Filter high value orders (total > $500)"
    )
    
    # Custom filter: Recent orders
    recent = filters.BooleanFilter(
        method='filter_recent',
        help_text="Filter orders from the last 7 days"
    )
    
    # Search
    search = filters.CharFilter(
        method='filter_search',
        help_text="Search across order details"
    )
    
    # Ordering
    order_by = filters.OrderingFilter(
        fields=(
            ('order_date', 'order_date'),
            ('total_amount', 'total_amount'),
            ('created_at', 'created_at'),
        ),
        help_text="Order results by field"
    )
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte', 'range'],
            'order_date': ['exact', 'gte', 'lte', 'range'],
        }
    
    def filter_product_name(self, queryset, name, value):
        """Filter orders containing products with specific name"""
        if value:
            return queryset.filter(products__name__icontains=value).distinct()
        return queryset
    
    def filter_product_id(self, queryset, name, value):
        """Filter orders containing specific product ID"""
        if value:
            return queryset.filter(products__id=value).distinct()
        return queryset
    
    def filter_high_value(self, queryset, name, value):
        """Filter high value orders (total > $500)"""
        if value:
            return queryset.filter(total_amount__gt=500)
        return queryset
    
    def filter_recent(self, queryset, name, value):
        """Filter orders from the last 7 days"""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            week_ago = timezone.now() - timedelta(days=7)
            return queryset.filter(order_date__gte=week_ago)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across order and related fields"""
        if value:
            return queryset.filter(
                Q(customer__name__icontains=value) |
                Q(customer__email__icontains=value) |
                Q(products__name__icontains=value)
            ).distinct()
        return queryset
        