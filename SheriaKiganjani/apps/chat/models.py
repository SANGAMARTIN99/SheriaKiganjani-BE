import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_sessions'
    )
    title = models.CharField(max_length=255, default=_("New Chat"))
    language = models.CharField(max_length=10, default='sw')
    region = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_active']

    def __str__(self):
        return f"{self.title} ({self.session_id})"

class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ('user', _('User')),
        ('assistant', _('Assistant')),
    )
    
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    rating = models.IntegerField(null=True, blank=True, help_text="0: helpful, 1: not helpful")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
