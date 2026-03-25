import os
import streamlit as st

st.set_page_config(
    page_title="ImmigraSmart AI | Official Assistant",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── DESIGN SYSTEM (Government & Mobile Responsive) ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    /* Official Government Palette */
    --gov-blue: #0F2D52;
    --gov-blue-light: #1A4980;
    --gov-red: #D7141A;
    --bg-main: #F4F7F9;
    --bg-card: #FFFFFF;
    --text-dark: #1E293B;
    --text-muted: #64748B;
    --border-light: #E2E8F0;
    --notice-bg: #FFFBEB;
    --notice-border: #F59E0B;
    --notice-text: #92400E;
    --success: #059669;
}

/* Force Light Theme for Accessibility & Trust */
.stApp { background: var(--bg-main) !important; font-family: 'Inter', sans-serif; color: var(--text-dark); }
.main .block-container { padding-top: 2rem !important; max-width: 800px; }

/* SOLUCIÓN AL MENÚ HAMBURGUESA: 
   Solo ocultamos el footer y el botón de deploy. 
   Dejamos el 'header' visible para que aparezca el menú ☰ en móviles */
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border-light) !important;
}
[data-testid="stSidebar"] * { color: var(--text-dark) !important; }
[data-testid="stSidebarContent"] { padding: 1.5rem 1rem; }

.sb-brand {
    display: flex; align-items: center; gap: 12px;
    padding: 0 0 1.2rem; border-bottom: 2px solid var(--gov-blue);
    margin-bottom: 1.2rem;
}
.sb-brand-icon {
    width: 42px; height: 42px; background: var(--gov-blue);
    border-radius: 4px; display: flex; align-items: center; 
    justify-content: center; flex-shrink: 0;
}
.sb-brand-title { font-weight: 700; font-size: 16px; color: var(--gov-blue) !important; }
.sb-brand-sub { font-size: 12px; color: var(--text-muted) !important; font-weight: 500; }

.sb-link-group { margin-bottom: 1.5rem; }
.sb-link-label { font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--gov-blue) !important; margin-bottom: 10px; }
.sb-link {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px; border-radius: 4px; margin-bottom: 4px;
    text-decoration: none; color: var(--gov-blue-light) !important;
    font-size: 14px; transition: background 0.15s;
    border: 1px solid var(--border-light);
    background: var(--bg-card);
}
.sb-link:hover { background: var(--bg-main); border-color: var(--gov-blue-light); }

.sb-phone {
    background: var(--bg-main); border: 1px solid var(--border-light);
    border-left: 4px solid var(--gov-red); border-radius: 4px; 
    padding: 12px 14px; margin-bottom: 1.2rem;
}
.sb-phone-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--gov-red) !important; margin-bottom: 4px; }
.sb-phone-num { font-size: 16px; font-weight: 700; color: var(--text-dark) !important;}

.sb-status { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-top: 1px solid var(--border-light); margin-top: 10px;}
.sb-status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); }
.sb-status-text { font-size: 12px; color: var(--text-muted) !important; font-weight: 500;}

/* Buttons */
div[data-testid="stButton"] button {
    background: var(--bg-card) !important; border: 1px solid var(--border-light) !important;
    color: var(--text-dark) !important; border-radius: 4px !important;
    font-weight: 500 !important; font-size: 14px !important;
}
div[data-testid="stButton"] button:hover {
    border-color: var(--gov-blue) !important; color: var(--gov-blue) !important;
    background: var(--bg-main) !important;
}

/* Header */
.page-header { margin-bottom: 1.5rem; }
.header-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--gov-blue); border-radius: 4px; padding: 4px 10px;
    font-size: 12px; font-weight: 600; color: #FFFFFF; margin-bottom: 12px;
}
.page-title {
    font-weight: 800; font-size: clamp(24px, 5vw, 36px); 
    color: var(--gov-blue); line-height: 1.2;
}
.page-sub { font-size: 16px; color: var(--text-muted); margin-top: 8px; }

/* Notice / Disclaimer */
.disclaimer {
    background: var(--notice-bg); border: 1px solid var(--notice-border);
    border-radius: 4px; padding: 12px 16px; margin-bottom: 1.5rem;
    font-size: 14px; color: var(--notice-text); line-height: 1.5;
    display: flex; gap: 10px; align-items: flex-start;
}
.disclaimer a { color: var(--gov-blue) !important; font-weight: 600; }
.disclaimer strong { color: var(--notice-text); }

