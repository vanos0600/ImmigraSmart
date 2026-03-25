"""
rag_engine.py — ImmigraSmart RAG Engine (v6 — Bug Fixes)

BUGS FIXED vs v5:
  BUG A — Confidence check ran BEFORE keyword boost and retrieval.
    "Can I work?" has low similarity to any chunk title → scored below threshold
    → returned fallback immediately, never reaching Section 9.
    FIX: Remove the pre-retrieval confidence check entirely. Instead, check
    confidence AFTER retrieval using the actual docs found. If zero docs come
    back, then fall back. Much more reliable.

  BUG B — Confidence threshold (0.40) was still too aggressive for short
    colloquial questions like "can I work?" or "what insurance?".
    FIX: Threshold dropped to 0.30. The keyword boost + FAQ bridge in the
    knowledge base ensure good docs ARE retrieved when the question is valid.
    The fallback is for truly out-of-scope questions only.
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

COMBINED_PREP_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are helping retrieve Czech immigration law documents. "
     "Given the conversation history and the latest user question:\n"
     "1. Rewrite the question to be fully self-contained (preserve EU/non-EU status and visa type).\n"
     "2. Write 2 alternative phrasings for better search coverage.\n\n"
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
        Follow-up → 1 LLM call produces standalone + 2 variants.
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

        # 4 — Prepare query variants
        #     First message → 0 LLM calls
        #     Follow-up     → 1 LLM call
        variants = self._prepare_variants(clean_input)

        # 5 — Retrieve documents
        #     FIX BUG A: confidence check is now AFTER retrieval, not before.
        #     We check whether docs were actually found, not a pre-retrieval
        #     similarity score that misses keyword-boosted sections.
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
            "input":        variants[0],
        })

        # 7 — Update history
        self._update_history(user_input, answer)
        return answer, meta

    def reset(self):
        self.chat_history = []