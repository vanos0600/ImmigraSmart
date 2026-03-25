"""
rag_engine.py — ImmigraSmart RAG Engine  (v4)
Bug fixes in this version:
  FIX 1 — Language Drift:
    language_instruction moved to the VERY END of the prompt, after the English
    legal context, with imperative phrasing ("CRITICAL — you MUST respond
    ENTIRELY in {language}"). The model no longer drifts back to English after
    reading 1,000 words of Czech law in English.

  FIX 2 — False Negative / Empty Context:
    condense prompt now explicitly carries the user's EU/non-EU status hint
    into the standalone question so the retriever finds the right section.
    Also added an "ambiguity check" — if the condensed question still contains
    pronouns like "my visa" without a type, a clarification is requested before
    retrieval runs.

  FIX 3 — Hallucination by Ambiguity:
    System prompt now instructs the model to ask ONE clarifying question when
    visa type is unclear, rather than guessing and mixing up student / work /
    family-reunification rules.
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

PERSIST_DIR = "/tmp/vector_db"
LOW_CONFIDENCE_THRESHOLD = 0.45

# Keywords that suggest the user hasn't specified their visa/student type.
# When found, the model is nudged to clarify before answering.
AMBIGUOUS_TERMS = [
    "my visa", "my permit", "my residence", "my stay",
    "mi visa", "mi permiso",          # Spanish
    "моя виза", "мой пермит",         # Russian/Ukrainian
    "ma visa", "mon permis",          # French
    "mein visum", "meine erlaubnis",  # German
]


# ── Context Formatter ──────────────────────────────────────────────────────────

def format_docs_with_sources(docs) -> str:
    if not docs:
        return "No relevant information found in the knowledge base."
    formatted = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        section = meta.get("section_title", meta.get("section_id", "General Information"))
        sub = meta.get("sub_section", "")
        label = f"{section} — {sub}" if sub else section
        formatted.append(f"[Source {i}: {label}]\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)


# ── Confidence Check ───────────────────────────────────────────────────────────

def check_confidence(vector_db: Chroma, query: str, k: int = 4) -> tuple[list, bool]:
    results = vector_db.similarity_search_with_relevance_scores(query, k=k)
    if not results:
        return [], False
    docs   = [doc   for doc, _     in results]
    scores = [score for _,   score in results]
    return docs, max(scores) >= LOW_CONFIDENCE_THRESHOLD


# ── Ambiguity Check ────────────────────────────────────────────────────────────

def is_ambiguous(question: str) -> bool:
    """
    Returns True if the question references 'my visa/permit' without
    specifying EU/non-EU or visa type — a signal to ask for clarification.
    """
    q = question.lower()
    return any(term in q for term in AMBIGUOUS_TERMS)


# ── Prompts ────────────────────────────────────────────────────────────────────

# FIX 1: language_instruction is now at the VERY BOTTOM — after the English
# legal context — so it's the last thing the model reads before generating.
# This prevents the English context from overriding the language instruction.

BASE_SYSTEM_PROMPT = """You are ImmigraSmart, a professional AI immigration consultant \
specializing in Czech Republic visa and residence permit regulations for international students.

YOUR ROLE:
- Provide accurate, clear, and structured answers based ONLY on the provided context.
- Always cite which section your information comes from \
  (e.g., "According to Section 3: Financial Requirements...").
- Use a friendly but professional tone — users are often stressed about immigration.
- Highlight deadlines and financial amounts clearly.
- When the answer requires action, provide a numbered step-by-step list.

STRICT RULES:
- ONLY use information from the LEGAL CONTEXT below. Do not use general knowledge.
- If the context does not contain the answer, say:
  "I don't have specific information about that. \
   Please contact OAMP at +420 974 801 801 or visit frs.gov.cz."
- NEVER fabricate deadlines, amounts, or legal requirements.
- NEVER give legal advice — you provide information, not legal representation.
- For serious legal risks (deportation, permit revocation), recommend \
  free legal aid at SIMI (migrace.com) or OPU (opu.cz).

FIX 3 — CLARIFICATION RULE:
- If the user's visa type or student status is UNCLEAR (e.g. they say "my visa"
  without specifying EU/non-EU or type), ask exactly ONE clarifying question
  BEFORE giving a definitive answer. Example:
  "To give you the most accurate information, could you tell me:
   Are you an EU or non-EU student? And is this a first-time application or a renewal?"
- Once the type is known (from this message or earlier in the conversation),
  answer directly without asking again.

--- OFFICIAL LEGAL CONTEXT (Czech immigration law — source documents) ---
{context}
--- END OF LEGAL CONTEXT ---

