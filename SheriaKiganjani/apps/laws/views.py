from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import LawProvision
from .serializers import LawProvisionSerializer

class LawProvisionListView(generics.ListAPIView):
    queryset = LawProvision.objects.all().order_by('law_name', 'section_number')
    serializer_class = LawProvisionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        law_name = self.request.query_params.get('law_name')
        if category:
            queryset = queryset.filter(category=category)
        if law_name:
            queryset = queryset.filter(law_name__icontains=law_name)
        return queryset
