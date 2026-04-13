import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class LawProvision(models.Model):
    SCOPE_CHOICES = (
        ('national', _('National')),
        ('regional', _('Regional')),
        ('municipal', _('Municipal')),
    )
    
    provision_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    law_name = models.CharField(max_length=255, help_text="e.g., Constitution of Tanzania, 1977")
    article_no = models.CharField(max_length=50, help_text="e.g., 15 or Section 4(2)")
    category = models.CharField(max_length=100, help_text="e.g., Basic Rights, Criminal, Labor")
    
    content_official_en = models.TextField(verbose_name=_("Official English Content"))
    content_official_sw = models.TextField(verbose_name=_("Official Swahili Content"))
    
    plain_summary_en = models.TextField(verbose_name=_("Plain English Summary (Mtaani)"))
    plain_summary_sw = models.TextField(verbose_name=_("Plain Swahili Summary (Mtaani)"))
    
    good_conduct = models.TextField(verbose_name=_("Good Conduct Suggestions"))
    penalty_summary = models.TextField(verbose_name=_("Penalty Summary"), null=True, blank=True)
    
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='national')
    region = models.CharField(max_length=100, null=True, blank=True, help_text="Required if scope is regional or municipal")
    
    last_amended = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    from pgvector.django import VectorField
    embedding = VectorField(dimensions=3072, null=True, blank=True)



    class Meta:
        verbose_name = _("Law Provision")
        verbose_name_plural = _("Law Provisions")
        unique_together = ('law_name', 'article_no')

    def __str__(self):
        return f"{self.law_name} - {self.article_no}"
