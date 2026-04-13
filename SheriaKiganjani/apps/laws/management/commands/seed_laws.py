from django.core.management.base import BaseCommand
from apps.laws.models import LawProvision
import datetime

class Command(BaseCommand):
    help = 'Seeds initial Constitution articles (12-15)'

    def handle(self, *args, **options):
        laws = [
            {
                'law_name': 'Constitution of Tanzania, 1977',
                'article_no': '12',
                'category': 'Basic Rights',
                'content_official_en': 'All human beings are born free, and are all equal.',
                'content_official_sw': 'Binadamu wote huzaliwa huru, na wote ni sawa.',
                'plain_summary_en': 'Everyone is equal and free from birth. No one is better than others.',
                'plain_summary_sw': 'Kila mtu ni sawa na huru tangu kuzaliwa. Hakuna aliye bora kuliko mwingine.',
                'good_conduct': 'Treat everyone with respect and do not discriminate based on tribe, religion, or gender.',
                'scope': 'national',
            },
            {
                'law_name': 'Constitution of Tanzania, 1977',
                'article_no': '13',
                'category': 'Basic Rights',
                'content_official_en': 'All persons are equal before the law and are entitled, without any discrimination, to protection and equality before the law.',
                'content_official_sw': 'Watu wote ni sawa mbele ya sheria, na wanayo haki, bila ubaguzi wowote, kulindwa na kupata haki sawa mbele ya sheria.',
                'plain_summary_en': 'The law applies to everyone equally. No one is above the law, and everyone has the right to be protected by it.',
                'plain_summary_sw': 'Sheria inamhusu kila mtu sawa. Hakuna aliye juu ya sheria, na kila mtu ana haki ya kulindwa nayo.',
                'good_conduct': 'Always follow legal procedures and expect equal treatment from authorities.',
                'scope': 'national',
            },
            {
                'law_name': 'Constitution of Tanzania, 1977',
                'article_no': '14',
                'category': 'Basic Rights',
                'content_official_en': 'Every person has the right to live and to the protection of his life by the society in accordance with the law.',
                'content_official_sw': 'Kila mtu anayo haki ya kuishi na kupata hifadhi ya maisha yake kutoka kwa jamii kwa mujibu wa sheria.',
                'plain_summary_en': 'You have the right to stay alive and be safe. The government and society must protect your life.',
                'plain_summary_sw': 'Una haki ya kuishi na kuwa salama. Serikali na jamii lazima zilinde maisha yako.',
                'good_conduct': 'Respect the lives of others and seek help from authorities if your life is in danger.',
                'scope': 'national',
            },
            {
                'law_name': 'Constitution of Tanzania, 1977',
                'article_no': '15',
                'category': 'Basic Rights',
                'content_official_en': 'Every person has the right to and is entitled to personal freedom.',
                'content_official_sw': 'Kila mtu anayo haki ya kuwa huru na kuishi kama mtu huru.',
                'plain_summary_en': 'You have the right to your personal freedom. You cannot be arrested or detained without a valid legal reason.',
                'plain_summary_sw': 'Una haki ya kuwa huru. Huwezi kukamatwa au kufungwa bila sababu halali ya kisheria.',
                'good_conduct': 'If arrested, calmly ask for the reason and your right to speak to a lawyer or family member. Do not resist violently.',
                'scope': 'national',
            },
            {
                'law_name': 'Penal Code (Sura ya 16)',
                'article_no': '258',
                'category': 'Criminal Law',
                'content_official_en': 'A person who fraudulently and without any claim of right taking anything capable of being stolen is guilty of theft.',
                'content_official_sw': 'Mtu yeyote ambaye kwa udanganyifu na bila kudai haki ya kumiliki anachukua kitu kinachoweza kuibiwa anapaswa kuadhibiwa kwa kosa la wizi.',
                'plain_summary_en': 'Taking someone else\'s property without their permission and with the intent to keep it is theft.',
                'plain_summary_sw': 'Kuchukua mali ya mtu mwingine bila ridhaa yake kwa lengo la kuimiliki ni wizi.',
                'good_conduct': 'Never take items that do not belong to you. If you find lost property, report it to the nearest police station.',
                'penalty_summary': 'Imprisonment for up to seven years unless otherwise specified.',
                'scope': 'national',
            },
            {
                'law_name': 'Employment and Labour Relations Act, 2004',
                'article_no': '15',
                'category': 'Labour Law',
                'content_official_en': 'An employer shall supply an employee with written particulars of the employment.',
                'content_official_sw': 'Mwajiri atampatia mfanyakazi maelezo ya maandishi ya ajira yake.',
                'plain_summary_en': 'Every worker has the right to a written employment contract explaining their salary, hours, and duties.',
                'plain_summary_sw': 'Kila mfanyakazi ana haki ya kupewa mkataba wa maandishi unaoelezea mshahara, saa za kazi, na majukumu yake.',
                'good_conduct': 'Always ask for a written contract before starting a job. Keep a copy for your records.',
                'scope': 'national',
            },
            {
                'law_name': 'Road Traffic Act',
                'article_no': '63',
                'category': 'Traffic Law',
                'content_official_en': 'Any person who, when driving or attempting to drive a motor vehicle on a road or other public place, is under the influence of drink or a drug is guilty of an offence.',
                'content_official_sw': 'Mtu yeyote ambaye, wakati akiendesha au akijaribu kuendesha chombo cha moto barabarani, anakuwa chini ya ushawishi wa kinywaji au dawa anakuwa na hatia ya kosa la jinai.',
                'plain_summary_en': 'Driving while drunk or under the influence of drugs is strictly prohibited.',
                'plain_summary_sw': 'Kuendesha gari ukiwa umelewa au kutumia dawa za kulevya ni kosa la kisheria.',
                'good_conduct': 'Do not drive if you have consumed alcohol. Use public transport or a designated driver.',
                'penalty_summary': 'Fine and/or imprisonment, and potential disqualification from driving.',
                'scope': 'national',
            },
            {
                'law_name': 'Kinondoni Municipal Council (Health and Sanitation) Bylaws, 2017',
                'article_no': '4',
                'category': 'Environmental Law',
                'content_official_en': 'No person shall throw, deposit or discharge any litter or waste onto any street, public place or unallocated land.',
                'content_official_sw': 'Ni marufuku kwa mtu yeyote kutupa, kuweka au kumwaga takataka yoyote barabarani, mahali pa umma au kwenye ardhi ambayo haijatengwa.',
                'plain_summary_en': 'Littering in public places, streets, or open spaces in Kinondoni is a crime and attracts fines.',
                'plain_summary_sw': 'Kutupa takataka ovyo barabarani au maeneo ya wazi kule Kinondoni ni kosa na linaweza kupelekea faini.',
                'good_conduct': 'Always use designated trash bins. In Kinondoni, ensure you have a contract with a registered waste collection service for your household.',
                'penalty_summary': 'Fine of not less than 50,000 TZS or imprisonment for a term not exceeding 3 months.',
                'scope': 'regional',
                'region': 'Kinondoni, Dar es Salaam',
            },
            {
                'law_name': 'Moshi Municipal Council (Environmental Protection) Bylaws',
                'article_no': '12',
                'category': 'Environmental Law',
                'content_official_en': 'Every owner or occupier of a premises shall ensure that the frontage of his premises is kept clean and all trees or gardens are well maintained.',
                'content_official_sw': 'Kila mmiliki au mkazi wa nyumba atahakikisha kuwa mbele ya nyumba yake pako safi na miti au bustani zote zimepaliliwa na kutunzwa vizuri.',
                'plain_summary_en': 'In Moshi, you are responsible for keeping the area in front of your house clean and maintaining any greenery.',
                'plain_summary_sw': 'Huko Moshi, ni wajibu wako kuhakikisha eneo lililo mbele ya nyumba yako ni safi na miti au maua yaliyopandwa yanatunzwa.',
                'good_conduct': 'Clean your surroundings every morning. Moshi is known for its cleanliness; help maintain this reputation.',
                'scope': 'regional',
                'region': 'Moshi, Kilimanjaro',
            },
        ]

        for law_data in laws:
            obj, created = LawProvision.objects.update_or_create(
                law_name=law_data['law_name'],
                article_no=law_data['article_no'],
                defaults=law_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Law: Article {law_data['article_no']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated Law: Article {law_data['article_no']}"))
