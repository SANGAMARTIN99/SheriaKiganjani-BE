import os
import re
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from apps.laws.models import LawProvision
from django.conf import settings
from langchain_groq import ChatGroq


# ─────────────────────────────────────────────────────────────────────────────
# LLM & Embedding helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.GROQ_API_KEY,
        temperature=0.3,
        max_tokens=1500,
    )


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY
    )


# ─────────────────────────────────────────────────────────────────────────────
# Intent Detection — classify what the user actually wants
# ─────────────────────────────────────────────────────────────────────────────

GREETING_PATTERNS = [
    r'\b(habari|hujambo|mambo|salama|shikamoo|niaje|vipi|sasa|safi)\b',
    r'\b(hello|hi|hey|good morning|good afternoon|good evening|good day|greetings)\b',
    r'\b(how are you|how do you do|what\'s up|sup|howdy)\b',
    r'^\s*(hi|hey|hello|habari|hujambo|mambo)\s*[!?.]*\s*$',
]

FAREWELL_PATTERNS = [
    r'\b(bye|goodbye|kwaheri|tutaonana|baadaye|asante sana|nashukuru|thank you|thanks)\b',
    r'\b(see you|later|take care|all good|done|finished|nimekwisha)\b',
]

IDENTITY_PATTERNS = [
    r'\b(wewe ni nani|who are you|what are you|unafanya nini|what do you do)\b',
    r'\b(nikusaidie|unaweza|can you help|tell me about yourself|jina lako|your name)\b',
    r'\b(sheria kiganjani|ai|bot|robot|programu|app|system)\b',
]

PRAISE_PATTERNS = [
    r'\b(asante|thank|sawa sawa|nzuri|vizuri|hongera|excellent|perfect|great|awesome|wonderful|amazing)\b',
    r'\b(umesaidia|good job|well done|bravo|umejibu|best|smart|clever)\b',
]

SMALL_TALK_PATTERNS = [
    r'\b(unafikiria|what do you think|opinion|maoni|hisia|feelings)\b',
    r'\b(una familia|do you eat|una njaa|una furaha|are you happy|unachoka)\b',
    r'\b(siasa|politics|michezo|sport|muziki|music|sinema|movie|mchezo)\b',
]

HELP_PATTERNS = [
    r'\b(saidie|help me|niambie|tell me|eleza|explain|nieleze|nataka kujua|what is|ni nini|maana|meaning)\b',
    r'\b(naweza|i want|i need|i have|nina|nataka|ninatafuta|looking for)\b',
]

OUT_OF_SCOPE_SIGNALS = [
    r'\b(dawa|medicine|doctor|daktari|hospital|hospitali|afya|health|clinical)\b',
    r'\b(hali ya hewa|weather|mvua|jua|baridi|temperature|forecast)\b',
    r'\b(recipes|mapishi|cook|kupika|chakula|food|restaurant)\b',
    r'\b(jiografia|geography|historia|history|nchi|country|capital|mji mkuu)\b',
    r'\b(hesabu|math|science|sayansi|physics|chemistry|biology)\b',
    r'\b(mpira|football|basketball|cricket|tennis|sport|mchezo wa)\b',
]


def classify_intent(query: str) -> str:
    """
    Returns one of: 'greeting', 'farewell', 'identity', 'praise',
    'small_talk', 'out_of_scope', 'legal_query'
    """
    q_lower = query.lower().strip()

    for pattern in GREETING_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return 'greeting'

    for pattern in FAREWELL_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return 'farewell'

    for pattern in IDENTITY_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return 'identity'

    for pattern in PRAISE_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return 'praise'

    for pattern in SMALL_TALK_PATTERNS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return 'small_talk'

    # Short queries (< 4 words) with no legal indicators are likely non-legal
    word_count = len(q_lower.split())
    if word_count < 4:
        legal_keywords = [
            'sheria', 'haki', 'mahakama', 'polisi', 'kesi', 'kifungo', 'adhabu',
            'law', 'court', 'rights', 'arrest', 'crime', 'legal', 'constitution',
            'katiba', 'mkataba', 'ardhi', 'kazi', 'mwajiri', 'faini', 'rufaa',
        ]
        has_legal = any(kw in q_lower for kw in legal_keywords)
        if not has_legal:
            return 'greeting'  # Treat as conversational

    for pattern in OUT_OF_SCOPE_SIGNALS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            return 'out_of_scope'

    return 'legal_query'


