from django.urls import path
from .views import ChatView, ChatHistoryView, ChatSessionDetailView, MessageRatingView

urlpatterns = [
    path('', ChatView.as_view(), name='chat_api'),
    path('history/', ChatHistoryView.as_view(), name='chat_history'),
    path('session/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='chat_detail'),
    path('message/<uuid:message_id>/rate/', MessageRatingView.as_view(), name='message_rate'),
]
