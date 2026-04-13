from rest_framework import serializers
from .models import SearchTopic

class SearchTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchTopic
        fields = ['topic_name', 'count', 'last_requested']
