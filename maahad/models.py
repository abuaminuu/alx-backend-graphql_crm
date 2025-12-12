from django.db import models

# Create your models here.

class Student(models.Model):
    registration_number = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    phone = models.CharField(max_length=16)

    def __str__(self):
        return self.name

class Program(models.Model):
    name = models.CharField(max_length=16)
    program_code = models.CharField(max_length=8)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    def __str__(self):
        return self.name

class Staff(models.Model):
    pass
