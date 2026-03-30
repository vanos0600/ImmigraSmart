"""
rag_engine.py — ImmigraSmart RAG Engine (v7 — Language Response Fix)

BUGS FIXED vs v6:
  BUG C — COMBINED_PREP_PROMPT rewrote follow-up questions without any
    language instruction. When a user wrote in Czech, the prep LLM would
    rewrite the standalone question in English (since the knowledge base is
    in English). The final answer LLM then received an English question as
    its "human" turn and — despite the language_instruction in the system
    prompt — defaulted to responding in English.
    FIX: Added explicit note in COMBINED_PREP_PROMPT that rewriting must be
    in English for internal search purposes only, keeping retrieval correct
    while making the intent clear.

  BUG D — chain.invoke() passed `variants[0]` (the English-rewritten query)
    as the human turn in the answer prompt. The LLM anchors its response
    language to the human turn, not the system prompt, so English query →
    English answer regardless of language_instruction.
    FIX: chain.invoke() now passes `clean_input` (the original user message
    with PII removed, in the user's language) as the human turn. variants
    are used ONLY for retrieval, never for the final answer generation.
"""

import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from pii_scrubber import scrub
from lang_detect import detect_language, get_language_instruction

load_dotenv()

PERSIST_DIR          = "/tmp/vector_db"
RETRIEVER_K          = 6

# ── Keyword → Section boost map ───────────────────────────────────────────────
# Pure string matching → ChromaDB metadata filter. Zero LLM calls.

KEYWORD_SECTION_MAP = [
    (["work", "job", "employ", "earn", "internship", "salary", "wage",
      "part-time", "full-time", "trabajar", "trabajo", "practicas",
      "работ", "стажировк", "làm việc", "工作", "实习"],
     "student_employment"),

    (["money", "bank", "funds", "financial", "account", "savings",
      "scholarship", "sponsor", "balance", "czk", "euros", "afford",
      "dinero", "cuenta", "beca", "деньги", "счёт", "стипендия"],
     "financial_requirements"),

    (["insurance", "health", "pvzp", "vzp", "pojisteni", "medical",
      "coverage", "seguro", "salud", "страховка", "медицинская"],
     "health_insurance"),

    (["bridge", "label", "štítek", "překlenovací", "sticker",
      "expir", "extend", "renew", "extension", "renewal",
      "vencida", "renovar", "prórroga"],
     "residence_extension"),

    (["arriv", "register", "biometric", "fingerprint", "oamp",
      "foreign police", "llegada", "registro", "llegué",
      "прибыть", "регистрация"],
     "arrival_biometrics"),

    (["deport", "expel", "illegal", "overstay", "exit order",
      "výjezdní", "revok", "criminal", "offence", "violation"],
     "expulsion_violations"),

    (["appeal", "reject", "data box", "datová", "schránka",
      "apelación", "rechazado", "апелляция"],
     "legal_appeals_databox"),

    (["graduate", "graduation", "diploma", "job seeker", "after study",
      "post study", "find job", "start business", "9 month",
      "graduación", "después de estudiar"],
     "post_graduation"),
]

AMBIGUOUS_TERMS = [
    "my visa", "my permit", "my residence", "my stay",
    "mi visa", "mi permiso", "ma visa", "mon permis",
    "mein visum", "моя виза", "мой пермит",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def format_docs_with_sources(docs) -> str:
    if not docs:
        return "No relevant information found in the knowledge base."
    formatted = []
    for i, doc in enumerate(docs, 1):
        meta    = doc.metadata
        section = meta.get("section_title", meta.get("section_id", "General Information"))
        sub     = meta.get("sub_section", "")
        label   = f"{section} — {sub}" if sub else section
        formatted.append(f"[Source {i}: {label}]\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)


def detect_target_sections(question: str) -> list[str]:
    q = question.lower()
    return [
        section_id
        for keywords, section_id in KEYWORD_SECTION_MAP
        if any(kw in q for kw in keywords)
    ]


def is_ambiguous(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in AMBIGUOUS_TERMS)


# ── Prompts ────────────────────────────────────────────────────────────────────

# FIX BUG C: Added explicit note that rewriting is for internal retrieval
# in English only. This prevents the prep LLM from rewriting Czech/Spanish/etc.
# questions in a way that would confuse the answer LLM's language choice.
COMBINED_PREP_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are helping retrieve Czech immigration law documents. "
     "Given the conversation history and the latest user question:\n"
     "1. Rewrite the question to be fully self-contained (preserve EU/non-EU status and visa type).\n"
     "2. Write 2 alternative phrasings for better search coverage.\n\n"
     "IMPORTANT: Always rewrite in English — these variants are for internal "
     "vector search only and are NEVER shown to the user. The user's original "
     "language is handled separately for the final response.\n\n"
     "Return EXACTLY 3 lines — no numbering, no labels:\n"
     "Line 1: standalone question\n"
     "Line 2: variant A\n"
     "Line 3: variant B"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

BASE_SYSTEM_PROMPT = """You are ImmigraSmart, a professional AI immigration consultant \
specializing in Czech Republic visa and residence permit regulations for international students.

YOUR ROLE:
- Answer based ONLY on the provided legal context below.
- Cite the source section (e.g. "According to Section 9: Working as a Student...").
- Friendly but professional tone — users are often stressed.
- Highlight deadlines and CZK amounts clearly.
- If action is needed, give a numbered step-by-step list.
- If visa type is unclear, ask ONE clarifying question before answering.

STRICT RULES:
- Use ONLY the LEGAL CONTEXT. Never use general knowledge.
- TRANSLATION MANDATORY: The provided context is in English, but you MUST freely translate your final answer into the user's language without apologizing. Translating does NOT violate the rule of using only the provided context.
- If context lacks the answer: "I don't have specific information about that. \
  Please contact OAMP at +420 974 801 801 or visit frs.gov.cz."
- Never fabricate deadlines, amounts, or legal requirements.
- Never give legal advice — information only.
- For deportation/revocation risks: refer to SIMI (migrace.com) or OPU (opu.cz).

--- LEGAL CONTEXT ---
{context}
--- END CONTEXT ---

{language_instruction}"""

# ── Engine Builder ─────────────────────────────────────────────────────────────

def get_rag_chain():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not found. Check your .env file.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
        task_type="retrieval_query",
    )
    vector_db = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
    )
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=api_key,
    )
    retriever = vector_db.as_retriever(search_kwargs={"k": RETRIEVER_K})
    return llm, retriever, vector_db


