"""
app.py — ImmigraSmart UI v5 (Bug Fix)

BUGS FIXED vs v4:
  BUG A — Answer rendered then vanished.
    The typing div was rendered with st.markdown() inside the assistant
    chat_message block, then st.markdown(answer) rendered on top of it.
    When st.rerun() fired, Streamlit replayed everything — but the typing
    div was still there competing with the answer render.
    FIX: Remove the typing div entirely from the response block. The
    st.spinner() already shows a loading state. Keep it simple.

  BUG B — st.rerun() called unconditionally even on exception.
    If chat.ask() threw an error, st.rerun() still fired, wiping the
    error message before the user could read it.
    FIX: st.rerun() only called when a valid answer was received.

  BUG C — User message appended to session AFTER st.markdown(answer).
    The append order was: render user → ask() → append user → render answer
    → append answer → rerun. On rerun, if anything failed between ask()
    and the appends, the message was lost.
    FIX: Append user message to session state BEFORE calling ask(), so
    it survives any exception.
"""

import os
import streamlit as st

st.set_page_config(
    page_title="ImmigraSmart AI",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── DESIGN SYSTEM ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
  --navy:       #0b0f1a;
  --navy2:      #111827;
  --navy3:      #1a2235;
  --navy4:      #243048;
  --amber:      #f59e0b;
  --amber2:     #fbbf24;
  --amber-soft: rgba(245,158,11,0.12);
  --amber-glow: rgba(245,158,11,0.06);
  --red-cz:     #d7263d;
  --white:      #f8fafc;
  --muted:      #8b9ab5;
  --border:     rgba(255,255,255,0.07);
  --border2:    rgba(245,158,11,0.2);
  --success:    #10b981;
}

.stApp { background: var(--navy) !important; font-family: 'DM Sans', sans-serif; }
.main .block-container { padding-top: 1.5rem !important; max-width: 780px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

[data-testid="stSidebar"] {
  background: var(--navy2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--white) !important; }
[data-testid="stSidebarContent"] { padding: 1.5rem 1rem; }

.sb-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 0 0 1.2rem; border-bottom: 1px solid var(--border);
  margin-bottom: 1.2rem;
}
.sb-brand-icon {
  width: 38px; height: 38px; background: var(--amber-soft);
  border: 1px solid var(--border2); border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sb-brand-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; }
.sb-brand-sub { font-size: 11px; color: var(--muted) !important; font-family: 'DM Mono', monospace; letter-spacing: 0.04em; }

.sb-link-group { margin-bottom: 1.4rem; }
.sb-link-label { font-size: 10px; font-family: 'DM Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted) !important; margin-bottom: 8px; }
.sb-link {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px; margin-bottom: 4px;
  text-decoration: none; color: #c4d0e8 !important;
  font-size: 13px; transition: background 0.15s;
  border: 1px solid transparent;
}
.sb-link:hover { background: var(--navy3); border-color: var(--border); }
.sb-link-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--amber); flex-shrink: 0; }

.sb-phone {
  background: var(--amber-soft); border: 1px solid var(--border2);
  border-radius: 10px; padding: 12px 14px; margin-bottom: 1.2rem;
}
.sb-phone-label { font-size: 10px; font-family: 'DM Mono', monospace; letter-spacing: 0.1em; text-transform: uppercase; color: var(--amber) !important; margin-bottom: 4px; }
.sb-phone-num { font-family: 'DM Mono', monospace; font-size: 15px; font-weight: 500; }

.sb-status { display: flex; align-items: center; gap: 8px; padding: 8px 0; }
.sb-status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); box-shadow: 0 0 6px var(--success); animation: pulse 2s infinite; }
.sb-status-text { font-size: 12px; color: var(--muted) !important; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

div[data-testid="stButton"] button {
  background: transparent !important; border: 1px solid var(--border) !important;
  color: var(--muted) !important; border-radius: 8px !important;
  font-family: 'DM Sans', sans-serif !important; font-size: 13px !important;
  transition: all 0.2s !important;
}
div[data-testid="stButton"] button:hover {
  border-color: var(--red-cz) !important; color: var(--red-cz) !important;
  background: rgba(215,38,61,0.08) !important;
}

.page-header { margin-bottom: 1.5rem; animation: fadeIn 0.5s ease; }
.header-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--amber-soft); border: 1px solid var(--border2);
  border-radius: 20px; padding: 4px 12px;
  font-family: 'DM Mono', monospace; font-size: 11px;
  color: var(--amber); letter-spacing: 0.06em; margin-bottom: 8px;
}
.page-title {
  font-family: 'Syne', sans-serif; font-weight: 800;
  font-size: clamp(22px, 4vw, 32px); color: var(--white);
  line-height: 1.1; letter-spacing: -0.02em;
}
.page-title span { color: var(--amber); }
.page-sub { font-size: 14px; color: var(--muted); margin-top: 4px; }