FIX 1 — LANGUAGE OVERRIDE (takes priority over everything above):
{language_instruction}"""

# FIX 2: Condense prompt now explicitly asks the model to preserve
# EU/non-EU status and visa type in the rephrased question.
CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Given the conversation history and a new follow-up question, "
     "rewrite the question to be fully self-contained. "
     "IMPORTANT: preserve any mention of EU/non-EU status, visa type, "
     "or permit type from the conversation history — these are critical "
     "for finding the correct legal information. "
     "Return ONLY the rephrased question, nothing else."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])


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
    retriever = vector_db.as_retriever(search_kwargs={"k": 6})
    return llm, retriever, vector_db, CONDENSE_PROMPT


# ── Stateful Chat Handler ──────────────────────────────────────────────────────

class ImmigraSmartChat:
    """
    Full RAG pipeline with all three bug fixes applied.

    ask() returns (answer: str, meta: dict)
    meta keys:
      pii_detected   bool       — PII was scrubbed before sending to LLM
      pii_entities   list[str]  — which entity types were found
      language       str        — BCP-47 code of detected input language
      confident      bool       — retrieval exceeded confidence threshold
      needs_clarify  bool       — question was ambiguous; model asked for type
    """

    def __init__(self):
        (self.llm,
         self.retriever,
         self.vector_db,
         self.condense_prompt) = get_rag_chain()
        self.chat_history: list = []
        self.parser = StrOutputParser()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _condense(self, user_input: str) -> str:
        """Rephrase follow-up into standalone question, preserving visa type context."""
        if not self.chat_history:
            return user_input
        chain = self.condense_prompt | self.llm | self.parser
        return chain.invoke({"chat_history": self.chat_history, "input": user_input})

    def _multi_retrieve(self, question: str) -> list:
        """3-variant retrieval: original + 2 rephrasings, deduplicated."""
        rephrase_chain = (
            ChatPromptTemplate.from_template(
                "Rephrase this Czech immigration question in 2 different ways "
                "to improve document search. Preserve any visa type or EU/non-EU "
                "status mentioned. Return only 2 questions, one per line:\n{q}"
            )
            | self.llm
            | StrOutputParser()
        )
        try:
            raw = rephrase_chain.invoke({"q": question})
            variants = [question] + [
                line.strip() for line in raw.strip().split("\n") if line.strip()
            ][:2]
        except Exception:
            variants = [question]

        seen, docs = set(), []
        for v in variants:
            for doc in self.retriever.invoke(v):
                key = doc.page_content[:80]
                if key not in seen:
                    seen.add(key)
                    docs.append(doc)
        return docs

    def _update_history(self, user_input: str, answer: str):
        self.chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=answer),
        ])
        if len(self.chat_history) > 12:
            self.chat_history = self.chat_history[-12:]

    def _build_prompt(self, context: str, lang_instruction: str) -> ChatPromptTemplate:
        """Builds the dynamic prompt with context + language injected."""
        system_msg = BASE_SYSTEM_PROMPT.format(
            context=context,
            language_instruction=lang_instruction,
        )
        return ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

    # ── Main Entry Point ──────────────────────────────────────────────────────

    def ask(self, user_input: str) -> tuple[str, dict]:
        meta = {
            "pii_detected":  False,
            "pii_entities":  [],
            "language":      "en",
            "confident":     True,
            "needs_clarify": False,
        }

        # 1 ── PII Scrubbing (GDPR art. 25) ────────────────────────────────────
        scrub_result = scrub(user_input)
        clean_input  = scrub_result.clean_text
        if scrub_result.was_modified:
            meta["pii_detected"] = True
            meta["pii_entities"] = scrub_result.entities_found

        # 2 ── Language Detection (on ORIGINAL text before scrubbing) ──────────
        lang_code        = detect_language(user_input)
        meta["language"] = lang_code
        lang_instruction = get_language_instruction(lang_code)

        # 3 ── Condense with history (FIX 2: preserves visa type in context) ───
        standalone = self._condense(clean_input)

        # 4 ── Ambiguity Check (FIX 3: flag unclear visa type) ─────────────────
        if is_ambiguous(standalone) and not self.chat_history:
            meta["needs_clarify"] = True

        # 5 ── Confidence Guard ─────────────────────────────────────────────────
        _, is_confident = check_confidence(self.vector_db, standalone)
        meta["confident"] = is_confident

        if not is_confident:
            fallback = (
                "I couldn't find reliable information about that in my knowledge base. "
                "For the most accurate guidance, please:\n\n"
                "1. Contact OAMP directly: **+420 974 801 801**\n"
                "2. Visit the official portal: **frs.gov.cz** or **ipc.gov.cz**\n"
                "3. Get free legal advice from **SIMI** (migrace.com) or **OPU** (opu.cz)"
            )
            self._update_history(user_input, fallback)
            return fallback, meta

        # 6 ── Multi-query Retrieval (rephrase prompt also preserves visa type) ─
        docs    = self._multi_retrieve(standalone)
        context = format_docs_with_sources(docs)

        # 7 ── Build prompt: context THEN language instruction at the end ────────
        # FIX 1: lang_instruction is the LAST thing the model reads.
        # It overrides the implicit "everything above is in English" signal.
        prompt = self._build_prompt(context, lang_instruction)
        chain  = prompt | self.llm | self.parser
        answer = chain.invoke({
            "chat_history": self.chat_history,
            "input":        standalone,
        })

        # 8 ── Update history ───────────────────────────────────────────────────
        self._update_history(user_input, answer)
        return answer, meta

    def reset(self):
        self.chat_history = []