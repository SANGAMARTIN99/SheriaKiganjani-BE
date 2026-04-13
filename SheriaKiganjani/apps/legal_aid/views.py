from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import LegalAidOrganization
from .serializers import LegalAidOrganizationSerializer

class LegalAidListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        category = request.query_params.get('category')
        if category:
            orgs = LegalAidOrganization.objects.filter(category=category, is_active=True)
        else:
            orgs = LegalAidOrganization.objects.filter(is_active=True)
            
        serializer = LegalAidOrganizationSerializer(orgs, many=True)
        return Response(serializer.data)
