from django.urls import path
from .views import HotTopicsView

urlpatterns = [
    path('hot-topics/', HotTopicsView.as_view(), name='hot_topics'),
]
