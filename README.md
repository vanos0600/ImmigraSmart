<div align="center">

# 🇨🇿 ImmigraSmart AI

**AI-powered immigration assistant for international students in the Czech Republic**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://lnkd.in/dfWfdMza)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?logo=chainlink)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Google_AI-4285F4?logo=google)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35)
![Supabase](https://img.shields.io/badge/Supabase-Cloud_DB-3ECF8E?logo=supabase)
![GDPR](https://img.shields.io/badge/GDPR-Compliant-003399)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

<br/>

> Built by a student from Nicaragua living in Prague — for every international student who has ever felt lost in the Czech immigration system.

<br/>

</div>

---

## 📌 The Problem

Moving to the Czech Republic as an international student means dealing with:

- Strict legal deadlines — miss one and your permit can be cancelled
- Complex documents written in Czech legalese
- Multiple government offices (OAMP, Foreign Police, Czech POINT) that are easy to confuse
- Language barriers at every step
- No single place that answers all your questions accurately

**ImmigraSmart solves this.** It is a production-grade RAG (Retrieval-Augmented Generation) application that answers immigration questions using only verified official sources — no hallucinations, no guesswork, full GDPR compliance, and now with persistent cloud memory and hybrid search.

---

## ✨ Features

| Feature | Description |
|---|---|
| ☁️ **Persistent Cloud Memory** | Integrated with Supabase. Chat history is saved via UUID sessions — refreshing the page no longer wipes your conversation. |
| 🔎 **Hybrid Search (RAG v9.1)** | Combines BM25 (keyword) + ChromaDB (semantic) retrieval in parallel. Legal terms like "Bridge Label" or "VZP" are always found, even when embeddings alone would miss them. |
| 📄 **Document Analysis** | Students can upload their own lease or insurance contracts (PDF). The AI analyzes them against the 2026 legal framework in real-time. |
| 🔒 **PII Scrubbing (GDPR)** | Regex layer strips passport numbers, IBANs, rodné číslo, and phone numbers before any text reaches the LLM. |
| 🌍 **11-Language Detection** | Auto-detects and responds in the user's language (Czech, Spanish, Ukrainian, Arabic, and more) while citing English legal sources. |
| 📚 **Structured Knowledge Base** | 11 sections covering the full student immigration lifecycle — from arrival to post-graduation — based on Act No. 326/1999 Coll. and official MVČR sources. |

---

## 🏗️ Architecture

```
User Question + PDF Upload
      │
      ▼
┌─────────────────────────────┐
│   PII Scrubber + Lang Det   │  Strips PII & detects input language
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Supabase History Load     │  Retrieves last 20 messages for session_id
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   HYBRID RETRIEVAL (v9.1)   │
│   1. BM25 (Keyword Match)   │  Runs in parallel to prevent
│   2. ChromaDB (Semantic)    │  missing specific legal terms
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Gemini 2.5 Flash          │  Grounded in Legal Context + User PDF
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Supabase History Save     │  New user/AI message pair saved to cloud
└─────────────┬───────────────┘
              │
              ▼
         Answer + Citations
```

---

## 📚 Knowledge Base

Version `2026.2` — covers **11 structured sections** sourced from the Ministry of the Interior (MVČR), Act No. 326/1999 Coll., `frs.gov.cz`, and `ipc.gov.cz`.

| Section | Topic |
|---|---|
| 1 | Arrival & Biometrics — what to do within 3 days |
| 2 | Extending Your Residence Permit — deadlines, Bridge Label |
| 3 | Financial Requirements — CZK amounts, proof of funds formulas |
| 4 | Health Insurance — approved providers, what is NOT accepted |
| 5 | Administrative Expulsion & 2026 Rules — exit orders, deportation |
| 6 | Legal Appeals & Data Box — appeal deadlines, Datová schránka |
| 7 | Post-Graduation — 9-month job-seeker permit |
| 8 | Study Obligations — university transfers, leaves of absence |
| 9 | Working as a Student — employment rights, internships |
| 10 | Quick Reference — all deadlines and CZK amounts in one place |
| 11 | FAQ Bridge — Q&A pairs that close the semantic gap for common questions |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | `gemini-embedding-001` (`retrieval_query` / `retrieval_document`) |
| Vector Database | ChromaDB (local persistence at `/tmp/vector_db`) |
| Cloud Database | Supabase (PostgreSQL) — chat history |
| Hybrid Search | LangChain BM25 Retriever + ChromaDB |
| RAG Framework | LangChain 0.2+ |
| Frontend | Streamlit |
| Deployment | Streamlit Cloud |
| PII Layer | Custom regex scrubber (`pii_scrubber.py`) |
| Language Detection | Custom heuristic word-list (`lang_detect.py`) |
| PDF Parsing | PyPDF |

---

## 📁 Project Structure

```
ImmigraSmart/
├── app.py                                    # Streamlit frontend — UI & session UUID logic
├── src/
│   ├── rag_engine.py                         # Hybrid RAG pipeline — ImmigraSmartChat class
│   ├── database.py                           # Supabase connector — history load/save
│   ├── ingest.py                             # Document ingestion, chunking, vector DB build
│   ├── pii_scrubber.py                       # GDPR layer — strips PII before LLM calls
│   └── lang_detect.py                        # Language detection + response instruction
├── data/
│   └── immigrasmart_knowledge_base.txt       # Structured knowledge base (11 sections)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Google AI Studio](https://aistudio.google.com) API key (free tier works)
- A [Supabase](https://supabase.com) project (free tier works)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/vanos0600/ImmigraSmart.git
cd ImmigraSmart

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your keys (see below)
```

### Environment Variables

```env
GOOGLE_API_KEY=your_google_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_public_key
```

### Supabase Setup

Run this SQL in your Supabase SQL editor to create the chat history table:

```sql
CREATE TABLE chat_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_session_id ON chat_history(session_id);
```

### Run Locally

```bash
streamlit run app.py
```

Open `http://localhost:8501`. On first run, the vector database is built automatically (~1–2 minutes). Subsequent runs use the cached database and start in seconds.

---

## 📦 Requirements

```
streamlit
langchain
langchain-google-genai
langchain-chroma
langchain-community
langchain-core
langchain-text-splitters
chromadb
supabase
python-dotenv
pypdf
rank-bm25
```

---

## 🔒 GDPR Compliance

ImmigraSmart was designed with privacy-by-design principles (GDPR Article 25).

**PII Scrubbing** — `pii_scrubber.py` runs before every LLM API call and strips:

- Czech/Slovak passport numbers (`AB1234567` format)
- Czech personal ID numbers / rodné číslo (`YYMMDD/XXXX` with separator)
- IBAN / bank account numbers
- Email addresses
- Phone numbers (`+420` and international `+XX` formats)
- Dates of birth (`DD.MM.YYYY`, `YYYY-MM-DD`)

Personal data is **never sent to the Gemini API**. The scrubber returns a `ScrubResult` dataclass indicating which entity types were found, allowing the UI to display a privacy badge to the user.

**Data Sovereignty** — All chat logs are stored in a secure Supabase instance. Users can request data deletion by providing their `session_id`, ensuring compliance with the GDPR Right to Erasure (Article 17).

---

## 🌍 Supported Languages

ImmigraSmart detects the language of each message and responds in kind. The language instruction is injected at the **end** of the system prompt — after the English legal context — to prevent language drift, a known failure mode where the model defaults to English after reading large amounts of English text.

| Language | Code | Detection method |
|---|---|---|
| Czech | `cs` | Heuristic word list |
| Slovak | `sk` | Heuristic word list |
| English | `en` | Default fallback |
| Spanish | `es` | Heuristic word list |
| Arabic | `ar` | Heuristic word list |
| Ukrainian | `uk` | Heuristic word list |
| Russian | `ru` | Heuristic word list |
| Vietnamese | `vi` | Heuristic word list |
| Chinese (Simplified) | `zh` | Heuristic word list |
| German | `de` | Heuristic word list |
| French | `fr` | Heuristic word list |

---

## 🐛 Known Issues Resolved

| Issue | Root Cause | Fix Applied |
|---|---|---|
| "Can I work?" returned generic fallback | Confidence check ran before keyword boost — short questions scored below threshold | Moved confidence check to post-retrieval; fallback only triggers on empty results |
| Czech/Spanish responses came back in English | `chain.invoke()` received the English rewrite (`variants[0]`) instead of the user's original message | Changed final chain invocation to use `clean_input`; variants are now retrieval-only |
| Language instruction ignored after English context | Instruction injected before legal context — English text volume overrode it | Instruction moved to end of system prompt with imperative phrasing |
| "Foreign Police" → `[PERSON_NAME]` | Name regex matched any two capitalised words, destroying legal terms | Name regex removed; only exact document formats matched |
| Chat messages showed black background on mobile | `[data-testid="stSidebar"] * { color: white }` wildcard bled into main content | Wildcard replaced with scoped selectors; all text colors made explicit |
| Answers took 8–14 seconds | 3 sequential LLM calls per message (condense + rephrase + answer) | Combined into 1 call; first messages skip it entirely (0 LLM calls) |
| `No module named 'pii_scrubber'` | Python path not set when importing from `src/` | `sys.path.insert(0, ...)` added to `rag_engine.py` |
| Refreshing page wiped conversation | State stored only in Streamlit `session_state` (in-memory) | Migrated to Supabase; history persists across sessions via UUID |
| Legal terms like "VZP" missed by semantic search | Embedding similarity alone fails on abbreviations and proper nouns | BM25 keyword retriever runs in parallel, merged with semantic results |

---

## 🔮 Roadmap

- [x] Hybrid Search — BM25 keyword + semantic retrieval
- [x] Persistent Cloud History — Supabase integration with UUID sessions
- [x] PDF Document Upload — contextual analysis of student documents
- [ ] Supabase Auth — proper user accounts with email/password
- [ ] RAGAS Evaluation Pipeline — automated quality scoring on 30 test questions
- [ ] Vertex AI Context Caching — cache the legal corpus, reduce LLM cost ~80%
- [ ] Automated KB Updates — weekly GitHub Action that checks `frs.gov.cz` for changes
- [ ] FastAPI Backend — async endpoints, enables WhatsApp/Telegram bot on same engine
- [ ] OAMP Appointment Checker — scrape available appointment slots, notify users

---

## ⚠️ Disclaimer

ImmigraSmart AI provides **general informational guidance only** and does not constitute legal advice. Immigration rules change — always verify current requirements with:

- **OAMP official portal:** [frs.gov.cz](https://frs.gov.cz)
- **Info portal for foreigners:** [ipc.gov.cz](https://ipc.gov.cz)
- **OAMP Info Line:** +420 974 801 801 (Mon–Thu 08:00–16:00, Fri 08:00–12:00)
- **Free legal aid (SIMI):** [migrace.com](https://migrace.com)
- **Free legal aid (OPU):** [opu.cz](https://opu.cz)

---

## 🤝 Contributing

Contributions are welcome — especially from Czech immigration lawyers, international students who have spotted outdated information, or developers who want to help.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add: your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 👤 Author

**Oskar Vanegas** — Student, AI Engineer, Nicaraguan in Prague 🇳🇮 → 🇨🇿

Built this because I needed it. Sharing it because others do too.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?logo=linkedin)](https://www.linkedin.com/in/oskar-david-vanegas-juarez-59301b322/?locale=en)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github)](https://github.com/vanos0600)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ in Prague &nbsp;|&nbsp; If this helped you, give it a ⭐

</div>