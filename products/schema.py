import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q, Avg, Count
from .models import Category, Product, Review

# Define Object Types
class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        filter_fields = ['name']
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    # Custom fields
    average_rating = graphene.Float()
    review_count = graphene.Int()
    in_stock = graphene.Boolean()
    
    class Meta:
        model = Product
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'price': ['exact', 'gte', 'lte', 'range'],
            'stock_quantity': ['exact', 'gte', 'lte'],
            'status': ['exact'],
            'category__name': ['exact', 'icontains'],
            'seller__username': ['exact'],
        }
        interfaces = (graphene.relay.Node,)
    
    def resolve_average_rating(self, info):
        # Calculate average rating on the fly
        return self.reviews.aggregate(avg=Avg('rating'))['avg']
    
    def resolve_review_count(self, info):
        return self.reviews.count()
    
    def resolve_in_stock(self, info):
        return self.stock_quantity > 0

class ReviewType(DjangoObjectType):
    class Meta:
        model = Review
        filter_fields = {
            'rating': ['exact', 'gte', 'lte'],
            'product__name': ['icontains'],
            'user__username': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

# Define Queries for Products app
class ProductsQuery(graphene.ObjectType):
    # Single queries
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    category = graphene.Field(CategoryType, id=graphene.ID(required=True))
    review = graphene.Field(ReviewType, id=graphene.ID(required=True))
    
    # List queries with filtering
    all_products = DjangoFilterConnectionField(ProductType)
    all_categories = DjangoFilterConnectionField(CategoryType)
    all_reviews = DjangoFilterConnectionField(ReviewType)
    
    # Custom queries
    search_products = graphene.List(
        ProductType,
        query=graphene.String(required=True),
        min_price=graphene.Float(),
        max_price=graphene.Float(),
        in_stock_only=graphene.Boolean(default_value=False)
    )
    
    top_rated_products = graphene.List(
        ProductType,
        limit=graphene.Int(default_value=10)
    )
    
    products_by_category = graphene.List(
        ProductType,
        category_name=graphene.String(required=True)
    )
    
    # Resolvers
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_category(self, info, id):
        try:
            return Category.objects.get(id=id)
        except Category.DoesNotExist:
            return None
    
    def resolve_review(self, info, id):
        try:
            return Review.objects.get(id=id)
        except Review.DoesNotExist:
            return None
    
    def resolve_all_products(self, info, **kwargs):
        # Base queryset
        qs = Product.objects.all()
        
        # Add permission/visibility logic
        request = info.context
        if not request.user.is_staff:
            qs = qs.filter(status='active')
        
        return qs
    
    def resolve_search_products(self, info, query, min_price=None, max_price=None, in_stock_only=False):
        # Build search query
        search_q = Q(name__icontains=query) | Q(description__icontains=query)
        qs = Product.objects.filter(search_q)
        
        # Apply filters
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if in_stock_only:
            qs = qs.filter(stock_quantity__gt=0)
        
        # Hide inactive products from non-staff
        request = info.context
        if not request.user.is_staff:
            qs = qs.filter(status='active')
        
        return qs
    
    def resolve_top_rated_products(self, info, limit):
        # Get products with their average ratings
        from django.db.models import Avg
        
        qs = Product.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(
            avg_rating__isnull=False,
            status='active'
        ).order_by('-avg_rating')[:limit]
        
        return qs
    
    def resolve_products_by_category(self, info, category_name):
        return Product.objects.filter(
            category__name__iexact=category_name,
            status='active'
        )
