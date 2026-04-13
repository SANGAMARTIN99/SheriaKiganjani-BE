from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('message_id', 'role', 'content', 'citations', 'rating', 'created_at')

class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source='messages.count', read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ('session_id', 'title', 'language', 'region', 'started_at', 'last_active', 'message_count')