# ── Stateful Chat Handler ──────────────────────────────────────────────────────

class ImmigraSmartChat:
    """
    ask() → (answer: str, meta: dict)
    meta keys: pii_detected, pii_entities, language, confident, needs_clarify
    """

    def __init__(self):
        self.llm, self.retriever, self.vector_db = get_rag_chain()
        self.chat_history: list = []
        self.parser = StrOutputParser()

    def _prepare_variants(self, clean_input: str) -> list[str]:
        """
        First message → return [original] immediately (0 LLM calls).
        Follow-up → 1 LLM call produces standalone + 2 variants (always in English
        for retrieval purposes — see COMBINED_PREP_PROMPT for rationale).
        """
        if not self.chat_history:
            return [clean_input]
        chain = COMBINED_PREP_PROMPT | self.llm | self.parser
        try:
            raw   = chain.invoke({"chat_history": self.chat_history, "input": clean_input})
            lines = [l.strip() for l in raw.strip().split("\n") if l.strip()][:3]
            return lines if lines else [clean_input]
        except Exception:
            return [clean_input]

    def _retrieve(self, variants: list[str], original_question: str) -> list:
        """
        1. Semantic search across all query variants.
        2. Keyword-boosted metadata filter search for targeted sections.
        Returns deduplicated doc list.
        """
        seen, docs = set(), []

        for v in variants:
            for doc in self.retriever.invoke(v):
                key = doc.page_content[:80]
                if key not in seen:
                    seen.add(key)
                    docs.append(doc)

        # Force-inject relevant sections via metadata filter (no LLM call)
        for section_id in detect_target_sections(original_question):
            try:
                for doc in self.vector_db.similarity_search(
                    original_question, k=3,
                    filter={"section_id": section_id},
                ):
                    key = doc.page_content[:80]
                    if key not in seen:
                        seen.add(key)
                        docs.append(doc)
            except Exception:
                pass

        return docs

    def _update_history(self, user_input: str, answer: str):
        self.chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=answer),
        ])
        if len(self.chat_history) > 12:
            self.chat_history = self.chat_history[-12:]

    def ask(self, user_input: str) -> tuple[str, dict]:
        meta = {
            "pii_detected":  False,
            "pii_entities":  [],
            "language":      "en",
            "confident":     True,
            "needs_clarify": False,
        }

        # 1 — PII scrub (regex, ~0ms)
        scrub_result = scrub(user_input)
        clean_input  = scrub_result.clean_text
        if scrub_result.was_modified:
            meta["pii_detected"] = True
            meta["pii_entities"] = scrub_result.entities_found

        # 2 — Language detection (regex, ~0ms)
        lang_code        = detect_language(user_input)
        meta["language"] = lang_code
        lang_instruction = get_language_instruction(lang_code)

        # 3 — Ambiguity flag (no API call)
        if is_ambiguous(clean_input) and not self.chat_history:
            meta["needs_clarify"] = True

        # 4 — Prepare query variants for retrieval
        #     First message → 0 LLM calls
        #     Follow-up     → 1 LLM call (variants are always in English for
        #                     vector search; original language preserved in
        #                     clean_input for the answer step below)
        variants = self._prepare_variants(clean_input)

        # 5 — Retrieve documents
        #     FIX BUG A (v6): confidence check is AFTER retrieval.
        docs = self._retrieve(variants, clean_input)

        if not docs:
            # Genuine fallback: nothing found even with keyword boost
            meta["confident"] = False
            fallback = (
                "I couldn't find reliable information about that in my knowledge base. "
                "For accurate guidance:\n\n"
                "1. Contact OAMP: **+420 974 801 801**\n"
                "2. Official portal: **frs.gov.cz** or **ipc.gov.cz**\n"
                "3. Free legal aid: **SIMI** (migrace.com) or **OPU** (opu.cz)"
            )
            self._update_history(user_input, fallback)
            return fallback, meta

        context = format_docs_with_sources(docs)

        # 6 — Generate answer (1 LLM call)
        #     FIX BUG D: Pass `clean_input` (user's original language, PII-scrubbed)
        #     as the human turn — NOT variants[0] (which is the English rewrite used
        #     for retrieval). The LLM anchors response language to the human turn,
        #     so sending an English query here caused English responses even when
        #     language_instruction said to respond in Czech/Spanish/etc.
        system_msg = BASE_SYSTEM_PROMPT.format(
            context=context,
            language_instruction=lang_instruction,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        chain  = prompt | self.llm | self.parser
        answer = chain.invoke({
            "chat_history": self.chat_history,
            "input":        clean_input,   # FIX BUG D: was variants[0]
        })

        # 7 — Update history
        self._update_history(user_input, answer)
        return answer, meta

    def reset(self):
        self.chat_history = []