from .models import SearchTopic
from django.db.models import F
import re

COMMON_STOPWORDS = {
    'je', 'ni', 'na', 'ya', 'wa', 'kwa', 'la', 'huu', 'hii', 'vile', 'vilevile',
    'pia', 'pale', 'nini', 'vipi', 'gani', 'ipi', 'yupi', 'wapi', 'how', 'what',
    'where', 'when', 'why', 'who', 'the', 'is', 'a', 'an'
}

def track_query_topics(query):
    # Simple extraction: words > 4 chars, normalized
    words = re.findall(r'\w+', query.lower())
    clean_words = [w for w in words if w not in COMMON_STOPWORDS and len(w) > 4]
    
    # Take top 3 keywords
    for topic in clean_words[:3]:
        obj, created = SearchTopic.objects.get_or_create(topic_name=topic)
        if not created:
            obj.count = F('count') + 1
            obj.save()
