# crm/inputs.py
import graphene
from graphene import relay
from graphene_django.filter import GlobalIDFilter

class DateRangeInput(graphene.InputObjectType):
    """Input type for date range filtering"""
    gte = graphene.Date(description="Greater than or equal to date")
    lte = graphene.Date(description="Less than or equal to date")

class NumberRangeInput(graphene.InputObjectType):
    """Input type for number range filtering"""
    gte = graphene.Float(description="Greater than or equal to")
    lte = graphene.Float(description="Less than or equal to")
    exact = graphene.Float(description="Exact value")

class CustomerFilterInput(graphene.InputObjectType):
    """Input type for filtering customers"""
    id = GlobalIDFilter()
    name = graphene.String()
    name__icontains = graphene.String()
    name__istartswith = graphene.String()
    email = graphene.String()
    email__icontains = graphene.String()
    phone = graphene.String()
    phone__icontains = graphene.String()
    phone_starts_with_plus_one = graphene.Boolean()
    created_at = DateRangeInput()
    created_at__gte = graphene.Date()
    created_at__lte = graphene.Date()
    search = graphene.String()
    order_by = graphene.String()

class ProductFilterInput(graphene.InputObjectType):
    """Input type for filtering products"""
    id = GlobalIDFilter()
    name = graphene.String()
    name__icontains = graphene.String()
    price = NumberRangeInput()
    price__gte = graphene.Float()
    price__lte = graphene.Float()
    stock = NumberRangeInput()
    stock__gte = graphene.Int()
    stock__lte = graphene.Int()
    low_stock = graphene.Boolean()
    out_of_stock = graphene.Boolean()
    price_category = graphene.String()
    search = graphene.String()
    order_by = graphene.String()

class OrderFilterInput(graphene.InputObjectType):
    """Input type for filtering orders"""
    id = GlobalIDFilter()
    total_amount = NumberRangeInput()
    total_amount__gte = graphene.Float()
    total_amount__lte = graphene.Float()
    order_date = DateRangeInput()
    order_date__gte = graphene.Date()
    order_date__lte = graphene.Date()
    customer_name = graphene.String()
    customer_email = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()
    high_value = graphene.Boolean()
    recent = graphene.Boolean()
    search = graphene.String()
    order_by = graphene.String()
    