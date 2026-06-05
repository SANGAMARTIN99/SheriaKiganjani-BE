from .models import LegalAidOrganization
from .serializers import LegalAidOrganizationSerializer

CATEGORY_MAPPING = {
    'Labour Law': 'labour',
    'Criminal Law': 'criminal',
    'Basic Rights': 'human_rights',
    'Land Law': 'land',
    'Traffic Law': 'general',
    'Environmental Law': 'general',
    'Family Law': 'family',
    'Constitutional Law': 'human_rights',
}

def get_referral_for_category(law_category):
    mapped_cat = CATEGORY_MAPPING.get(law_category, 'general')
    orgs = LegalAidOrganization.objects.filter(category=mapped_cat, is_active=True).first()
    
    if orgs:
        return LegalAidOrganizationSerializer(orgs).data
    return None
