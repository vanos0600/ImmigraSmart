"""
rag_engine.py — ImmigraSmart RAG Engine (v9.1 — Bulletproof Custom Hybrid Search)

BUGS FIXED:
  - Bypassed LangChain's broken EnsembleRetriever module entirely.
  - Built a custom parallel retrieval system combining BM25 and ChromaDB.
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
from langchain_core.documents import Document

# SOLO IMPORTAMOS BM25 (Despedimos a EnsembleRetriever)
from langchain_community.retrievers import BM25Retriever

from pii_scrubber import scrub
from lang_detect import detect_language, get_language_instruction

load_dotenv()

PERSIST_DIR          = "/tmp/vector_db"
RETRIEVER_K          = 6

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

def is_ambiguous(question: str) -> bool:
    q = question.lower()
    return any(term in q for term in AMBIGUOUS_TERMS)

# ── Prompts ────────────────────────────────────────────────────────────────────

COMBINED_PREP_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are helping retrieve Czech immigration law documents. "
     "Given the conversation history and the latest user question:\n"
     "1. Rewrite the question to be fully self-contained.\n"
     "2. Write 2 alternative phrasings for better search coverage.\n\n"
     "IMPORTANT: Always rewrite in English — these variants are for internal "
     "vector search only.\n\n"
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
- If the user provides an uploaded document, analyze it against the legal context.
- Cite the source section (e.g. "According to Section 9: Working as a Student...").
- Friendly but professional tone — users are often stressed.
- Highlight deadlines and CZK amounts clearly.
- If action is needed, give a numbered step-by-step list.

STRICT RULES:
- You MUST answer in the EXACT SAME LANGUAGE that the user used in their question. If they ask in English, reply in English. If they ask in Spanish, reply in Spanish. Do not let currencies like "CZK" confuse your language detection.
- Use ONLY the LEGAL CONTEXT. Never use general knowledge.
- TRANSLATION MANDATORY: The provided context is in English, but you MUST freely translate your final answer into the user's language without apologizing.
- If context lacks the answer: "I don't have specific information about that. \
  Please contact OAMP at +420 974 801 801 or visit frs.gov.cz."
- Never fabricate deadlines, amounts, or legal requirements.
- Never give legal advice.

--- LEGAL CONTEXT ---
{context}
--- END CONTEXT ---

{user_document_section}

{language_instruction}"""

# ── Engine Builder (CUSTOM HYBRID SEARCH) ──────────────────────────────────────

def get_rag_chain():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not found. Check your .env file.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
        task_type="retrieval_query",
    )
    
    # 1. Cargar Base de Datos Semántica (ChromaDB)
    vector_db = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
    )
    chroma_retriever = vector_db.as_retriever(search_kwargs={"k": RETRIEVER_K})

    # 2. Extraer documentos para construir BM25
    db_data = vector_db.get()
    all_docs = []
    if db_data and "documents" in db_data and db_data["documents"]:
        for i in range(len(db_data["ids"])):
            doc = Document(
                page_content=db_data["documents"][i],
                metadata=db_data["metadatas"][i]
            )
            all_docs.append(doc)
            
    # 3. Guardar AMBOS motores en una lista (Nuestra solución a prueba de balas)
    if all_docs:
        bm25_retriever = BM25Retriever.from_documents(all_docs)
        bm25_retriever.k = RETRIEVER_K
        retrievers_list = [bm25_retriever, chroma_retriever]
    else:
        retrievers_list = [chroma_retriever]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        google_api_key=api_key,
    )
    
    return llm, retrievers_list, vector_db

# ── Stateful Chat Handler ──────────────────────────────────────────────────────

class ImmigraSmartChat:
    def __init__(self):
        # Ahora recibimos una LISTA de retrievers
        self.llm, self.retrievers_list, self.vector_db = get_rag_chain()
        self.chat_history: list = []
        self.parser = StrOutputParser()

    def _prepare_variants(self, clean_input: str) -> list[str]:
        if not self.chat_history:
            return [clean_input]
        chain = COMBINED_PREP_PROMPT | self.llm | self.parser
        try:
            raw   = chain.invoke({"chat_history": self.chat_history, "input": clean_input})
            lines = [l.strip() for l in raw.strip().split("\n") if l.strip()][:3]
            return lines if lines else [clean_input]
        except Exception:
            return [clean_input]

    def _retrieve(self, variants: list[str]) -> list:
        # 🚀 CUSTOM HYBRID SEARCH: Disparamos todos los motores y juntamos resultados
        seen, docs = set(), []
        for v in variants:
            for retriever in self.retrievers_list:
                for doc in retriever.invoke(v):
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

    def ask(self, user_input: str, user_document: str = None) -> tuple[str, dict]:
        meta = {
            "pii_detected":  False,
            "pii_entities":  [],
            "language":      "en",
            "confident":     True,
            "needs_clarify": False,
        }

        # 1 — PII scrub
        scrub_result = scrub(user_input)
        clean_input  = scrub_result.clean_text
        if scrub_result.was_modified:
            meta["pii_detected"] = True
            meta["pii_entities"] = scrub_result.entities_found

        # 2 — Language detection
        lang_code        = detect_language(user_input)
        meta["language"] = lang_code
        lang_instruction = get_language_instruction(lang_code)

        # 3 — Ambiguity flag
        if is_ambiguous(clean_input) and not self.chat_history:
            meta["needs_clarify"] = True

        # 4 — Prepare query variants
        variants = self._prepare_variants(clean_input)

        # 5 — Retrieve documents (AHORA USANDO NUESTRO MOTOR HÍBRIDO CUSTOM)
        docs = self._retrieve(variants)

        if not docs:
            meta["confident"] = False
            fallback = (
                "I couldn't find reliable information about that in my knowledge base. "
                "For accurate guidance:\n\n"
                "1. Contact OAMP: **+420 974 801 801**\n"
                "2. Official portal: **frs.gov.cz**\n"
            )
            self._update_history(user_input, fallback)
            return fallback, meta

        context = format_docs_with_sources(docs)

        # Inyección del documento del usuario (PDF)
        doc_section = ""
        if user_document:
            doc_section = (
                "--- USER UPLOADED DOCUMENT ---\n"
                "The user has uploaded a personal document. Here is the text extracted from it:\n\n"
                f"{user_document}\n\n"
                "--- END USER DOCUMENT ---\n"
                "Please analyze the user's query in the context of BOTH the legal rules above and their uploaded document."
            )

        system_msg = BASE_SYSTEM_PROMPT.format(
            context=context,
            language_instruction=lang_instruction,
            user_document_section=doc_section 
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        chain  = prompt | self.llm | self.parser
        answer = chain.invoke({
            "chat_history": self.chat_history,
            "input":        clean_input,
        })

        self._update_history(user_input, answer)
        return answer, meta

    def reset(self):
        self.chat_history = []