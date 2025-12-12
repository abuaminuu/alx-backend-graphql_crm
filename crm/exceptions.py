# crm/exceptions.py
from graphql import GraphQLError

class CRMValidationError(GraphQLError):
    """Custom validation error for CRM mutations"""
    def __init__(self, message, code="VALIDATION_ERROR"):
        super().__init__(message, extensions={"code": code})

class DuplicateEmailError(CRMValidationError):
    """Error for duplicate email addresses"""
    def __init__(self, email):
        super().__init__(
            f"Email '{email}' already exists",
            code="DUPLICATE_EMAIL"
        )

class InvalidPhoneError(CRMValidationError):
    """Error for invalid phone format"""
    def __init__(self):
        super().__init__(
            "Phone number must be in format: +1234567890 or 123-456-7890",
            code="INVALID_PHONE"
        )

class ResourceNotFoundError(CRMValidationError):
    """Error when resource not found"""
    def __init__(self, resource_type, resource_id):
        super().__init__(
            f"{resource_type} with ID '{resource_id}' not found",
            code="RESOURCE_NOT_FOUND"
        )

class InsufficientStockError(CRMValidationError):
    """Error when product stock is insufficient"""
    def __init__(self, product_name, requested, available):
        super().__init__(
            f"Insufficient stock for '{product_name}': "
            f"requested {requested}, available {available}",
            code="INSUFFICIENT_STOCK"
        )
        