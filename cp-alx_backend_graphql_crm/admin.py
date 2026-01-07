from django.contrib import admin
from crm.models import Product, Customer, Order, OrderItem

# register boiler plate 
def register(model):
    return admin.site.register(model)

# Register your models here.
register(Customer)
register(Product)
register(Order)
register(OrderItem)