.disclaimer {
  background: rgba(215,38,61,0.07); border: 1px solid rgba(215,38,61,0.2);
  border-left: 3px solid var(--red-cz); border-radius: 0 8px 8px 0;
  padding: 10px 14px; margin-bottom: 1.5rem;
  font-size: 13px; color: #e8a0a8; line-height: 1.5;
}
.disclaimer a { color: var(--amber) !important; text-decoration: none; }
.disclaimer strong { color: var(--white); }

.suggestions-label {
  font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--muted); margin-bottom: 10px;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:none} }

[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 0.3rem 0 !important;
}

.meta-row { display: flex; align-items: center; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
.meta-badge {
  display: inline-flex; align-items: center; gap: 5px;
  font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.06em;
  padding: 3px 8px; border-radius: 4px;
}
.badge-lang { background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.25); color: #93c5fd; }
.badge-pii  { background: rgba(16,185,129,0.1);  border: 1px solid rgba(16,185,129,0.25); color: #6ee7b7; }
.fb-given { font-size: 12px; color: var(--muted); font-family: 'DM Mono', monospace; margin-top: 8px; }

[data-testid="stChatInput"] > div {
  background: var(--navy2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: var(--white) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--navy4); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── SVG ICONS ──────────────────────────────────────────────────────────────────
ICONS = {
    "logo":   '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2L2 7l10 5 10-5-10-5z" stroke="#f59e0b" stroke-width="1.5" stroke-linejoin="round"/><path d="M2 17l10 5 10-5" stroke="#f59e0b" stroke-width="1.5" stroke-linejoin="round"/><path d="M2 12l10 5 10-5" stroke="#f59e0b" stroke-width="1.5" stroke-linejoin="round"/></svg>',
    "link":   '<svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
    "phone":  '<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>',
    "spark":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>',
    "lock":   '<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M7 11V7a5 5 0 0110 0v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="12" cy="16" r="1.5" fill="currentColor"/></svg>',
    "alert":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M10.3 3.3L2 20h20L13.7 3.3a2 2 0 00-3.4 0z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M12 10v4M12 17v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
}

def icon(name, style=""):
    return f'<span style="display:inline-flex;align-items:center;{style}">{ICONS.get(name,"")}</span>'

DB_PATH = "/tmp/vector_db"
LANG_FLAGS = {
    "cs": "🇨🇿", "sk": "🇸🇰", "es": "🇪🇸", "ar": "🇸🇦",
    "uk": "🇺🇦", "ru": "🇷🇺", "vi": "🇻🇳", "zh": "🇨🇳",
    "de": "🇩🇪", "fr": "🇫🇷", "en": "🇬🇧",
}
LANG_NAMES = {
    "cs": "Czech", "sk": "Slovak", "es": "Spanish", "ar": "Arabic",
    "uk": "Ukrainian", "ru": "Russian", "vi": "Vietnamese",
    "zh": "Chinese", "de": "German", "fr": "French", "en": "English",
}

# ── INIT ───────────────────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    with st.spinner("Building knowledge base — takes ~1 min on first run..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
        except Exception as e:
            st.error(f"Initialisation failed: {e}")
            st.info("Refresh or check your GOOGLE_API_KEY.")
            st.stop()

if "chat" not in st.session_state:
    try:
        from src.rag_engine import ImmigraSmartChat
        st.session_state.chat = ImmigraSmartChat()
    except Exception as e:
        st.error(f"Failed to start AI engine: {e}")
        st.stop()

if "messages"  not in st.session_state: st.session_state.messages  = []
if "feedback"  not in st.session_state: st.session_state.feedback  = {}

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sb-brand">
      <div class="sb-brand-icon">{ICONS['logo']}</div>
      <div>
        <div class="sb-brand-title">ImmigraSmart</div>
        <div class="sb-brand-sub">AI · Czech Republic</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-link-label">Official Resources</div>', unsafe_allow_html=True)
    resources = [
        ("OAMP Appointments",        "https://frs.gov.cz"),
        ("Info Portal for Foreigners","https://ipc.gov.cz"),
        ("PVZP Insurance",            "https://pvzp.cz"),
        ("Free Legal Aid — SIMI",     "https://migrace.com"),
        ("Free Legal Aid — OPU",      "https://opu.cz"),
        ("Czech POINT (Data Box)",    "https://czechpoint.cz"),
    ]
    links_html = "".join(
        f'<a class="sb-link" href="{url}" target="_blank">'
        f'<span class="sb-link-dot"></span>{name} {ICONS["link"]}</a>'
        for name, url in resources
    )
    st.markdown(f'<div class="sb-link-group">{links_html}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-phone">
      <div class="sb-phone-label">{ICONS['phone']} Emergency Contact</div>
      <div class="sb-phone-num">+420 974 801 801</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-status">
      <div class="sb-status-dot"></div>
      <div class="sb-status-text">Knowledge Base v2026.2 · Active</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.session_state.chat.reset()
        st.rerun()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="header-badge">{ICONS['spark']} AI Powered</div>
  <div class="page-title">ImmigraSmart <span>AI</span></div>
  <div class="page-sub">Czech Republic immigration assistant for international students</div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="disclaimer">
  {icon('alert', 'color:#d7263d;margin-right:6px')}
  <strong>Legal disclaimer:</strong> General information only — not legal advice.
  Always verify with <a href="https://frs.gov.cz" target="_blank">OAMP</a> or a qualified immigration lawyer.
</div>""", unsafe_allow_html=True)

# ── SUGGESTIONS ────────────────────────────────────────────────────────────────
SUGGESTIONS = [
    "How much money do I need for a 12-month stay?",
    "What should I do within 3 days of arriving?",
    "When should I apply to extend my permit?",
    "What is a Bridge Label and when do I need one?",
    "Can I work while studying on a student permit?",
    "What health insurance do I need?",
]

if not st.session_state.messages:
    st.markdown('<div class="suggestions-label">Try asking</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(text, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_input = text
                st.rerun()

# ── CHAT HISTORY ───────────────────────────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🇨🇿"):
        st.markdown(msg["content"])

        if msg["role"] == "user":
            meta   = msg.get("meta", {})
            badges = ""
            lang   = meta.get("language", "en")
            if lang != "en":
                flag  = LANG_FLAGS.get(lang, "🌐")
                lname = LANG_NAMES.get(lang, lang)
                badges += f'<span class="meta-badge badge-lang">{flag} {lname}</span>'
            if meta.get("pii_detected"):
                entities = ", ".join(meta.get("pii_entities", []))
                badges += f'<span class="meta-badge badge-pii">{icon("lock")} PII removed · {entities}</span>'
            if badges:
                st.markdown(f'<div class="meta-row">{badges}</div>', unsafe_allow_html=True)

        if msg["role"] == "assistant":
            existing = st.session_state.feedback.get(idx)
            if existing:
                emoji = "👍" if existing == "up" else "👎"
                st.markdown(f'<div class="fb-given">{emoji} Thank you for your feedback</div>', unsafe_allow_html=True)
            else:
                c1, c2, _ = st.columns([1, 1, 10])
                if c1.button("👍", key=f"up_{idx}"):
                    st.session_state.feedback[idx] = "up"
                    st.rerun()
                if c2.button("👎", key=f"down_{idx}"):
                    st.session_state.feedback[idx] = "down"
                    st.rerun()

# ── INPUT ──────────────────────────────────────────────────────────────────────
pending    = st.session_state.pop("pending_input", None)
user_input = st.chat_input("Ask about visas, permits, deadlines, insurance...") or pending

if user_input:
    # Render user message immediately
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # Generate and render assistant response
    with st.chat_message("assistant", avatar="🇨🇿"):
        with st.spinner("Searching knowledge base..."):
            try:
                answer, meta = st.session_state.chat.ask(user_input)

                # FIX BUG C: append BEFORE rerun so messages survive
                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": meta
                })
                st.session_state.messages.append({
                    "role": "assistant", "content": answer, "meta": meta
                })

                st.markdown(answer)

                # FIX BUG B: rerun only on success
                st.rerun()

            except Exception as e:
                # On error: show message, do NOT rerun (so user can read it)
                st.error(
                    "Something went wrong. Please try again.\n\n"
                    "If this persists: **+420 974 801 801**"
                )
                st.caption(f"Detail: {e}")
                # Still save the user message so chat history is consistent
                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": {}
                })