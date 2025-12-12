from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.username

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.street}, {self.city}"
