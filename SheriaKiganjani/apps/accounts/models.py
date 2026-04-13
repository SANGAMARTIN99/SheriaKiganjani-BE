from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', _('Citizen')),
        ('admin', _('Admin')),
        ('content_editor', _('Content Editor')),
        ('legal_reviewer', _('Legal Reviewer')),
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )
    
    preferred_language = models.CharField(
        max_length=10,
        choices=(('sw', 'Swahili'), ('en', 'English')),
        default='sw'
    )
    
    region = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.username} ({self.role})"
