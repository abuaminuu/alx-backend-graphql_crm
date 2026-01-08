"""
crm/__init__.py
Make Celery app available when importing crm
"""

from .celery import app as celery_app

__all__ = ('celery_app',)
