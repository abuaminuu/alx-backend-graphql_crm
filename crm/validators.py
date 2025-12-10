# crm/validators.py
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return True
    
    # Acceptable formats: +1234567890 or 123-456-7890 or (123) 456-7890
    phone_pattern = re.compile(r'^(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$')
    
    if not phone_pattern.match(phone):
        raise ValidationError(
            "Phone number must be in format: +1234567890 or 123-456-7890"
        )
    return True

def validate_unique_email(email, exclude_id=None):
    """Validate that email is unique"""
    from .models import Customer
    
    qs = Customer.objects.filter(email=email)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    
    if qs.exists():
        raise ValidationError(f"Email '{email}' already exists")
    return True