# ─────────────────────────────────────────────────────────────────────────────
# RAG Retrieval
# ─────────────────────────────────────────────────────────────────────────────

SIMILARITY_THRESHOLD = 0.50  # cosine distance — lower means more relevant


def retrieve_relevant_laws(query, k=5):
    """
    Retrieves the most relevant law provisions using pgvector similarity search.
    Returns provisions that pass the similarity threshold plus their distances.
    """
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)

    from pgvector.django import CosineDistance

    laws = LawProvision.objects.annotate(
        distance=CosineDistance('embedding', query_vector)
    ).order_by('distance').filter(is_active=True, distance__lte=SIMILARITY_THRESHOLD)[:k]

    return list(laws)


# ─────────────────────────────────────────────────────────────────────────────
# Canned Responses for Non-Legal Intents
# ─────────────────────────────────────────────────────────────────────────────

def get_greeting_response(language: str) -> str:
    if language == 'sw':
        return (
            "Habari sana! 👋 Karibu kwenye **Sheria Kiganjani** — msaidizi wako wa kisheria wa Tanzania.\n\n"
            "Mimi ni AI iliyoundwa maalum kuelewa na kueleza sheria za Tanzania kwa lugha rahisi. "
            "Ninaweza kukusaidia kuhusu:\n\n"
            "• 📜 **Katiba ya Tanzania** (haki zako za msingi)\n"
            "• ⚖️ **Sheria ya Jinai** (makosa ya jinai na adhabu)\n"
            "• 👷 **Sheria ya Kazi** (haki za mfanyakazi)\n"
            "• 🏠 **Sheria ya Ardhi** (umiliki wa ardhi na migogoro)\n"
            "• 🏛️ **Sheria za Serikali za Mitaa** (kanuni za manispaa)\n\n"
            "Niambie — unajua nini unachotaka kujua? 😊\n\n"
            "---\n"
            "*Sheria Kiganjani ni AI wa kisheria wa Tanzania. Kwa ushauri wa kisheria rasmi, wasiliana na wakili aliye na leseni.*"
        )
    else:
        return (
            "Hello! 👋 Welcome to **Sheria Kiganjani** — your Tanzanian legal awareness assistant.\n\n"
            "I am an AI specifically built to help you understand Tanzanian law in plain, accessible language. "
            "I can assist you with:\n\n"
            "• 📜 **Constitution of Tanzania** (your fundamental rights)\n"
            "• ⚖️ **Criminal Law** (offences and penalties)\n"
            "• 👷 **Labour Law** (workers' rights)\n"
            "• 🏠 **Land Law** (land ownership and disputes)\n"
            "• 🏛️ **Local Government By-laws** (municipal regulations)\n\n"
            "What legal topic would you like to explore today? 😊\n\n"
            "---\n"
            "*Sheria Kiganjani is a Tanzanian legal AI. For formal legal advice, please consult a licensed lawyer.*"
        )


def get_farewell_response(language: str) -> str:
    if language == 'sw':
        return (
            "Asante kwa kutumia **Sheria Kiganjani**! 🙏\n\n"
            "Ninafurahi kukusaidia kuelewa sheria za Tanzania. "
            "Ukihitaji usaidizi wowote wa kisheria tena, niambie wakati wowote.\n\n"
            "Tutaonana! Na kumbuka — **Sheria ni Haki yako**. 💚\n\n"
            "---\n"
            "*Sheria Kiganjani — AI ya Kisheria ya Tanzania.*"
        )
    else:
        return (
            "Thank you for using **Sheria Kiganjani**! 🙏\n\n"
            "It was a pleasure helping you understand Tanzanian law. "
            "Whenever you need legal guidance again, I am always here.\n\n"
            "Goodbye! And remember — **The Law is Your Right**. 💚\n\n"
            "---\n"
            "*Sheria Kiganjani — Tanzania's Legal AI.*"
        )


