from django.urls import path
from .views import LawProvisionListView

urlpatterns = [
    path('provisions/', LawProvisionListView.as_view(), name='law_provisions_list'),
]
