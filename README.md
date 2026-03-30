<div align="center">

# 🇨🇿 ImmigraSmart AI

**AI-powered immigration assistant for international students in the Czech Republic**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://lnkd.in/dfWfdMza)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?logo=chainlink)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Google_AI-4285F4?logo=google)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35)
![GDPR](https://img.shields.io/badge/GDPR-Compliant-003399)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

<br/>

> Built by a student from Nicaragua living in Prague — for every international student who has ever felt lost in the Czech immigration system.

<br/>

</div>

---

## 📌 The Problem

Moving to the Czech Republic as an international student means dealing with:

- Strict legal deadlines (miss one and your permit can be cancelled)
- Complex documents written in Czech legalese
- Multiple government offices — OAMP, Foreign Police, Czech POINT — that are easy to confuse
- Language barriers at every step
- No single place that answers all your questions accurately

**ImmigraSmart solves this.** It is a RAG (Retrieval-Augmented Generation) application that answers immigration questions using only verified official sources — no hallucinations, no guesswork, full GDPR compliance.

---

## ✨ Feature Overview

| Feature | Description |
|---|---|
| 🧠 **Conversation Memory** | Remembers your session context — ask follow-ups naturally |
| 🔍 **Multi-Query Retrieval** | Generates query variants + keyword boosts to guarantee the right section is found |
| 🗂️ **Section-Aware Chunking** | Legal sections stay intact — no mid-sentence splits in the vector DB |
| 🔒 **PII Scrubbing (GDPR)** | Strips passport numbers, IBANs, emails, phone numbers before any text reaches the LLM |
| 🌍 **11-Language Detection** | Auto-detects language and responds in Spanish, Ukrainian, Arabic, Chinese, and more |
| 🛡️ **Confidence Guard** | Returns OAMP contact details instead of guessing when no relevant docs are found |
| 📎 **Source Citations** | Every answer references which knowledge base section it came from |
| 📊 **User Feedback** | Per-answer thumbs up/down for quality tracking |
| ♻️ **Smart Re-ingestion** | File hash caching — only rebuilds the vector DB when source files actually change |

---

## 🏗️ Architecture

```
User Question
      │
      ▼
┌─────────────────────────────┐
│   PII Scrubber (GDPR)       │  Regex-only, ~0ms — strips PII before any API call
│   + Language Detection      │  11-language heuristic, ~0ms
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Query Preparation         │  First message → 0 LLM calls (original question only)
│                             │  Follow-up     → 1 LLM call (condense + 2 rephrasings)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Retrieval (3 layers)      │
│   1. Semantic search (k=6)  │  Vector similarity across all query variants
│   2. Keyword boost          │  Maps topic keywords → section_id metadata filter
│   3. FAQ bridge             │  Section 11: Q&A pairs written as students ask them
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Confidence Guard          │  Zero docs found → OAMP fallback (never hallucinates)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Gemini 2.5 Flash          │  1 LLM call — grounded strictly in retrieved context
│   + Language instruction    │  Injected at END of prompt to prevent language drift
└─────────────┬───────────────┘
              │
              ▼
         Answer + Citations
```

---

## 📚 Knowledge Base Coverage

The knowledge base (`Ver. 2026.2`) covers **11 structured sections** based on official sources from the Ministry of the Interior (MVČR), Act No. 326/1999 Coll., `frs.gov.cz`, and `ipc.gov.cz`.

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
| **LLM** | Google Gemini 2.5 Flash |
| **Embeddings** | `gemini-embedding-001` (task: `retrieval_query` / `retrieval_document`) |
| **Vector Database** | ChromaDB (local persistence at `/tmp/vector_db`) |
| **RAG Framework** | LangChain 0.2+ |
| **Frontend** | Streamlit |
| **Deployment** | Streamlit Cloud |
| **PII Layer** | Custom regex scrubber (`pii_scrubber.py`) |
| **Language Detection** | Custom heuristic word-list (`lang_detect.py`) |

---

## 📁 Project Structure

```
ImmigraSmart/
├── app.py                          # Streamlit frontend (UI + session management)
├── src/
│   ├── rag_engine.py               # Full RAG pipeline — ImmigraSmartChat class
│   ├── ingest.py                   # Document ingestion, chunking, vector DB build
│   ├── pii_scrubber.py             # GDPR layer — strips PII before LLM calls
│   └── lang_detect.py              # Language detection + response instruction
├── data/
│   └── immigrasmart_knowledge_base.txt   # Structured knowledge base (11 sections)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Google AI Studio](https://aistudio.google.com) API key (free tier works)

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
# Edit .env and set your GOOGLE_API_KEY
```

### Environment Variables

```env
GOOGLE_API_KEY=your_google_api_key_here
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
python-dotenv
pypdf
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

Personal data is **never sent to the Gemini API**. The scrubber returns a `ScrubResult` dataclass indicating which entity types were found, allowing the UI to display a privacy notice to the user.

---

## 🌍 Supported Languages

ImmigraSmart detects the language of each message and responds in kind.

| Language | Code | Detected via |
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

The language instruction is injected at the **end** of the system prompt (after the English legal context) to prevent language drift — a known failure mode where the model defaults to English after reading large amounts of English text.

---

## 🐛 Known Issues Resolved

| Issue | Root Cause | Fix Applied |
|---|---|---|
| "Can I work?" returned fallback | Confidence check ran before keyword boost — colloquial questions scored below threshold | Moved confidence check to post-retrieval; fallback only triggers on empty results |
| Spanish/Ukrainian responses came back in English | Language instruction placed before legal context — English text overrode it | Language instruction moved to end of prompt with imperative phrasing |
| "Foreign Police" → `[PERSON_NAME]` | PII name regex matched any two capitalised words, destroying legal terms | Name regex removed; only explicit document formats matched |
| Chat messages showed black background on mobile | `[data-testid="stSidebar"] * { color: white }` wildcard bled into main content | Wildcard replaced with scoped class selectors; all text colors explicit with `-webkit-text-fill-color` |
| Answers took 8–14 seconds | 3 sequential LLM calls per message (condense + rephrase + answer) | Combined condense+rephrase into 1 call; first messages skip it entirely (0 calls) |
| `No module named 'pii_scrubber'` | Python path not set when importing from `src/` | `sys.path.insert(0, str(pathlib.Path(__file__).parent))` added to `rag_engine.py` |

---

## 🔮 Roadmap

- [ ] **Hybrid Search** — BM25 keyword + semantic (replaces keyword boost with proper solution)
- [ ] **RAGAS Evaluation Pipeline** — automated quality scoring on 30 test questions
- [ ] **PDF Upload** — let students upload their own permit documents and ask questions
- [ ] **Supabase Auth** — persistent chat history + GDPR Right to Erasure per user
- [ ] **Vertex AI Context Caching** — cache the legal corpus, reduce LLM cost ~80%
- [ ] **Automated KB Updates** — weekly GitHub Action that checks `frs.gov.cz` for changes
- [ ] **FastAPI Backend** — async endpoints, enables WhatsApp/Telegram bot on same engine
- [ ] **OAMP Appointment Checker** — scrape available appointment slots, notify users

---

## ⚠️ Disclaimer

ImmigraSmart AI provides **general informational guidance only** and does not constitute legal advice. Immigration rules change — always verify current requirements with:

- **OAMP official portal:** [frs.gov.cz](https://frs.gov.cz)
- **Info portal for foreigners:** [ipc.gov.cz](https://ipc.gov.cz)
- **OAMP Info Line:** +420 974 801 801
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

[![LinkedIn](https://www.linkedin.com/in/oskar-david-vanegas-juarez-59301b322/?locale=en)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github)](https://github.com/vanos0600)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ in Prague &nbsp;|&nbsp; If this helped you, give it a ⭐

</div>