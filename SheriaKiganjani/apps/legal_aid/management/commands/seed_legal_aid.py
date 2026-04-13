from django.core.management.base import BaseCommand
from apps.legal_aid.models import LegalAidOrganization

class Command(BaseCommand):
    help = 'Seeds initial Legal Aid Organizations'

    def handle(self, *args, **options):
        organizations = [
            {
                'name': 'TAWLA (Tanzania Women Lawyers Association)',
                'category': 'human_rights',
                'description': 'Provides legal aid mostly to women and children on issues of inheritance, land, and domestic violence.',
                'phone': '+255 22 211 0758',
                'email': 'info@tawla.or.tz',
                'website': 'https://tawla.or.tz',
                'address': 'Dares Salaam, Arusha, Dodoma, Tanga.',
            },
            {
                'name': 'LHRC (Legal and Human Rights Centre)',
                'category': 'human_rights',
                'description': 'A premier human rights organization in Tanzania providing legal aid and advocacy.',
                'phone': '+255 22 277 3037',
                'website': 'https://humanrights.or.tz',
                'address': 'Kijitonyama, Dar es Salaam.',
            },
            {
                'name': 'TLS (Tanganyika Law Society) Legal Aid',
                'category': 'general',
                'description': 'The bar association of Tanzania Mainland offering legal aid clinics across the country.',
                'phone': '+255 22 211 2060',
                'website': 'https://tls.or.tz',
                'address': 'Dar es Salaam.',
            },
            {
                'name': 'TUCTA (Trade Union Congress of Tanzania)',
                'category': 'labour',
                'description': 'Apex trade union body providing support and legal advice on labour disputes.',
                'phone': '+255 22 212 2568',
                'email': 'info@tucta.or.tz',
            },
        ]

        for org_data in organizations:
            obj, created = LegalAidOrganization.objects.update_or_create(
                name=org_data['name'],
                defaults=org_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Org: {org_data['name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated Org: {org_data['name']}"))