def get_identity_response(language: str) -> str:
    if language == 'sw':
        return (
            "Mimi ni **Sheria Kiganjani** 🤖 — AI ya kisheria iliyoundwa mahsusi kwa Tanzania.\n\n"
            "**Ninachofanya:**\n"
            "Nasaidia wananchi wa Tanzania kuelewa haki zao za kisheria kwa lugha rahisi ya Kiswahili na Kiingereza. "
            "Ninategemea maktaba ya sheria za Tanzania ikiwemo Katiba, Sheria ya Jinai, Sheria ya Kazi, Sheria ya Ardhi, na kanuni za manispaa.\n\n"
            "**Ninafanya kazi kwa kutumia:**\n"
            "• 🧠 AI ya kisasa (LLM - Large Language Model)\n"
            "• 📚 Maktaba ya kisheria ya Tanzania (RAG - Retrieval Augmented Generation)\n"
            "• 🔍 Utafutaji wa kisemantiki (vector embeddings)\n\n"
            "**Muhimu kujua:**\n"
            "Mimi ni msaidizi wa uelewa wa kisheria — sio badala ya wakili. "
            "Kwa mambo mazito ya kisheria, tafadhali wasiliana na wakili aliye na leseni.\n\n"
            "Niambie — una swali gani la kisheria? ⚖️\n\n"
            "---\n"
            "*Sheria Kiganjani — AI ya Kisheria ya Tanzania.*"
        )
    else:
        return (
            "I am **Sheria Kiganjani** 🤖 — a legal AI built specifically for Tanzania.\n\n"
            "**What I do:**\n"
            "I help Tanzanian citizens understand their legal rights in plain, accessible Swahili and English. "
            "I draw from a curated database of Tanzanian laws including the Constitution, Penal Code, "
            "Labour Relations Act, Land Laws, and local government by-laws.\n\n"
            "**How I work:**\n"
            "• 🧠 Advanced AI (LLM - Large Language Model)\n"
            "• 📚 Tanzanian legal knowledge base (RAG - Retrieval Augmented Generation)\n"
            "• 🔍 Semantic search (vector embeddings)\n\n"
            "**Important to know:**\n"
            "I am a legal awareness tool — not a replacement for a lawyer. "
            "For serious legal matters, please consult a licensed legal practitioner.\n\n"
            "What legal question can I help you with? ⚖️\n\n"
            "---\n"
            "*Sheria Kiganjani — Tanzania's Legal AI.*"
        )


def get_praise_response(language: str) -> str:
    if language == 'sw':
        return (
            "Asante sana kwa maneno mazuri! 😊🙏\n\n"
            "Ninafurahi sana kukusaidia. Lengo langu ni kuhakikisha kila mwananchi wa Tanzania "
            "anaelewa haki zake za kisheria bila kuhitaji elimu ya sheria.\n\n"
            "Una swali lingine lolote la kisheria? Niko hapa kukusaidia! ⚖️\n\n"
            "---\n"
            "*Sheria Kiganjani — AI ya Kisheria ya Tanzania.*"
        )
    else:
        return (
            "Thank you so much for the kind words! 😊🙏\n\n"
            "It is truly my purpose to ensure every Tanzanian citizen can access and understand "
            "their legal rights without needing a law degree.\n\n"
            "Do you have any other legal questions? I am here to help! ⚖️\n\n"
            "---\n"
            "*Sheria Kiganjani — Tanzania's Legal AI.*"
        )


