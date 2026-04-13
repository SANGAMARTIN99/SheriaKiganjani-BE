from django.db import models

class SearchTopic(models.Model):
    topic_name = models.CharField(max_length=100, unique=True)
    count = models.PositiveIntegerField(default=1)
    last_requested = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-count']
        verbose_name = "Search Topic"
        verbose_name_plural = "Search Topics"

    def __str__(self):
        return f"{self.topic_name} ({self.count})"
