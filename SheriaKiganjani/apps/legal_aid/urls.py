from django.urls import path
from .views import LegalAidListView

urlpatterns = [
    path('organizations/', LegalAidListView.as_view(), name='legal_aid_list'),
]
