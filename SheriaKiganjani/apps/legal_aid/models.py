from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class LegalAidOrganization(models.Model):
    CATEGORY_CHOICES = (
        ('human_rights', _('Human Rights')),
        ('labour', _('Labour Law')),
        ('family', _('Family & Inheritance')),
        ('criminal', _('Criminal Defence')),
        ('land', _('Land Disputes')),
        ('general', _('General Legal Aid')),
    )
    
    org_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    
    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Legal Aid Organization")
        verbose_name_plural = _("Legal Aid Organizations")

    def __str__(self):
        return self.name
