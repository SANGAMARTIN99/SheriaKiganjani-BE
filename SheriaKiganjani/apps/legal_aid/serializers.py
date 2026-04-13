from rest_framework import serializers
from .models import LegalAidOrganization

class LegalAidOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalAidOrganization
        fields = '__all__'
