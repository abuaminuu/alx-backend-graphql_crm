from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from alx_backend_graphql_crm import schema

urlpatterns = [
    path("graphql",csrf_exempt(GraphQLView.as_view(graphiql=True))),
]

