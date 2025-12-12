# crm/schema.py
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Customer, Product, Order
from .mutations import (
    CustomerType, ProductType, OrderItem,
    CreateCustomer, BulkCreateCustomers,
    CreateProduct, CreateOrder
)


# Queries
class Query(graphene.ObjectType):
    customer = relay.Node.Field(CustomerType)
    all_customers = DjangoFilterConnectionField(CustomerType)
    
    product = relay.Node.Field(ProductType)
    all_products = DjangoFilterConnectionField(ProductType)
    
    order = relay.Node.Field(OrderItem)
    all_orders = DjangoFilterConnectionField(OrderItem)
    
    number = graphene.String(default_value="+234....")

    def resolve_number(self, info):
        return f"please call +354.... for care"

    # Custom resolvers
    def resolve_all_customers(self, info, **kwargs):
        return Customer.objects.all()
    
    def resolve_all_products(self, info, **kwargs):
        return Product.objects.all()
    
    def resolve_all_orders(self, info, **kwargs):
        return Order.objects.all()

# Mutations
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
