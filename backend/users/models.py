from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'ADMIN' or self.is_superuser
    
    @property
    def is_staff_user(self):
        """Check if user is staff (not just Django is_staff)"""
        return self.role in ['STAFF', 'ADMIN'] or self.is_staff


# Create your models here.