/* Chat Elements */
.suggestions-label {
    font-size: 12px; font-weight: 600; text-transform: uppercase; 
    color: var(--text-muted); margin-bottom: 12px; border-bottom: 1px solid var(--border-light); padding-bottom: 4px;
}

[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 6px !important;
    padding: 1rem !important;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
[data-testid="stChatMessage"][data-baseweb="user"] {
    background: var(--bg-main) !important;
}

.meta-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.meta-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px; font-weight: 500; padding: 4px 8px; border-radius: 4px;
    background: var(--bg-main); border: 1px solid var(--border-light); color: var(--text-muted);
}
.fb-given { font-size: 13px; color: var(--success); font-weight: 500; margin-top: 8px; }

/* --- SOLUCIÓN DEFINITIVA A LA CAJA DE TEXTO (Input Box) --- */
[data-testid="stChatInput"] { 
    background: transparent !important; 
}

/* 1. Contenedor principal externo (Fondo Blanco) */
[data-testid="stChatInput"] > div {
    background-color: var(--bg-card) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 6px !important;
}

/* 2. Matar el fondo oscuro de los contenedores internos de Streamlit (baseweb) */
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] > div {
    background-color: transparent !important;
}

/* 3. Estilo del área de texto (Letra oscura) */
[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: var(--text-dark) !important;
    -webkit-text-fill-color: var(--text-dark) !important; /* Fuerza webkit/Chrome */
    font-size: 15px !important;
}

/* 4. Color del texto de ayuda (Placeholder) */
[data-testid="stChatInput"] textarea::placeholder { 
    color: var(--text-muted) !important; 
    -webkit-text-fill-color: var(--text-muted) !important;
}

/* 5. Borde azul al hacer clic para escribir */
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--gov-blue) !important;
}

