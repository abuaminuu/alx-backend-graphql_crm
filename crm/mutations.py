# crm/mutations.py
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError as DjangoValidationError
from graphql import GraphQLError

from .models import Customer, Product, Order, OrderProduct
from .validators import (
    validate_phone_format, validate_unique_email,
    validate_price, validate_stock,
    validate_customer_exists, validate_products_exist
)
from .exceptions import (
    CRMValidationError, DuplicateEmailError,
    InvalidPhoneError, ResourceNotFoundError
)

# --------------------------
# Object Types
# --------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = "__all__"

class OrderProductType(DjangoObjectType):
    class Meta:
        model = OrderProduct
        fields = "__all__"

class OrderType(DjangoObjectType):
    products = graphene.List(ProductType)
    
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = "__all__"
    
    def resolve_products(self, info):
        return self.products.all()

# --------------------------
# Input Types
# --------------------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Customer's full name")
    email = graphene.String(required=True, description="Customer's email address")
    phone = graphene.String(description="Customer's phone number (optional)")

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Product name")
    price = graphene.Decimal(required=True, description="Product price (positive)")
    stock = graphene.Int(description="Stock quantity (non-negative, default: 0)")

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True, description="ID of existing customer")
    product_ids = graphene.List(
        graphene.ID, 
        required=True, 
        description="List of product IDs"
    )
    order_date = graphene.DateTime(description="Order date (defaults to now)")

# --------------------------
# Output Types
# --------------------------
class CustomerOutput(graphene.ObjectType):
    customer = graphene.Field(CustomerType)
    message = graphene.String()

class BulkCustomerOutput(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    error_count = graphene.Int()

class ProductOutput(graphene.ObjectType):
    product = graphene.Field(ProductType)

class OrderOutput(graphene.ObjectType):
    order = graphene.Field(OrderType)

# --------------------------
# Mutation: CreateCustomer
# --------------------------
class CreateCustomer(graphene.Mutation):
    """Mutation to create a single customer"""
    
    class Arguments:
        input = CustomerInput(required=True)
    
    Output = CustomerOutput
    
    @classmethod
    def mutate(cls, root, info, input):
        try:
            # Validate email uniqueness
            validate_unique_email(input.email)
            
            # Validate phone format if provided
            if input.phone:
                validate_phone_format(input.phone)
            
            # Create and save customer
            customer = Customer(
                name=input.name.strip(),
                email=input.email.lower().strip(),
                phone=input.phone.strip() if input.phone else None
            )
            
            # Run Django model validation
            customer.full_clean()
            customer.save()
            
            return CustomerOutput(
                customer=customer,
                message="Customer created successfully"
            )
            
        except DjangoValidationError as e:
            # Extract first error message
            error_msg = list(e.message_dict.values())[0][0]
            raise CRMValidationError(error_msg)
        except Exception as e:
            raise GraphQLError(f"Failed to create customer: {str(e)}")

# --------------------------
# Mutation: BulkCreateCustomers
# --------------------------
class BulkCreateCustomers(graphene.Mutation):
    """Mutation to create multiple customers in a single transaction"""
    
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)
    
    Output = BulkCustomerOutput
    
    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, inputs):
        created_customers = []
        errors = []
        
        for idx, input_data in enumerate(inputs, start=1):
            try:
                # Validate email uniqueness
                validate_unique_email(input_data.email)
                
                # Validate phone format if provided
                if input_data.phone:
                    validate_phone_format(input_data.phone)
                
                # Create customer
                customer = Customer(
                    name=input_data.name.strip(),
                    email=input_data.email.lower().strip(),
                    phone=input_data.phone.strip() if input_data.phone else None
                )
                
                customer.full_clean()
                customer.save()
                created_customers.append(customer)
                
            except DjangoValidationError as e:
                error_msg = list(e.message_dict.values())[0][0]
                errors.append(f"Row {idx}: {error_msg}")
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        return BulkCustomerOutput(
            customers=created_customers,
            errors=errors,
            success_count=len(created_customers),
            error_count=len(errors)
        )

# --------------------------
# Mutation: CreateProduct
# --------------------------
class CreateProduct(graphene.Mutation):
    """Mutation to create a product"""
    
    class Arguments:
        input = ProductInput(required=True)
    
    Output = ProductOutput
    
    @classmethod
    def mutate(cls, root, info, input):
        try:
            # Validate price
            validate_price(input.price)
            
            # Validate stock
            stock = input.stock if input.stock is not None else 0
            validate_stock(stock)
            
            # Create and save product
            product = Product(
                name=input.name.strip(),
                price=input.price,
                stock=stock
            )
            
            product.full_clean()
            product.save()
            
            return ProductOutput(product=product)
            
        except DjangoValidationError as e:
            error_msg = list(e.message_dict.values())[0][0]
            raise CRMValidationError(error_msg)
        except Exception as e:
            raise GraphQLError(f"Failed to create product: {str(e)}")

# --------------------------
# Mutation: CreateOrder
# --------------------------
class CreateOrder(graphene.Mutation):
    """Mutation to create an order with products"""
    
    class Arguments:
        input = OrderInput(required=True)
    
    Output = OrderOutput
    
    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, input):
        try:
            # Validate customer exists
            customer = validate_customer_exists(input.customer_id)
            
            # Validate products exist
            products = validate_products_exist(input.product_ids)
            
            # Create order
            order = Order(customer=customer)
            if input.order_date:
                order.order_date = input.order_date
            
            order.full_clean()
            order.save()
            
            # Add products to order and calculate total
            total_amount = 0
            for product in products:
                order_product = OrderProduct(
                    order=order,
                    product=product,
                    price_at_time=product.price,
                    quantity=1  # Default quantity
                )
                order_product.save()
                total_amount += product.price
            
            # Update order total
            order.total_amount = total_amount
            order.save()
            
            return OrderOutput(order=order)
            
        except DjangoValidationError as e:
            error_msg = list(e.message_dict.values())[0][0]
            raise CRMValidationError(error_msg)
        except Exception as e:
            # Rollback transaction on error
            transaction.set_rollback(True)
            raise GraphQLError(f"Failed to create order: {str(e)}")
            