def get_small_talk_response(language: str, query: str) -> str:
    if language == 'sw':
        return (
            "Naelewa swali lako, lakini lazima nikuambie kwa uaminifu — **mimi ni AI ya kisheria** iliyoundwa "
            "kwa Tanzania, kwa hiyo mambo ya kawaida ya mazungumzo si utaalamu wangu. 😊\n\n"
            "Ninachojua vizuri sana ni:\n"
            "• ⚖️ Haki za kisheria za Watanzania\n"
            "• 📜 Katiba na sheria za Tanzania\n"
            "• 🏛️ Miongozo ya kisheria na ushauri wa jinsi ya kulinda haki zako\n\n"
            "Je, una swali lolote kuhusu sheria za Tanzania? Hiyo ndiyo eneo langu la ubingwa. 💪\n\n"
            "---\n"
            "*Sheria Kiganjani — AI ya Kisheria ya Tanzania.*"
        )
    else:
        return (
            "I appreciate your message! But I should be honest — **I am a Tanzanian legal AI**, "
            "purpose-built for legal awareness. Everyday small talk is outside my expertise. 😊\n\n"
            "What I do really well is:\n"
            "• ⚖️ Tanzanian citizens' legal rights\n"
            "• 📜 The Constitution and laws of Tanzania\n"
            "• 🏛️ Legal guidance and how to protect your rights\n\n"
            "Do you have a legal question I can help with? That is where I shine! 💪\n\n"
            "---\n"
            "*Sheria Kiganjani — Tanzania's Legal AI.*"
        )


def get_out_of_scope_response(language: str, query: str) -> str:
    if language == 'sw':
        return (
            "Naelewana nawe! Lakini swali lako halihusu eneo langu la kisheria. 🙏\n\n"
            "**Mimi ni Sheria Kiganjani** — AI iliyoundwa mahsusi kwa sheria za Tanzania peke yake. "
            "Sijaundwa kwa dawa, siasa, michezo, hali ya hewa, au mada nyingine za jumla.\n\n"
            "**Ninachoweza kukusaidia:**\n"
            "• 📜 Haki zako katika Katiba ya Tanzania\n"
            "• ⚖️ Sheria za jinai na adhabu\n"
            "• 👷 Haki za mfanyakazi\n"
            "• 🏠 Sheria ya ardhi na umiliki wa mali\n"
            "• 🏛️ Kanuni za manispaa na serikali za mitaa\n\n"
            "Je, una swali lolote la kisheria ambalo ninaweza kukusaidia nalo? 😊\n\n"
            "---\n"
            "*Sheria Kiganjani — AI ya Kisheria ya Tanzania. Kwa masuala mengine, tafadhali tumia zana zinazofaa.*"
        )
    else:
        return (
            "I appreciate your question! However, it falls outside my area of expertise. 🙏\n\n"
            "**I am Sheria Kiganjani** — an AI built specifically and exclusively for Tanzanian law. "
            "I am not designed for medicine, sports, weather, general knowledge, or other topics.\n\n"
            "**What I can help you with:**\n"
            "• 📜 Your rights under the Constitution of Tanzania\n"
            "• ⚖️ Criminal law and penalties\n"
            "• 👷 Workers' rights and labour law\n"
            "• 🏠 Land law and property ownership\n"
            "• 🏛️ Municipal by-laws and local government regulations\n\n"
            "Do you have a legal question I can assist you with? 😊\n\n"
            "---\n"
            "*Sheria Kiganjani — Tanzania's Legal AI. For other topics, please use an appropriate tool.*"
        )


