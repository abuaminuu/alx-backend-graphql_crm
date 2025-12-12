import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth import get_user_model
from .models import Address

# Get the actual user model (custom or default)
User = get_user_model()

# Define Object Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        # Exclude sensitive fields
        exclude = ('password', 'is_superuser', 'is_staff', 'groups', 'user_permissions')
        # Enable filtering
        filter_fields = {
            'username': ['exact', 'icontains', 'istartswith'],
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'is_active': ['exact'],
        }
        interfaces = (graphene.relay.Node,)
    
    # Custom field that requires logic
    full_name = graphene.String()
    
    def resolve_full_name(self, info):
        return f"{self.first_name} {self.last_name}".strip()
    
    # Field with permission check
    email = graphene.String()
    
    def resolve_email(self, info):
        # Only show email to the user themselves or staff
        request = info.context
        if request.user.is_authenticated and (request.user == self or request.user.is_staff):
            return self.email
        return None

class AddressType(DjangoObjectType):
    class Meta:
        model = Address
        filter_fields = {
            'city': ['exact', 'icontains'],
            'state': ['exact'],
            'is_primary': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

# Define Queries for Users app
class UsersQuery(graphene.ObjectType):
    # Single user by ID
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    
    # All users with filtering
    all_users = DjangoFilterConnectionField(UserType)
    
    # Current authenticated user
    me = graphene.Field(UserType)
    
    # Resolvers
    def resolve_user(self, info, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None
    
    def resolve_all_users(self, info, **kwargs):
        # Add permission check
        request = info.context
        if not request.user.is_authenticated:
            raise Exception("Authentication required")
        if not request.user.is_staff:
            raise Exception("Staff permission required")
        return User.objects.all()
    
    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in!")
        return user
    
    # Address queries
    address = graphene.Field(AddressType, id=graphene.ID(required=True))
    all_addresses = DjangoFilterConnectionField(AddressType)
    
    def resolve_address(self, info, id):
        return Address.objects.get(id=id)
    
    def resolve_all_addresses(self, info, **kwargs):
        return Address.objects.all()
    