import os
import re
from django.core.management.base import BaseCommand
from apps.laws.models import LawProvision
from pypdf import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import time

class Command(BaseCommand):
    help = 'Ingests a Constitution PDF into the LawProvision model with AI enrichment'

    def add_arguments(self, parser):
        parser.add_argument('pdf_path', type=str, help='Path to the PDF file')
        parser.add_argument('--law_name', type=str, required=True, help='Name of the law (e.g., Constitution 1977)')
        parser.add_argument('--language', type=str, choices=['en', 'sw'], default='en', help='Primary language of the PDF')
        parser.add_argument('--scope', type=str, choices=['national', 'regional'], default='national', help='Scope of the law')

    def handle(self, *args, **options):
        pdf_path = options['pdf_path']
        law_name = options['law_name']
        language = options['language']
        scope = options['scope']

        if not os.path.exists(pdf_path):
            self.stderr.write(self.style.ERROR(f"File not found: {pdf_path}"))
            return

        self.stdout.write(self.style.NOTICE(f"Parsing PDF: {pdf_path}..."))
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

        # Simple article segmentation logic
        # Look for " 12. " or " 13. " etc at the start of lines or after double newlines
        articles = self.segment_articles(full_text)
        self.stdout.write(self.style.SUCCESS(f"Found {len(articles)} articles."))

        # Initialize AI
        from django.conf import settings
        from langchain_groq import ChatGroq
        api_key = settings.GEMINI_API_KEY
        groq_key = settings.GROQ_API_KEY
        
        embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key)


        for art_no, content in articles.items():
            # Check if already processed (has plain_summary_sw or en)
            existing = LawProvision.objects.filter(law_name=law_name, article_no=art_no).first()
            if existing and ((language == 'sw' and existing.plain_summary_sw) or (language == 'en' and existing.plain_summary_en)):
                self.stdout.write(f"Skipping Article {art_no} (already enriched)...")
                continue
                
            self.stdout.write(f"Processing Article {art_no}...")
            
            # Enrich with AI
            enriched_data = self.enrich_article(art_no, content, llm)
            
            # Prepare model data
            law_provision_data = {
                'law_name': law_name,
                'article_no': art_no,
                'scope': scope,
            }
            
            if language == 'en':
                law_provision_data['content_official_en'] = content
            else:
                law_provision_data['content_official_sw'] = content
                
            law_provision_data['plain_summary_en'] = enriched_data.get('summary_en')
            law_provision_data['plain_summary_sw'] = enriched_data.get('summary_sw')
            law_provision_data['good_conduct'] = enriched_data.get('good_conduct')
            
            # Generate embedding
            # We embed a combination of official content and summaries for better retrieval
            text_to_embed = f"{law_name} Article {art_no}: {content} {enriched_data.get('summary_en')} {enriched_data.get('summary_sw')}"
            try:
                embedding = embeddings_model.embed_query(text_to_embed)
                law_provision_data['embedding'] = embedding
            except Exception as e:
                self.stderr.write(f"Embedding failed for Art {art_no}: {str(e)}")

            # Save or Update
            provision, created = LawProvision.objects.update_or_create(
                law_name=law_name,
                article_no=art_no,
                defaults=law_provision_data
            )
            
            self.stdout.write(self.style.SUCCESS(f"Article {art_no} ingested."))
            time.sleep(1) # Small delay to stay within Groq TPM limits

    def segment_articles(self, text):
        # Improved regex to find article numbers like " 12. ", "12.-", or "93. "
        # We look for a number followed by a period, potentially with spaces or a dash.
        pattern = r'\n\s*(\d{1,3})\s*\.\s*(?:-)?'
        segments = re.split(pattern, text)

        
        articles = {}
        # segments[0] is intro text before first article
        for i in range(1, len(segments), 2):
            art_no = segments[i]
            content = segments[i+1].strip()
            # Stop if we hit a known footer or next part
            articles[art_no] = content[:5000] # Limit content for now
            
        return articles

    def enrich_article(self, art_no, content, llm):
        prompt = f"""
        Strictly analyze Article {art_no} of the Tanzanian Constitution and return the following in a structured format:
        1. SUMMARY_EN: A concise 2-sentence summary in English.
        2. SUMMARY_SW: A concise 2-sentence summary in Swahili.
        3. CONDUCT: One bullet point on how a good citizen should behave based on this article.

        Structure your response EXACTLY as:
        SUMMARY_EN: [English summary here]
        SUMMARY_SW: [Swahili summary here]
        CONDUCT: [Conduct tip here]

        Article Content:
        {content[:2000]}
        """
        
        max_retries = 2
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                text = response.content
                
                if isinstance(text, list):
                    text = "".join([t.get("text", str(t)) if isinstance(t, dict) else str(t) for t in text])
                
                summary_en_match = re.search(r'SUMMARY_EN:\s*(.*?)(?=SUMMARY_SW:|CONDUCT:|$)', text, re.IGNORECASE | re.DOTALL)
                summary_sw_match = re.search(r'SUMMARY_SW:\s*(.*?)(?=CONDUCT:|SUMMARY_EN:|$)', text, re.IGNORECASE | re.DOTALL)
                conduct_match = re.search(r'CONDUCT:\s*(.*)', text, re.IGNORECASE | re.DOTALL)
                
                return {
                    'summary_en': summary_en_match.group(1).strip() if summary_en_match else "",
                    'summary_sw': summary_sw_match.group(1).strip() if summary_sw_match else "",
                    'good_conduct': conduct_match.group(1).strip() if conduct_match else ""
                }
            except Exception as e:
                if "429" in str(e) or "rate_limit_exceeded" in str(e).lower():
                    self.stdout.write(self.style.WARNING(f"Groq Rate Limit for Art {art_no}. Continuing with raw text..."))
                    break
                else:
                    self.stderr.write(f"AI Enrichment failed for Art {art_no}: {str(e)}")
                    break
        
        return {'summary_en': "", 'summary_sw': "", 'good_conduct': ""}
