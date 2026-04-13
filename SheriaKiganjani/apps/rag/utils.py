import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from apps.laws.models import LawProvision
from django.conf import settings
from langchain_groq import ChatGroq


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.GROQ_API_KEY,
        temperature=0.05,
        max_tokens=1024,
    )


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY
    )


SIMILARITY_THRESHOLD = 0.45  # cosine distance — lower means more relevant


def retrieve_relevant_laws(query, k=4):
    """
    Retrieves the most relevant law provisions using pgvector similarity search.
    Returns only provisions that pass the similarity threshold.
    """
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)

    from pgvector.django import CosineDistance

    laws = LawProvision.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).order_by('distance').filter(is_active=True, distance__lte=SIMILARITY_THRESHOLD)[:k]

    return list(laws)


def get_legal_response(query, language='sw'):
    llm = get_llm()
    relevant_laws = retrieve_relevant_laws(query)
    has_context = len(relevant_laws) > 0

    context_text = ""
    if has_context:
        for law in relevant_laws:
            if language == 'sw':
                context_text += (
                    f"Sheria: {law.law_name} | Ibara: {law.article_no}\n"
                    f"Maelezo Rasmi: {law.content_official_sw}\n"
                    f"Muhtasari Rahisi: {law.plain_summary_sw}\n"
                    f"Ushauri wa Maadili: {law.good_conduct}\n\n"
                )
            else:
                context_text += (
                    f"Law: {law.law_name} | Article: {law.article_no}\n"
                    f"Official Text: {law.content_official_en}\n"
                    f"Plain Summary: {law.plain_summary_en}\n"
                    f"Good Conduct Advice: {law.good_conduct}\n\n"
                )

    if language == 'sw':
        system_prompt = """Wewe ni Sheria Kiganjani, msaidizi wa uelewa wa kisheria kwa Tanzania. \
Unazungumza Kiswahili sanifu cha Tanzania — sio tafsiri ya mashine bali lugha ya asili, laini, na inayoeleweka.

SHERIA ZA MSINGI (LAZIMA UZIFUATE):
1. Tumia tu maelezo yaliyotolewa katika "Muktadha wa Kisheria" hapa chini. Usibuni wala kukisia sheria.
2. Kama muktadha haufai kwa swali lililoulizwa — sema wazi: "Samahani, sijapata taarifa za kisheria zinazohusiana na swali hili katika mfumo wetu. Naomba uwasiliane na wakili au ofisi ya kisheria karibu nawe."
3. Kamwe usitoe majibu ya uongo au ya kuvumbua — ukweli ni muhimu kuliko kujibu.
4. Jibu liwe fupi, wazi, na la kirafiki — kama rafiki anayekusaidia, si kama jaji.
5. DAIMA jumuisha onyo hili mwishoni: "Taarifa hizi ni kwa uelewa wa kisheria tu. Kwa mambo mazito, wasiliana na wakili aliye na leseni."

MUUNDO WA JIBU (Kiswahili):
- Anza na kutambua hali kwa urahisi
- Toa maelezo ya kisheria kwa lugha rahisi
- Pendekeza hatua za vitendo (ushauri wa maadili)
- Maliza na onyo la kisheria"""
    else:
        system_prompt = """You are Sheria Kiganjani, a legal awareness assistant for Tanzania. \
You speak clear, natural English that is easy to understand.

STRICT RULES (NON-NEGOTIABLE):
1. Use ONLY the information found in the "Legal Context" below. Never fabricate or guess laws.
2. If the context is not relevant to the question — say clearly: "I'm sorry, I don't have specific legal information about this topic in my database. Please consult a qualified lawyer or a nearby legal aid office."
3. Never give false or invented answers — accuracy matters more than appearing helpful.
4. Keep responses brief, clear, and friendly — like a knowledgeable friend, not a judge.
5. ALWAYS end with: "This information is for legal awareness only. For serious matters, please consult a licensed legal practitioner."

RESPONSE STRUCTURE (English):
- Identify the legal situation simply
- Explain the relevant law in plain language
- Suggest practical steps (good conduct)
- End with the legal disclaimer"""

    # Build a structured prompt string (simpler than lambda chains)
    no_context_sw = (
        "Samahani, sijapata taarifa za kisheria zinazohusiana na swali hili katika mfumo wetu. "
        "Muktadha wa kisheria unaopatikana hauhusiani moja kwa moja na swali lako.\n\n"
        "Naomba uzingatie hatua zifuatazo:\n"
        "• Wasiliana na wakili aliyesajiliwa Tanzania\n"
        "• Tembelea Ofisi ya Msaada wa Kisheria (Legal Aid) karibu nawe\n"
        "• Piga simu Baraza la Taifa la Msaada wa Kisheria: 0800110030 (bure)\n\n"
        "⚠️ Taarifa hizi ni kwa uelewa wa kisheria tu. Kwa mambo mazito, wasiliana na wakili aliye na leseni."
    )
    no_context_en = (
        "I'm sorry, I don't have specific legal information relevant to this question in my database. "
        "The available legal context does not directly address your query.\n\n"
        "Please consider these steps:\n"
        "• Consult a registered lawyer in Tanzania\n"
        "• Visit your nearest Legal Aid office\n"
        "• Call the National Legal Aid Hotline: 0800110030 (toll-free)\n\n"
        "⚠️ This information is for legal awareness only. For serious matters, consult a licensed legal practitioner."
    )

    if not has_context:
        return no_context_sw if language == 'sw' else no_context_en

    lang_label = "Kiswahili sanifu" if language == 'sw' else "clear English"

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"""Muktadha wa Kisheria / Legal Context:
{context_text}

Swali / Question: {{query}}

Jibu kwa {lang_label}:""")
    ])

    chain = final_prompt | llm | StrOutputParser()
    return chain.invoke({"query": query})
