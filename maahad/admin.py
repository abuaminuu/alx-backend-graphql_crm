from django.contrib import admin
from .models import Student, Program

# register boiler plate 
def register(model):
    return admin.site.register(model)

# Register your models here.
register(Student)
register(Program)
