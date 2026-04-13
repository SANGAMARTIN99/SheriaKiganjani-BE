from django.http import JsonResponse
from apps.chat.models import ChatMessage, ChatSession
from django.utils import timezone
from datetime import timedelta

class AnonymousRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only rate limit POST requests to the chat API
        if request.path == '/api/chat/' and request.method == 'POST':
            if not request.user.is_authenticated:
                # Get client IP
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                # Count messages from this IP in the last 24 hours
                last_24h = timezone.now() - timedelta(days=1)
                
                # We find all sessions matching this IP
                anonymous_sessions = ChatSession.objects.filter(
                    user__isnull=True,
                    ip_address=ip,
                    started_at__gte=last_24h
                )
                
                message_count = ChatMessage.objects.filter(
                    session__in=anonymous_sessions,
                    role='user'
                ).count()

                if message_count >= 3:
                    return JsonResponse({
                        'error': 'Daily limit reached for anonymous users. Please sign up to continue.',
                        'limit_reached': True
                    }, status=403)

        response = self.get_response(request)
        return response