/* 6. Cambiar el color del botón de enviar (Flecha) a Azul Oficial */
[data-testid="stChatInput"] button {
    background-color: var(--gov-blue) !important;
    color: white !important;
}
[data-testid="stChatInput"] button:hover {
    background-color: var(--gov-blue-light) !important;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    .main .block-container { padding-top: 1rem !important; padding-left: 1rem; padding-right: 1rem; }
    .page-title { font-size: 24px; }
    .page-sub { font-size: 14px; }
    .disclaimer { flex-direction: column; font-size: 13px; }
    [data-testid="stChatMessage"] { padding: 0.75rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ── SVG ICONS (Clean & Professional) ──────────────────────────────────────────
ICONS = {
    "logo":   '<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2L2 7l10 5 10-5-10-5z" fill="#FFFFFF"/><path d="M2 17l10 5 10-5" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/><path d="M2 12l10 5 10-5" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/></svg>',
    "link":   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    "phone":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    "spark":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2v20M17 5l-10 14M22 12H2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    "lock":   '<svg width="12" height="12" viewBox="0 0 24 24" fill="none"><rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2"/><path d="M7 11V7a5 5 0 0110 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    "alert":  '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="flex-shrink:0;"><path d="M10.3 3.3L2 20h20L13.7 3.3a2 2 0 00-3.4 0z" stroke="#92400E" stroke-width="2" stroke-linejoin="round"/><path d="M12 10v4M12 17v.5" stroke="#92400E" stroke-width="2" stroke-linecap="round"/></svg>',
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
    with st.spinner("Initializing knowledge base..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
        except Exception as e:
            st.error(f"System initialization failed: {e}")
            st.info("Please refresh the page or check system parameters.")
            st.stop()

if "chat" not in st.session_state:
    try:
        from src.rag_engine import ImmigraSmartChat
        st.session_state.chat = ImmigraSmartChat()
    except Exception as e:
        st.error(f"Failed to connect to AI service: {e}")
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
        <div class="sb-brand-sub">Official Portal Assistant</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-link-label">Government Resources</div>', unsafe_allow_html=True)
    resources = [
        ("OAMP Appointments",        "https://frs.gov.cz"),
        ("Foreigners Portal",        "https://ipc.gov.cz"),
        ("PVZP Health Insurance",    "https://pvzp.cz"),
        ("Czech POINT (Data Box)",   "https://czechpoint.cz"),
        ("Free Legal Aid — SIMI",    "https://migrace.com"),
        ("Free Legal Aid — OPU",     "https://opu.cz"),
    ]
    links_html = "".join(
        f'<a class="sb-link" href="{url}" target="_blank">'
        f'{name} {ICONS["link"]}</a>'
        for name, url in resources
    )
    st.markdown(f'<div class="sb-link-group">{links_html}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-phone">
      <div class="sb-phone-label">{ICONS['phone']} OAMP Helpline</div>
      <div class="sb-phone-num">+420 974 801 801</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-status">
      <div class="sb-status-dot"></div>
      <div class="sb-status-text">System Active · DB v2026.2</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.session_state.chat.reset()
        st.rerun()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="header-badge">{ICONS['spark']} Automated Support</div>
  <div class="page-title">ImmigraSmart Assistant</div>
  <div class="page-sub">Official guidance for international students in the Czech Republic.</div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="disclaimer">
  {icon('alert')}
  <div>
    <strong>Important Notice:</strong> Information provided is for general guidance only and does not constitute legal advice. 
    Always verify current requirements directly with <a href="https://frs.gov.cz" target="_blank">OAMP</a>.
  </div>
</div>""", unsafe_allow_html=True)

# ── SUGGESTIONS ────────────────────────────────────────────────────────────────
SUGGESTIONS = [
    "Financial requirements for a 12-month stay?",
    "Mandatory actions within 3 days of arrival?",
    "Timeline for permit extension applications?",
    "When is a Bridge Label required?",
]

if not st.session_state.messages:
    st.markdown('<div class="suggestions-label">Common Inquiries</div>', unsafe_allow_html=True)
    # Streamlit natively stacks columns on mobile, this works well for responsiveness
    cols = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(text, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_input = text
                st.rerun()

# ── CHAT HISTORY ───────────────────────────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🏛️"):
        st.markdown(msg["content"])

        if msg["role"] == "user":
            meta   = msg.get("meta", {})
            badges = ""
            lang   = meta.get("language", "en")
            if lang != "en":
                flag  = LANG_FLAGS.get(lang, "🌐")
                lname = LANG_NAMES.get(lang, lang)
                badges += f'<span class="meta-badge">{flag} {lname}</span>'
            if meta.get("pii_detected"):
                entities = ", ".join(meta.get("pii_entities", []))
                badges += f'<span class="meta-badge">{icon("lock")} PII Protected · {entities}</span>'
            if badges:
                st.markdown(f'<div class="meta-row">{badges}</div>', unsafe_allow_html=True)

        if msg["role"] == "assistant":
            existing = st.session_state.feedback.get(idx)
            if existing:
                st.markdown(f'<div class="fb-given">Response recorded as helpful.</div>', unsafe_allow_html=True)
            else:
                c1, c2, _ = st.columns([1, 1, 10])
                if c1.button("Helpful", key=f"up_{idx}"):
                    st.session_state.feedback[idx] = "up"
                    st.rerun()
                if c2.button("Not Helpful", key=f"down_{idx}"):
                    st.session_state.feedback[idx] = "down"
                    st.rerun()

# ── INPUT ──────────────────────────────────────────────────────────────────────
pending    = st.session_state.pop("pending_input", None)
user_input = st.chat_input("Enter your inquiry regarding visas, permits, or insurance...") or pending

if user_input:
    # Render user message immediately
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_input)

    # Generate and render assistant response
    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("Retrieving official guidance..."):
            try:
                answer, meta = st.session_state.chat.ask(user_input)

                # Append BEFORE rerun so messages survive exceptions
                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": meta
                })
                st.session_state.messages.append({
                    "role": "assistant", "content": answer, "meta": meta
                })

                st.markdown(answer)
                st.rerun()

            except Exception as e:
                # On error: show message, do NOT rerun (so user can read it)
                st.error(
                    "Service temporarily unavailable. Please try again later.\n\n"
                    "For immediate assistance, contact OAMP: **+420 974 801 801**"
                )
                st.caption(f"Error Code: {e}")
                # Still save the user message so chat history is consistent
                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": {}
                })