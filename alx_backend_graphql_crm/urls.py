# graphql_crm/urls.py
from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from .schema import schema
from django.http import JsonResponse

# Optional: Health check endpoint
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "CRM GraphQL API"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(
        graphiql=True, 
        schema=schema
    ))),
    path('health/', health_check),
]
