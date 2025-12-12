from django.urls import path, include
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin

urlpatterns = [
    # path("admin/", admin.site.urls),
    # path("/graphqlz/", csrf_exempt(GraphQLView.as_view(grapiql=True))),
]
