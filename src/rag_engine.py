"""
rag_engine.py — ImmigraSmart RAG Engine
Improvements over v1:
  - Conversation memory (chat history context)
  - Confidence guard: low-similarity results trigger a "consult OAMP" fallback
  - Source citations in every answer (section titles passed to LLM)
  - Structured prompt with role, tone, and safety guardrails
  - Multi-query retrieval (3 rephrasings) for better recall
  - Metadata-aware context formatting
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage


load_dotenv()

PERSIST_DIR = "/tmp/vector_db"
LOW_CONFIDENCE_THRESHOLD = 0.45  # Cosine distance above this = low confidence


# ── Context Formatter ──────────────────────────────────────────────────────────

def format_docs_with_sources(docs) -> str:
    """
    Formats retrieved documents into context string with section labels.
    This lets the LLM cite sources in its answer.
    """
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
    """
    Retrieves documents WITH similarity scores.
    Returns (docs, is_confident) where is_confident=False triggers fallback message.
    """
    results = vector_db.similarity_search_with_relevance_scores(query, k=k)
    if not results:
        return [], False

    docs = [doc for doc, score in results]
    scores = [score for _, score in results]
    best_score = max(scores)

    # Relevance score: 1.0 = perfect match, 0.0 = no match
    is_confident = best_score >= LOW_CONFIDENCE_THRESHOLD
    return docs, is_confident


# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are ImmigraSmart, a professional AI immigration consultant \
specializing in Czech Republic visa and residence permit regulations for international students.

YOUR ROLE:
- Provide accurate, clear, and structured answers based ONLY on the provided context.
- Always cite which section or source your information comes from (e.g., "According to Section 3: Financial Requirements...").
- Use a friendly but professional tone — many users are stressed about immigration issues.
- If deadlines or amounts are mentioned, highlight them clearly.
- If the answer requires action from the user, provide a numbered step-by-step list.

STRICT RULES:
- ONLY use information from the provided CONTEXT. Do not use general knowledge.
- If the CONTEXT does not contain the answer, say exactly:
  "I don't have specific information about that in my knowledge base. \
   Please contact OAMP directly at +420 974 801 801 or visit frs.gov.cz for the most accurate guidance."
- NEVER make up deadlines, amounts, or legal requirements.
- NEVER give legal advice — you provide information, not legal representation.
- If a question involves a serious legal risk (deportation, permit revocation), \
  always recommend consulting free legal aid at SIMI (migrace.com) or OPU (opu.cz).

CONTEXT:
{context}
"""

CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Given the conversation history and a new user question, \
rephrase the question to be self-contained (as if there were no prior conversation). \
Return ONLY the rephrased question, nothing else."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


# ── Engine Builder ─────────────────────────────────────────────────────────────

def get_rag_chain():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not found. Check your .env file.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
        task_type="retrieval_query"  # Use query-optimized task type for retrieval
    )

    vector_db = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,  # Slight warmth for natural tone, still mostly deterministic
        google_api_key=api_key
    )

    base_retriever = vector_db.as_retriever(search_kwargs={"k": 6})

    return llm, base_retriever, vector_db, QA_PROMPT, CONDENSE_PROMPT


# ── Stateful Chat Handler ──────────────────────────────────────────────────────

class ImmigraSmartChat:
    """
    Manages conversation state and runs the full RAG pipeline per turn.
    Usage:
        chat = ImmigraSmartChat()
        answer = chat.ask("How much money do I need for 6 months?")
        answer2 = chat.ask("What about for a full year?")  # remembers context
    """

    def __init__(self):
        self.llm, self.retriever, self.vector_db, self.qa_prompt, self.condense_prompt = get_rag_chain()
        self.chat_history: list = []
        self.parser = StrOutputParser()

    def _condense_question(self, user_input: str) -> str:
        """If there's chat history, rephrase the question to be self-contained."""
        if not self.chat_history:
            return user_input
        chain = self.condense_prompt | self.llm | self.parser
        return chain.invoke({
            "chat_history": self.chat_history,
            "input": user_input
        })

    def ask(self, user_input: str) -> str:
        # Step 1: Condense question with history context
        standalone_question = self._condense_question(user_input)

        # Step 2: Confidence check with similarity scores
        _, is_confident = check_confidence(self.vector_db, standalone_question)

        if not is_confident:
            fallback = (
                "I couldn't find reliable information about that in my knowledge base. "
                "For the most accurate guidance, please:\n\n"
                "1. Contact OAMP directly: **+420 974 801 801**\n"
                "2. Visit the official portal: **frs.gov.cz** or **ipc.gov.cz**\n"
                "3. Get free legal advice from **SIMI** (migrace.com) or **OPU** (opu.cz)"
            )
            self.chat_history.extend([
                HumanMessage(content=user_input),
                AIMessage(content=fallback)
            ])
            return fallback

        # Step 3: Multi-query retrieval (manual — avoids unstable LangChain imports)
        # Generate 2 rephrasings of the question, merge all retrieved docs, deduplicate
        rephrase_chain = (
            ChatPromptTemplate.from_template(
                "Rephrase this immigration question in 2 different ways to improve search. "
                "Return only the 2 questions, one per line, no numbering:\n{q}"
            )
            | self.llm
            | StrOutputParser()
        )
        try:
            rephrased_raw = rephrase_chain.invoke({"q": standalone_question})
            variants = [standalone_question] + [
                line.strip() for line in rephrased_raw.strip().split("\n") if line.strip()
            ][:2]
        except Exception:
            variants = [standalone_question]

        seen, docs = set(), []
        for variant in variants:
            for doc in self.retriever.invoke(variant):
                key = doc.page_content[:80]
                if key not in seen:
                    seen.add(key)
                    docs.append(doc)
        context = format_docs_with_sources(docs)

        # Step 4: Generate answer
        chain = self.qa_prompt | self.llm | self.parser
        answer = chain.invoke({
            "context": context,
            "chat_history": self.chat_history,
            "input": standalone_question
        })

        # Step 5: Update history (keep last 6 turns to avoid context bloat)
        self.chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=answer)
        ])
        if len(self.chat_history) > 12:  # 6 turns × 2 messages
            self.chat_history = self.chat_history[-12:]

        return answer

    def reset(self):
        """Clears conversation history."""
        self.chat_history = []


# ── Legacy compatibility (simple chain for basic use) ─────────────────────────

def get_simple_chain():
    """
    Returns a simple (stateless) RAG chain for backward compatibility.
    For production, use ImmigraSmartChat() instead.
    """
    llm, retriever, _, qa_prompt, _ = get_rag_chain()
    parser = StrOutputParser()

    def run(question: str) -> str:
        docs = retriever.invoke(question)
        context = format_docs_with_sources(docs)
        chain = qa_prompt | llm | parser
        return chain.invoke({
            "context": context,
            "chat_history": [],
            "input": question
        })

    return run