def get_no_law_found_response(language: str) -> str:
    if language == 'sw':
        return (
            "Nimejaribu kutafuta katika maktaba yetu ya kisheria, lakini sijapata sheria inayohusiana "
            "moja kwa moja na swali lako. 🔍\n\n"
            "**Hii inaweza kumaanisha:**\n"
            "• Swali lako linahitaji utaalamu wa kina wa kisheria\n"
            "• Maktaba yetu bado inaongezwa na sheria zaidi\n"
            "• Au swali linahitaji msaada wa wakili mwenye uzoefu\n\n"
            "**Hatua zinazoshauriwa:**\n"
            "• 👨‍⚖️ Wasiliana na wakili aliyesajiliwa Tanzania\n"
            "• 🏛️ Tembelea Ofisi ya Msaada wa Kisheria (Legal Aid) karibu nawe\n"
            "• 📞 Piga simu Baraza la Taifa la Msaada wa Kisheria: **0800110030** (bure)\n"
            "• 🌐 Tembelea: [Tanganyika Law Society](https://www.tls.or.tz)\n\n"
            "---\n"
            "⚠️ *Taarifa hizi ni kwa uelewa wa kisheria tu. Kwa mambo mazito, wasiliana na wakili aliye na leseni.*\n\n"
            "*Sheria Kiganjani — AI ya Kisheria ya Tanzania.*"
        )
    else:
        return (
            "I searched our legal knowledge base but could not find a law that directly addresses "
            "your question. 🔍\n\n"
            "**This may mean:**\n"
            "• Your question requires in-depth legal expertise\n"
            "• Our database is still being expanded with more laws\n"
            "• Or the matter needs an experienced legal practitioner\n\n"
            "**Recommended steps:**\n"
            "• 👨‍⚖️ Consult a registered lawyer in Tanzania\n"
            "• 🏛️ Visit your nearest Legal Aid office\n"
            "• 📞 Call the National Legal Aid Hotline: **0800110030** (toll-free)\n"
            "• 🌐 Visit: [Tanganyika Law Society](https://www.tls.or.tz)\n\n"
            "---\n"
            "⚠️ *This information is for legal awareness only. For serious matters, consult a licensed legal practitioner.*\n\n"
            "*Sheria Kiganjani — Tanzania's Legal AI.*"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main Legal Response Generator
# ─────────────────────────────────────────────────────────────────────────────

def get_legal_response(query, language='sw'):
    """
    Full AI pipeline:
    1. Classify intent
    2. Route to canned response OR RAG pipeline
    3. Return structured response with optional citations
    """
    # Step 1: Classify intent
    intent = classify_intent(query)

    # Step 2: Route based on intent
    if intent == 'greeting':
        return {'text': get_greeting_response(language), 'citations': [], 'intent': intent}

    if intent == 'farewell':
        return {'text': get_farewell_response(language), 'citations': [], 'intent': intent}

    if intent == 'identity':
        return {'text': get_identity_response(language), 'citations': [], 'intent': intent}

    if intent == 'praise':
        return {'text': get_praise_response(language), 'citations': [], 'intent': intent}

    if intent == 'small_talk':
        return {'text': get_small_talk_response(language, query), 'citations': [], 'intent': intent}

    if intent == 'out_of_scope':
        return {'text': get_out_of_scope_response(language, query), 'citations': [], 'intent': intent}

    # Step 3: Legal query — run RAG
    return _generate_legal_rag_response(query, language)


def _generate_legal_rag_response(query: str, language: str) -> dict:
    """
    Full RAG pipeline for legal questions.
    Returns dict with 'text', 'citations', and 'intent'.
    """
    llm = get_llm()
    relevant_laws = retrieve_relevant_laws(query)
    has_context = len(relevant_laws) > 0

    if not has_context:
        return {
            'text': get_no_law_found_response(language),
            'citations': [],
            'intent': 'legal_query'
        }

    # Build context string and citations
    context_text = ""
    citations = []

    for law in relevant_laws:
        if language == 'sw':
            context_text += (
                f"Sheria: {law.law_name} | Ibara: {law.article_no} | Aina: {law.category}\n"
                f"Maelezo Rasmi: {law.content_official_sw}\n"
                f"Muhtasari Rahisi: {law.plain_summary_sw}\n"
                f"Ushauri wa Maadili: {law.good_conduct}\n"
            )
            if law.penalty_summary:
                context_text += f"Adhabu: {law.penalty_summary}\n"
            context_text += "\n"
        else:
            context_text += (
                f"Law: {law.law_name} | Article: {law.article_no} | Category: {law.category}\n"
                f"Official Text: {law.content_official_en}\n"
                f"Plain Summary: {law.plain_summary_en}\n"
                f"Good Conduct Advice: {law.good_conduct}\n"
            )
            if law.penalty_summary:
                context_text += f"Penalty: {law.penalty_summary}\n"
            context_text += "\n"

        citations.append({
            'law_name': law.law_name,
            'article_no': law.article_no,
            'category': law.category,
        })

    if language == 'sw':
        system_prompt = """Wewe ni Sheria Kiganjani — msaidizi mkuu wa kisheria wa AI kwa Tanzania. \
Unazungumza Kiswahili sanifu cha Tanzania kwa njia ya kirafiki, wazi, na ya kuaminika.

KANUNI KUU (LAZIMA UZIFUATE):
1. Tumia TU maelezo yaliyotolewa katika "Muktadha wa Kisheria" hapa chini. Usibuni wala kukisia sheria.
2. Jibu liwe wazi, laini, na rahisi kuelewa — kama rafiki anayekusaidia, sio kama jaji.
3. Tumia emojis kidogo ili jibu lisionekane gumu (mf: ⚖️ 📜 ✅ ⚠️ 👋).
4. Panga jibu vizuri kwa kutumia headers, bullet points, na bold text inapohitajika.
5. Daima taja sheria au ibara uliyoitumia (mf: "Kulingana na Ibara ya 15 ya Katiba...").
6. DAIMA maliza jibu na mstari huu: "---\\n⚠️ *Taarifa hizi ni kwa uelewa wa kisheria tu. Kwa mambo mazito, wasiliana na wakili aliye na leseni.*\\n\\n*Sheria Kiganjani — AI ya Kisheria ya Tanzania.*"

MUUNDO WA JIBU (Kiswahili):
- **Kuelewa hali yako** — tambua tatizo kwa urahisi
- **Sheria inasema nini** — eleza kwa lugha rahisi ukitaja vyanzo
- **Hatua za kuchukua** — pendekeza vitendo vya vitendo
- **Onyo la kisheria** — daima mwishoni"""
    else:
        system_prompt = """You are Sheria Kiganjani — Tanzania's premier legal AI assistant. \
You speak clear, warm, and trustworthy English.

STRICT RULES (NON-NEGOTIABLE):
1. Use ONLY the information in the "Legal Context" below. Never fabricate or guess laws.
2. Be clear, friendly, and accessible — like a knowledgeable friend, not a judge.
3. Use emojis sparingly to make responses feel approachable (e.g., ⚖️ 📜 ✅ ⚠️ 👋).
4. Structure responses well using headers, bullet points, and bold text where needed.
5. Always cite the law or article you are referencing (e.g., "Under Article 15 of the Constitution...").
6. ALWAYS end with: "---\\n⚠️ *This information is for legal awareness only. For serious matters, consult a licensed legal practitioner.*\\n\\n*Sheria Kiganjani — Tanzania's Legal AI.*"

RESPONSE STRUCTURE (English):
- **Understanding your situation** — identify the issue simply
- **What the law says** — explain in plain language, citing sources
- **Steps to take** — suggest practical, actionable advice
- **Legal disclaimer** — always at the end"""

    lang_label = "Kiswahili sanifu" if language == 'sw' else "clear English"

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"""Muktadha wa Kisheria / Legal Context:
{context_text}

Swali / Question: {{query}}

Jibu kwa {lang_label} — jibu liwe kamili, la kirafiki, na lenye msaada wa kweli:""")
    ])

    chain = final_prompt | llm | StrOutputParser()
    response_text = chain.invoke({"query": query})

    return {
        'text': response_text,
        'citations': citations,
        'intent': 'legal_query'
    }
