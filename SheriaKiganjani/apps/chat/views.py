from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import ChatSession, ChatMessage
from .serializers import ChatMessageSerializer, ChatSessionSerializer
from apps.rag.utils import get_legal_response, get_llm
from apps.analytics.utils import track_query_topics
from apps.legal_aid.utils import get_referral_for_category
import uuid


class ChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = request.data.get('session_id')
        query = request.data.get('query', '').strip()
        language = request.data.get('language', 'sw')

        if language not in ('sw', 'en'):
            language = 'sw'

        if not query:
            return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Sanitize query length — prevent abuse
        if len(query) > 2000:
            query = query[:2000]

        # Track topics for analytics (non-blocking)
        try:
            track_query_topics(query)
        except Exception:
            pass

        # ── 1. Get or Create Session ──────────────────────────────────────────
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_fwd.split(',')[0] if x_fwd else request.META.get('REMOTE_ADDR')

            session = ChatSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                language=language,
                ip_address=ip
            )

        # ── 2. Save User Message ──────────────────────────────────────────────
        user_msg = ChatMessage.objects.create(
            session=session,
            role='user',
            content=query
        )

        # ── 3. Get AI Response (now returns a dict) ───────────────────────────
        try:
            ai_result = get_legal_response(query, language=language)
        except Exception as e:
            return Response(
                {'error': f"AI Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # ai_result = {'text': str, 'citations': list, 'intent': str}
        ai_response_text = ai_result.get('text', '')
        citations = ai_result.get('citations', [])
        intent = ai_result.get('intent', 'legal_query')

        # ── 4. Save AI Message (with citations) ───────────────────────────────
        ai_msg = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response_text,
            citations=citations
        )

        # ── 5. Referral Logic (only for legal queries) ────────────────────────
        referral = None
        if intent == 'legal_query':
            q_lower = query.lower()
            if any(w in q_lower for w in [
                'kazi', 'mwajiri', 'futiwa', 'mkataba', 'labour', 'work', 'ajira',
                'mfanyakazi', 'mshahara', 'likizo', 'salary', 'wage', 'employment'
            ]):
                referral = get_referral_for_category('Labour Law')
            elif any(w in q_lower for w in [
                'haki', 'shambulio', 'katiba', 'rights', 'arrested', 'kukamatwa',
                'polisi', 'jela', 'kifungo', 'discrimination', 'ubaguzi', 'uhuru'
            ]):
                referral = get_referral_for_category('Basic Rights')
            elif any(w in q_lower for w in [
                'ardhi', 'kiwanja', 'shamba', 'land', 'plot', 'nyumba', 'house',
                'property', 'mali', 'umiliki', 'ownership'
            ]):
                referral = get_referral_for_category('Land Law')
            elif any(w in q_lower for w in [
                'wizi', 'theft', 'iba', 'uongo', 'fraud', 'jinai', 'criminal',
                'kosa', 'uhalifu', 'offense', 'mauaji', 'murder', 'shambulio'
            ]):
                referral = get_referral_for_category('Criminal Law')

        # ── 6. Auto-generate session title on first interaction ───────────────
        if session.messages.filter(role='user').count() == 1:
            try:
                llm = get_llm()
                title_prompt = (
                    f"Summarize this legal question in 4-6 words as a chat title "
                    f"in {'Swahili' if language == 'sw' else 'English'}: '{query}'. "
                    f"Return ONLY the title, no quotes, no punctuation at end."
                )
                title_res = llm.invoke(title_prompt)
                generated_title = title_res.content.strip().strip('"').strip("'")
                if generated_title:
                    session.title = generated_title[:255]
                    session.save()
            except Exception:
                pass

        return Response({
            'session_id': str(session.session_id),
            'title': session.title,
            'intent': intent,
            'user_message': ChatMessageSerializer(user_msg).data,
            'ai_message': ChatMessageSerializer(ai_msg).data,
            'referral': referral,
            'citations': citations,
        })


class ChatHistoryView(generics.ListAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by('-last_active')


class ChatSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_id=session_id, user=request.user)
            messages = session.messages.all()
            return Response({
                'session': ChatSessionSerializer(session).data,
                'messages': ChatMessageSerializer(messages, many=True).data
            })
        except ChatSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


class MessageRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, message_id):
        try:
            message = ChatMessage.objects.get(
                message_id=message_id,
                session__user=request.user
            )
            rating = request.data.get('rating')
            if rating not in [0, 1]:
                return Response(
                    {'error': 'Invalid rating. Use 0 for helpful, 1 for not helpful.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            message.rating = rating
            message.save()
            return Response({'status': 'success'})
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
