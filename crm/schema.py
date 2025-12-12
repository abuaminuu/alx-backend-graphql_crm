# crm/schema.py
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from .inputs import CustomerFilterInput, ProductFilterInput, OrderFilterInput
from .mutations import (
    CreateCustomer, BulkCreateCustomers,
    CreateProduct, CreateOrder
)

# --------------------------
# Object Types
# --------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = "__all__"
        filterset_class = CustomerFilter
    
    # Custom computed fields
    order_count = graphene.Int()
    total_spent = graphene.Float()
    
    def resolve_order_count(self, info):
        return self.orders.count()
    
    def resolve_total_spent(self, info):
        return self.orders.aggregate(total=Sum('total_amount'))['total'] or 0

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = "__all__"
        filterset_class = ProductFilter
    
    # Custom computed fields
    order_count = graphene.Int()
    revenue = graphene.Float()
    in_stock = graphene.Boolean()
    
    def resolve_order_count(self, info):
        return self.orders.count()
    
    def resolve_revenue(self, info):
        # Calculate revenue from OrderProduct records
        from .models import OrderProduct
        result = OrderProduct.objects.filter(product=self).aggregate(
            revenue=Sum('price_at_time') * Sum('quantity')
        )
        return result['revenue'] or 0
    
    def resolve_in_stock(self, info):
        return self.stock > 0

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = "__all__"
        filterset_class = OrderFilter
    
    products = graphene.List(ProductType)
    
    def resolve_products(self, info):
        return self.products.all()

# --------------------------
# Custom Connection Types with Filtering
# --------------------------
class CustomerConnection(graphene.relay.Connection):
    class Meta:
        node = CustomerType
    
    total_count = graphene.Int()
    edge_count = graphene.Int()
    
    def resolve_total_count(self, info):
        return self.iterable.count()
    
    def resolve_edge_count(self, info):
        return len(self.edges)

class ProductConnection(graphene.relay.Connection):
    class Meta:
        node = ProductType
    
    total_count = graphene.Int()
    total_value = graphene.Float()
    
    def resolve_total_count(self, info):
        return self.iterable.count()
    
    def resolve_total_value(self, info):
        return sum(float(node.price) for node in self.iterable)

class OrderConnection(graphene.relay.Connection):
    class Meta:
        node = OrderType
    
    total_count = graphene.Int()
    total_revenue = graphene.Float()
    average_order_value = graphene.Float()
    
    def resolve_total_count(self, info):
        return self.iterable.count()
    
    def resolve_total_revenue(self, info):
        return sum(float(node.total_amount) for node in self.iterable)
    
    def resolve_average_order_value(self, info):
        orders = list(self.iterable)
        if orders:
            total = sum(float(order.total_amount) for order in orders)
            return total / len(orders)
        return 0

# --------------------------
# Queries with Advanced Filtering
# --------------------------
class Query(graphene.ObjectType):
    # Customer queries with filtering
    customer = relay.Node.Field(CustomerType)
    
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        where=CustomerFilterInput(),
        description="Get all customers with filtering options"
    )
    
    search_customers = graphene.List(
        CustomerType,
        query=graphene.String(),
        limit=graphene.Int(default_value=20),
        description="Search customers across multiple fields"
    )
    
    # Product queries with filtering
    product = relay.Node.Field(ProductType)
    
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        where=ProductFilterInput(),
        description="Get all products with filtering options"
    )
    
    available_products = graphene.List(
        ProductType,
        description="Get products that are in stock"
    )
    
    low_stock_products = graphene.List(
        ProductType,
        threshold=graphene.Int(default_value=10),
        description="Get products with low stock"
    )
    
    # Order queries with filtering
    order = relay.Node.Field(OrderType)
    
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        where=OrderFilterInput(),
        description="Get all orders with filtering options"
    )
    
    customer_orders = graphene.List(
        OrderType,
        customer_id=graphene.ID(required=True),
        description="Get orders for a specific customer"
    )
    
    recent_orders = graphene.List(
        OrderType,
        days=graphene.Int(default_value=7),
        description="Get recent orders"
    )
    
    # Advanced queries with aggregation
    customer_stats = graphene.JSONString(
        description="Get customer statistics"
    )
    
    product_stats = graphene.JSONString(
        description="Get product statistics"
    )
    
    sales_summary = graphene.JSONString(
        start_date=graphene.Date(),
        end_date=graphene.Date(),
        description="Get sales summary for a date range"
    )
    
    # --------------------------
    # Resolvers
    # --------------------------
    
    def resolve_search_customers(self, info, query=None, limit=20):
        """Search customers across multiple fields"""
        qs = Customer.objects.all()
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        return qs[:limit]
    
    def resolve_available_products(self, info):
        """Get products that are in stock"""
        return Product.objects.filter(stock__gt=0)
    
    def resolve_low_stock_products(self, info, threshold=10):
        """Get products with low stock"""
        return Product.objects.filter(stock__gt=0, stock__lt=threshold)
    
    def resolve_customer_orders(self, info, customer_id):
        """Get orders for a specific customer"""
        try:
            customer = Customer.objects.get(id=customer_id)
            return customer.orders.all()
        except Customer.DoesNotExist:
            raise GraphQLError(f"Customer with ID {customer_id} not found")
    
    def resolve_recent_orders(self, info, days=7):
        """Get recent orders"""
        from_date = timezone.now() - timedelta(days=days)
        return Order.objects.filter(order_date__gte=from_date)
    
    def resolve_customer_stats(self, info):
        """Get customer statistics"""
        from django.db.models import Count, Avg, Sum
        
        stats = Customer.objects.aggregate(
            total_customers=Count('id'),
            active_customers=Count('id', filter=Q(orders__isnull=False)),
            avg_orders_per_customer=Avg('orders__count'),
            total_revenue=Sum('orders__total_amount')
        )
        
        # Top customers by order count
        top_customers = Customer.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:5].values('name', 'email', 'order_count')
        
        return {
            'summary': stats,
            'top_customers': list(top_customers)
        }
    
    def resolve_product_stats(self, info):
        """Get product statistics"""
        from django.db.models import Count, Sum, Avg
        
        stats = Product.objects.aggregate(
            total_products=Count('id'),
            in_stock=Count('id', filter=Q(stock__gt=0)),
            out_of_stock=Count('id', filter=Q(stock=0)),
            low_stock=Count('id', filter=Q(stock__lt=10, stock__gt=0)),
            avg_price=Avg('price'),
            total_stock_value=Sum('price') * Sum('stock')
        )
        
        # Best selling products
        from .models import OrderProduct
        best_sellers = OrderProduct.objects.values(
            'product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            revenue=Sum('price_at_time') * Sum('quantity')
        ).order_by('-total_sold')[:5]
        
        return {
            'summary': stats,
            'best_sellers': list(best_sellers)
        }
    
    def resolve_sales_summary(self, info, start_date=None, end_date=None):
        """Get sales summary for a date range"""
        from django.db.models import Count, Sum, Avg
        
        qs = Order.objects.all()
        
        if start_date:
            qs = qs.filter(order_date__gte=start_date)
        if end_date:
            qs = qs.filter(order_date__lte=end_date)
        
        summary = qs.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount'),
            max_order_value=Max('total_amount'),
            min_order_value=Min('total_amount')
        )
        
        # Daily sales breakdown
        if start_date and end_date:
            daily_sales = qs.values('order_date').annotate(
                daily_revenue=Sum('total_amount'),
                order_count=Count('id')
            ).order_by('order_date')
            
            summary['daily_breakdown'] = list(daily_sales)
        
        return summary

# --------------------------
# Mutations
# --------------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

