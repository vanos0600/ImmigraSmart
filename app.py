"""
app.py — ImmigraSmart UI (Government Edition)
Paleta: Azul institucional + blanco + rojo checo como acento
Estilo: GOV.CZ / EU portal — limpio, confiable, accesible
"""

import os
import streamlit as st

st.set_page_config(
    page_title="ImmigraSmart — Czech Republic",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Source+Sans+3:wght@300;400;500;600&family=Source+Code+Pro:wght@400;500&display=swap');

:root {
  /* Paleta institucional checa */
  --gov-navy:     #11396B;
  --gov-navy-d:   #0C2B52;
  --gov-navy-l:   #1A4F8A;
  --gov-red:      #CC1A2A;
  --gov-red-s:    #FDF1F2;
  --gov-white:    #FFFFFF;
  --gov-off:      #F5F7FA;
  --gov-line:     #DDE3EC;
  --gov-line-d:   #B8C4D6;
  --gov-text:     #1A2332;
  --gov-text-m:   #4A5568;
  --gov-text-l:   #8896A8;
  --gov-green:    #1A7A4A;
  --gov-green-s:  #EBF7F1;
  --gov-amber:    #7A5C1E;
  --gov-amber-s:  #FEF9EC;
  --gov-blue-s:   #EBF2FA;
}

/* Global */
html, body, .stApp {
  background: var(--gov-off) !important;
  font-family: 'Source Sans 3', sans-serif;
  color: var(--gov-text);
}
.main .block-container {
  max-width: 820px;
  padding: 2rem 1.5rem 4rem !important;
}
footer, #MainMenu { visibility: hidden; }
.stDeployButton { display: none; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: var(--gov-navy) !important;
  border-right: none !important;
}
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

.sb-wrap { padding: 0 1.1rem 2rem; }

/* Brand */
.sb-brand {
  background: var(--gov-navy-d);
  border-bottom: 3px solid var(--gov-red);
  padding: 1.25rem 1.1rem 1.1rem;
  margin-bottom: 1.5rem;
  display: flex; align-items: center; gap: 12px;
}
.sb-flag {
  display: flex; width: 36px; height: 24px;
  border-radius: 3px; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.15);
  flex-shrink: 0;
}
.f-w { flex:1; background:#FFFFFF; }
.f-r { flex:1; background:#CC1A2A; }
.f-b { flex:1; background:#11396B; }
.sb-name { font-family: 'Source Serif 4', serif; font-size: 17px; font-weight: 700; color: #FFFFFF !important; line-height: 1.2; }
.sb-sub  { font-size: 11px; color: rgba(255,255,255,0.55) !important; font-weight: 400; margin-top: 2px; letter-spacing: 0.03em; }

/* Section label */
.sb-label {
  font-size: 10px; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: rgba(255,255,255,0.4) !important;
  margin: 0 0 8px; padding-bottom: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* Links */
.sb-link {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 10px; border-radius: 5px; margin-bottom: 3px;
  text-decoration: none; color: rgba(255,255,255,0.82) !important;
  font-size: 13.5px; border: 1px solid transparent;
  transition: all 0.12s;
}
.sb-link:hover {
  background: rgba(255,255,255,0.09);
  border-color: rgba(255,255,255,0.12);
  color: #FFFFFF !important;
}
.sb-link-l { display: flex; align-items: center; gap: 9px; }
.sb-link-ico {
  width: 26px; height: 26px; border-radius: 4px;
  background: rgba(255,255,255,0.1);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
}
.sb-arr { font-size: 11px; color: rgba(255,255,255,0.25) !important; }

/* Emergency */
.sb-emergency {
  background: rgba(204,26,42,0.18);
  border: 1px solid rgba(204,26,42,0.35);
  border-left: 3px solid var(--gov-red);
  border-radius: 5px; padding: 12px 13px;
  margin: 1.2rem 0;
}
.sb-em-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #FF8A94 !important; margin-bottom: 4px; }
.sb-em-num   { font-family: 'Source Code Pro', monospace; font-size: 16px; font-weight: 500; color: #FFFFFF !important; letter-spacing: 0.05em; }
.sb-em-hours { font-size: 11px; color: rgba(255,255,255,0.45) !important; margin-top: 3px; }

/* Status */
.sb-status {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 5px; margin-top: 1rem;
}
.sb-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #4ADE80; box-shadow: 0 0 0 2px rgba(74,222,128,0.25);
  flex-shrink: 0; animation: blink 3s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.55} }
.sb-st-txt { font-size: 12px; color: rgba(255,255,255,0.5) !important; }

/* Sidebar Streamlit button */
div[data-testid="stButton"] button {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  color: rgba(255,255,255,0.75) !important;
  border-radius: 5px !important;
  font-family: 'Source Sans 3', sans-serif !important;
  font-size: 13px !important;
  transition: all 0.15s !important;
}
div[data-testid="stButton"] button:hover {
  background: rgba(255,255,255,0.13) !important;
  border-color: rgba(255,255,255,0.3) !important;
  color: #FFFFFF !important;
}

/* ── MAIN CONTENT ── */

/* Page header */
.page-header {
  background: var(--gov-white);
  border: 1px solid var(--gov-line);
  border-top: 4px solid var(--gov-navy);
  border-radius: 6px;
  padding: 1.5rem 1.75rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.ph-eyebrow {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px;
}
.ph-flag {
  display: flex; width: 22px; height: 15px;
  border-radius: 2px; overflow: hidden;
  border: 0.5px solid var(--gov-line);
}
.ph-flag-w { flex:1; background:#FFFFFF; }
.ph-flag-r { flex:1; background:#CC1A2A; }
.ph-flag-b { flex:1; background:#11396B; }
.ph-label {
  font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--gov-text-l);
}
.ph-title {
  font-family: 'Source Serif 4', serif;
  font-size: clamp(24px, 4vw, 34px);
  font-weight: 700; color: var(--gov-navy);
  line-height: 1.15; letter-spacing: -0.01em;
  margin-bottom: 6px;
}
.ph-title .red { color: var(--gov-red); }
.ph-desc { font-size: 15px; color: var(--gov-text-m); line-height: 1.6; }

/* Disclaimer */
.disclaimer {
  display: flex; gap: 11px; align-items: flex-start;
  background: var(--gov-amber-s);
  border: 1px solid rgba(122,92,30,0.2);
  border-left: 3px solid #C8920A;
  border-radius: 5px;
  padding: 11px 15px;
  margin-bottom: 1.25rem;
  font-size: 13px; line-height: 1.6;
  color: var(--gov-amber);
}
.disclaimer a { color: var(--gov-navy) !important; font-weight: 600; text-underline-offset: 2px; }
.disc-ico { flex-shrink: 0; font-size: 15px; margin-top: 1px; }

/* Empty state */
.empty-state {
  background: var(--gov-white); border: 1px solid var(--gov-line);
  border-radius: 6px; padding: 2.5rem 2rem;
  text-align: center; margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.es-icon { font-size: 38px; margin-bottom: 14px; }
.es-title {
  font-family: 'Source Serif 4', serif;
  font-size: 20px; font-weight: 700;
  color: var(--gov-navy); margin-bottom: 6px;
}
.es-desc { font-size: 14px; color: var(--gov-text-m); max-width: 440px; margin: 0 auto; line-height: 1.6; }

/* Suggestion grid header */
.sug-head {
  display: flex; align-items: center; gap: 10px;
  margin: 1.25rem 0 10px;
}
.sug-label {
  font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--gov-text-l);
  white-space: nowrap;
}
.sug-line { flex:1; height:1px; background: var(--gov-line); }

/* Suggestion buttons */
div[data-testid="stColumn"] div[data-testid="stButton"] button {
  background: var(--gov-white) !important;
  border: 1px solid var(--gov-line) !important;
  border-radius: 5px !important;
  color: var(--gov-text-m) !important;
  font-size: 13.5px !important;
  font-weight: 400 !important;
  text-align: left !important;
  padding: 11px 14px !important;
  line-height: 1.5 !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
  transition: all 0.15s !important;
  display: block !important;
}
div[data-testid="stColumn"] div[data-testid="stButton"] button:hover {
  border-color: var(--gov-navy) !important;
  color: var(--gov-navy) !important;
  background: var(--gov-blue-s) !important;
  box-shadow: 0 2px 8px rgba(17,57,107,0.1) !important;
}

/* Chat messages — force white on every inner element Streamlit dark-themes */
[data-testid="stChatMessage"],
[data-testid="stChatMessage"] > div,
[data-testid="stChatMessage"] > div > div,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] .stMarkdown {
  background: var(--gov-white) !important;
  color: var(--gov-text) !important;
}
[data-testid="stChatMessage"] {
  border: 1px solid var(--gov-line) !important;
  border-radius: 6px !important;
  padding: 1rem 1.25rem !important;
  margin-bottom: 0.75rem !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
/* User message tint — all inner divs */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div > div,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdown {
  background: var(--gov-blue-s) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  border-color: #C5D8EE !important;
}
/* Force readable text on all chat content */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] code {
  color: var(--gov-text) !important;
}

/* Meta badges */
.meta-row { display:flex; align-items:center; gap:6px; margin-top:10px; flex-wrap:wrap; }
.meta-badge {
  display:inline-flex; align-items:center; gap:4px;
  font-size:11px; font-weight:500;
  font-family:'Source Code Pro', monospace;
  padding:3px 8px; border-radius:3px;
  background:var(--gov-off); border:1px solid var(--gov-line);
  color:var(--gov-text-l);
}
.badge-lang { background:#EBF2FA; border-color:#B8D0EC; color:#1A4F8A; }
.badge-pii  { background:var(--gov-green-s); border-color:#A3D9BE; color:var(--gov-green); }

/* Feedback done state */
.fb-done {
  display:inline-flex; align-items:center; gap:6px;
  font-size:13px; color:var(--gov-green); font-weight:600;
  margin-top:12px; padding: 6px 12px;
  background: var(--gov-green-s);
  border: 1px solid #A3D9BE;
  border-radius: 5px;
}

/* Feedback buttons */
.feedback-area {
  display: flex; gap: 8px; margin-top: 12px; align-items: center;
}
.fb-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 16px; border-radius: 5px; cursor: pointer;
  font-family: 'Source Sans 3', sans-serif;
  font-size: 13px; font-weight: 500;
  border: 1px solid var(--gov-line);
  background: var(--gov-white);
  color: var(--gov-text-m);
  text-decoration: none; transition: all 0.15s;
  white-space: nowrap;
}
.fb-btn:hover { border-color: var(--gov-navy); color: var(--gov-navy); background: var(--gov-blue-s); }
.fb-btn-up:hover   { border-color: var(--gov-green); color: var(--gov-green); background: var(--gov-green-s); }
.fb-btn-down:hover { border-color: var(--gov-red);   color: var(--gov-red);   background: var(--gov-red-s);  }

/* Feedback column buttons — specific override for main area */
[data-testid="stChatMessage"] div[data-testid="stButton"] button {
  background: var(--gov-white) !important;
  border: 1px solid var(--gov-line) !important;
  color: var(--gov-text-m) !important;
  border-radius: 5px !important;
  font-family: 'Source Sans 3', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 6px 14px !important;
  line-height: 1.4 !important;
  white-space: nowrap !important;
  overflow: visible !important;
  height: auto !important;
  min-height: 36px !important;
  width: 100% !important;
  transition: all 0.15s !important;
}
[data-testid="stChatMessage"] div[data-testid="stButton"]:first-child button:hover {
  border-color: var(--gov-green) !important;
  color: var(--gov-green) !important;
  background: var(--gov-green-s) !important;
}
[data-testid="stChatMessage"] div[data-testid="stButton"]:last-child button:hover {
  border-color: var(--gov-red) !important;
  color: var(--gov-red) !important;
  background: var(--gov-red-s) !important;
}

/* Chat input */
[data-testid="stChatInput"] > div {
  background: var(--gov-white) !important;
  border: 1.5px solid var(--gov-line-d) !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInput"] > div:focus-within {
  border-color: var(--gov-navy) !important;
  box-shadow: 0 0 0 3px rgba(17,57,107,0.1) !important;
}
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] > div {
  background: transparent !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: var(--gov-text) !important;
  -webkit-text-fill-color: var(--gov-text) !important;
  font-family: 'Source Sans 3', sans-serif !important;
  font-size: 15px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: var(--gov-text-l) !important;
  -webkit-text-fill-color: var(--gov-text-l) !important;
}
[data-testid="stChatInput"] button {
  background: var(--gov-navy) !important;
  border-radius: 4px !important;
}
[data-testid="stChatInput"] button:hover {
  background: var(--gov-red) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--gov-off); }
::-webkit-scrollbar-thumb { background: var(--gov-line-d); border-radius: 3px; }

/* Mobile */
@media (max-width: 768px) {
  .main .block-container { padding: 1rem 0.75rem 3rem !important; }
  .page-header { padding: 1.1rem 1.1rem; }
  .ph-title { font-size: 22px; }
  .empty-state { padding: 1.75rem 1.25rem; }
  .disclaimer { font-size: 12px; }
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
DB_PATH = "/tmp/vector_db"
LANG_FLAGS = {
    "cs":"🇨🇿","sk":"🇸🇰","es":"🇪🇸","ar":"🇸🇦",
    "uk":"🇺🇦","ru":"🇷🇺","vi":"🇻🇳","zh":"🇨🇳",
    "de":"🇩🇪","fr":"🇫🇷","en":"🇬🇧",
}
LANG_NAMES = {
    "cs":"Czech","sk":"Slovak","es":"Spanish","ar":"Arabic",
    "uk":"Ukrainian","ru":"Russian","vi":"Vietnamese",
    "zh":"Chinese","de":"German","fr":"French","en":"English",
}
RESOURCES = [
    ("🏛️","OAMP Appointments",      "https://frs.gov.cz"),
    ("🌐","Foreigners Info Portal",  "https://ipc.gov.cz"),
    ("🏥","PVZP Health Insurance",   "https://pvzp.cz"),
    ("📮","Czech POINT — Data Box",  "https://czechpoint.cz"),
    ("⚖️","Free Legal Aid — SIMI",   "https://migrace.com"),
    ("⚖️","Free Legal Aid — OPU",    "https://opu.cz"),
]
SUGGESTIONS = [
    ("💶","Financial requirements for a 12-month stay"),
    ("📋","Mandatory steps within 3 days of arrival"),
    ("📅","Deadline to apply for permit extension"),
    ("🔖","When do I need a Bridge Label (překlenovací štítek)?"),
    ("💼","Can I work while on a student residence permit?"),
    ("🏥","What health insurance is valid for my visa?"),
]

# ── INIT ───────────────────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    with st.spinner("Initialising knowledge base — takes ~1 min on first run..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
        except Exception as e:
            st.error(f"Initialisation failed: {e}")
            st.info("Please refresh or check your GOOGLE_API_KEY.")
            st.stop()

if "chat" not in st.session_state:
    try:
        from src.rag_engine import ImmigraSmartChat
        st.session_state.chat = ImmigraSmartChat()
    except Exception as e:
        st.error(f"Failed to connect to AI service: {e}")
        st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
if "feedback" not in st.session_state: st.session_state.feedback = {}

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-flag">
        <div class="f-w"></div><div class="f-r"></div><div class="f-b"></div>
      </div>
      <div>
        <div class="sb-name">ImmigraSmart</div>
        <div class="sb-sub">Czech Republic · Immigration AI</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-wrap">', unsafe_allow_html=True)

    # Resources
    st.markdown('<div class="sb-label">Government Resources</div>', unsafe_allow_html=True)
    links = "".join(
        f'<a class="sb-link" href="{url}" target="_blank">'
        f'<span class="sb-link-l">'
        f'<span class="sb-link-ico">{ico}</span>{name}'
        f'</span><span class="sb-arr">↗</span></a>'
        for ico, name, url in RESOURCES
    )
    st.markdown(f'<div style="margin-bottom:1.25rem">{links}</div>', unsafe_allow_html=True)

    # Emergency
    st.markdown("""
    <div class="sb-emergency">
      <div class="sb-em-label">🚨 OAMP Helpline</div>
      <div class="sb-em-num">+420 974 801 801</div>
      <div class="sb-em-hours">Mon–Fri · 08:00–17:00</div>
    </div>
    """, unsafe_allow_html=True)

    # Status
    st.markdown("""
    <div class="sb-status">
      <div class="sb-dot"></div>
      <div class="sb-st-txt">System active · KB v2026.2</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("↺  Reset conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.session_state.chat.reset()
        st.rerun()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="ph-eyebrow">
    <div class="ph-flag">
      <div class="ph-flag-w"></div>
      <div class="ph-flag-r"></div>
      <div class="ph-flag-b"></div>
    </div>
    <span class="ph-label">Czech Republic · Official Immigration Guidance</span>
  </div>
  <div class="ph-title">Immigra<span class="red">Smart</span> AI</div>
  <div class="ph-desc">
    AI-powered assistant for international students navigating visas,
    residence permits, and post-arrival obligations in the Czech Republic.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
  <span class="disc-ico">⚠️</span>
  <span>
    <strong style="color:#7A5C1E">Important notice:</strong>
    This assistant provides general guidance only — not legal advice.
    Always verify current requirements with
    <a href="https://frs.gov.cz" target="_blank">OAMP (frs.gov.cz)</a>
    or a qualified immigration lawyer before acting.
  </span>
</div>
""", unsafe_allow_html=True)

# ── EMPTY STATE + SUGGESTIONS ──────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
      <div class="es-icon">🏛️</div>
      <div class="es-title">How can I help you today?</div>
      <div class="es-desc">
        Ask about visas, residence permits, health insurance,
        financial requirements, or what to do after you arrive.
      </div>
    </div>
    <div class="sug-head">
      <span class="sug-label">Common inquiries</span>
      <span class="sug-line"></span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for i, (emoji, text) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(f"{emoji}  {text}", key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_input = text
                st.rerun()

# ── CHAT HISTORY ───────────────────────────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    avatar = "🧑‍💼" if msg["role"] == "user" else "🏛️"
    with st.chat_message(msg["role"], avatar=avatar):
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
                badges += f'<span class="meta-badge badge-pii">🔒 PII Protected · {entities}</span>'
            if badges:
                st.markdown(f'<div class="meta-row">{badges}</div>', unsafe_allow_html=True)

        if msg["role"] == "assistant":
            existing = st.session_state.feedback.get(idx)
            if existing:
                label = "Marked as helpful" if existing == "up" else "Feedback recorded"
                icon  = "✓" if existing == "up" else "·"
                st.markdown(f'<div class="fb-done">{icon} {label}</div>', unsafe_allow_html=True)
            else:
                # Inline feedback buttons that don't wrap or clip
                col_up, col_dn, col_pad = st.columns([1.4, 1.8, 7])
                with col_up:
                    if st.button("👍  Helpful", key=f"up_{idx}", use_container_width=True):
                        st.session_state.feedback[idx] = "up"
                        st.rerun()
                with col_dn:
                    if st.button("👎  Not helpful", key=f"dn_{idx}", use_container_width=True):
                        st.session_state.feedback[idx] = "down"
                        st.rerun()

# ── INPUT ──────────────────────────────────────────────────────────────────────
pending    = st.session_state.pop("pending_input", None)
user_input = st.chat_input(
    "Ask about visas, permits, insurance, financial requirements..."
) or pending

if user_input:
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("Retrieving official guidance..."):
            try:
                answer, meta = st.session_state.chat.ask(user_input)

                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": meta
                })
                st.session_state.messages.append({
                    "role": "assistant", "content": answer, "meta": meta
                })

                st.markdown(answer)
                st.rerun()

            except Exception as e:
                st.error(
                    "Service temporarily unavailable. Please try again.\n\n"
                    "For immediate assistance: **+420 974 801 801**"
                )
                st.caption(f"Error: {e}")
                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": {}
                })