from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import SearchTopic
from .serializers import SearchTopicSerializer

class HotTopicsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Return top 10 trending topics
        topics = SearchTopic.objects.all()[:10]
        serializer = SearchTopicSerializer(topics, many=True)
        return Response(serializer.data)
