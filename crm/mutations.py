# crm/mutations.py
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from graphql import GraphQLError

from .models import Customer, Product, Order, OrderProduct
from .validators import validate_phone_number, validate_unique_email

# Object Types for GraphQL
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

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

# Mutation: CreateCustomer
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    
    @classmethod
    def mutate(cls, root, info, input):
        try:
            # Validate email uniqueness
            validate_unique_email(input.email)
            
            # Validate phone format if provided
            if input.phone:
                validate_phone_number(input.phone)
            
            # Create customer
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone or None
            )
            customer.full_clean()  # Run model validation
            customer.save()
            
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully"
            )
            
        except DjangoValidationError as e:
            raise GraphQLError(str(e))
        except Exception as e:
            raise GraphQLError(f"Failed to create customer: {str(e)}")

# Mutation: BulkCreateCustomers
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, inputs):
        created_customers = []
        errors = []
        
        with transaction.atomic():
            for idx, input_data in enumerate(inputs):
                try:
                    # Validate email uniqueness
                    validate_unique_email(input_data.email)
                    
                    # Validate phone format if provided
                    if input_data.phone:
                        validate_phone_number(input_data.phone)
                    
                    # Create customer
                    customer = Customer(
                        name=input_data.name,
                        email=input_data.email,
                        phone=input_data.phone or None
                    )
                    customer.full_clean()
                    customer.save()
                    created_customers.append(customer)
                    
                except Exception as e:
                    errors.append(f"Row {idx + 1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors
        )

# Mutation: CreateProduct
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    
    @classmethod
    def mutate(cls, root, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                raise GraphQLError("Price must be greater than 0")
            
            # Validate stock is not negative
            stock = input.stock or 0
            if stock < 0:
                raise GraphQLError("Stock cannot be negative")
            
            # Create product
            product = Product(
                name=input.name,
                price=input.price,
                stock=stock
            )
            product.full_clean()
            product.save()
            
            return CreateProduct(product=product)
            
        except DjangoValidationError as e:
            raise GraphQLError(str(e))
        except Exception as e:
            raise GraphQLError(f"Failed to create product: {str(e)}")

# Mutation: CreateOrder
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    
    @classmethod
    def mutate(cls, root, info, input):
        try:
            with transaction.atomic():
                # Validate customer exists
                try:
                    customer = Customer.objects.get(id=input.customer_id)
                except Customer.DoesNotExist:
                    raise GraphQLError(f"Customer with ID {input.customer_id} not found")
                
                # Validate at least one product
                if not input.product_ids:
                    raise GraphQLError("At least one product is required")
                
                # Get products and validate they exist
                products = []
                total_amount = 0
                
                for product_id in input.product_ids:
                    try:
                        product = Product.objects.get(id=product_id)
                        products.append(product)
                        total_amount += product.price
                    except Product.DoesNotExist:
                        raise GraphQLError(f"Product with ID {product_id} not found")
                
                # Create order
                order = Order(
                    customer=customer,
                    total_amount=total_amount
                )
                if input.order_date:
                    order.order_date = input.order_date
                
                order.full_clean()
                order.save()
                
                # Add products to order through OrderProduct
                for product in products:
                    OrderProduct.objects.create(
                        order=order,
                        product=product,
                        price_at_time=product.price,
                        quantity=1
                    )
                
                return CreateOrder(order=order)
                
        except GraphQLError as e:
            raise e
        except Exception as e:
            raise GraphQLError(f"Failed to create order: {str(e)}")
