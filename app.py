import sys
import os
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIGURATION (¡Debe ser siempre lo primero!)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ImmigraSmart — Czech Republic",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. PATH SETUP (Conectamos con la carpeta src)
# ─────────────────────────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

# Minimal CSS just for metadata badges
st.markdown("""
<style>
    .badge-lang { background: #DBEAFE; color: #1E40AF; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 500; }
    .badge-pii  { background: #EDF7F2; color: #1B6B3A; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. CONSTANTS & RESOURCES
# ─────────────────────────────────────────────────────────────────────────────
RESOURCES = [
    ("🏛️", "Ministry of Interior (OAMP)", "https://frs.gov.cz/en/"),
    ("🌐", "Foreigners Info Portal", "https://ipc.gov.cz/en/"),
    ("🏥", "VZP Public Health Insurance", "https://www.vzp.cz/en/"),
    ("🏢", "Integration Centre Prague (ICP)", "https://icpraha.com/en/"),
    ("⚖️", "SIMI - Free Legal Aid", "https://www.migrace.com/en/"),
]

SUGGESTIONS = [
    "💶 Financial requirements for a 12-month stay",
    "📋 Mandatory steps within 3 days of arrival",
    "📅 Deadline to apply for permit extension",
    "💼 Can I work on a student residence permit?"
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. INITIALIZE BACKEND (RAG ENGINE) & STATE
# ─────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# INYECCIÓN DE SECRETS PARA LA NUBE:
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass # Si no hay archivo secrets (porque estamos en local), usa el .env normal

# Intentamos cargar tu motor.
if "chat_engine" not in st.session_state:
    try:
        # Si la base de datos NO existe, la construimos automáticamente
        if not os.path.exists("/tmp/vector_db"):
            with st.spinner("⏳ Cloud Deployment Detected: Building knowledge base for the first time. This will take a minute..."):
                # Importamos tu script de ingestión y lo corremos
                from ingest import main as run_ingestion
                run_ingestion(force=True)
                st.toast("✅ Knowledge Base built successfully!")
                
        # Una vez que estamos seguros de que existe, cargamos el cerebro
        from rag_engine import ImmigraSmartChat
        st.session_state.chat_engine = ImmigraSmartChat()
        
    except Exception as e:
        st.error(f"🚨 **System Initialization Error:** {e}")
        with st.expander("Ver detalles del error"):
            st.code(str(e))
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 5. SIDEBAR NAVIGATION & INFO
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🇨🇿 ImmigraSmart")
    st.caption("Czech Republic · AI Assistant")
    
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.chat_engine.reset() # Limpiamos la memoria del RAG
        st.rerun()

    st.divider()
    
    st.subheader("🔗 Essential Portals")
    for ico, name, url in RESOURCES:
        st.markdown(f"{ico} [{name}]({url})")

    st.divider()

    st.error("""
    🚨 **OAMP Helpline**
    
    **Calls: +420 974 801 801**
    
    **Operating Hours:**
    Mon–Thurs: 08:00–16:00  and Friday: 08:00–12:00
              
    **For urgent assistance with residence permits, visas, or legal issues, contact the OAMP helpline.**
    """)

    st.divider()
    
    st.success("🟢 Knowledge Base: Active (ChromaDB)")

# ─────────────────────────────────────────────────────────────────────────────
# 6. MAIN CONTENT HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.caption("🇨🇿 CZECH REPUBLIC · OFFICIAL IMMIGRATION GUIDANCE")
st.title("ImmigraSmart AI")
st.markdown("Your AI-powered guide for navigating visas, residence permits, and integration in the Czech Republic.")

st.warning("⚠️ **Important notice:** This assistant provides general guidance based on public documents — not legal advice. Always verify with [OAMP](https://frs.gov.cz) before acting.")

# ─────────────────────────────────────────────────────────────────────────────
# 7. EMPTY STATE & SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.info("🏛️ **How can I help you today?**\nAsk about visas, residence permits, health insurance, or financial requirements.")
    
    st.write("### 💡 Quick Questions")
    cols = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(text, use_container_width=True):
                st.session_state.pending_input = text.split(" ", 1)[1] # Strip emoji
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 8. CHAT HISTORY DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    avatar = "🧑‍💼" if msg["role"] == "user" else "🏛️"
    
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        
        # Add metadata badges for user queries
        if msg["role"] == "user" and msg.get("meta"):
            meta_html = ""
            lang = msg["meta"].get("language", "en")
            if lang != "en":
                meta_html += f'<span class="badge-lang">🌐 {lang.upper()}</span> '
            if msg["meta"].get("pii_detected"):
                meta_html += '<span class="badge-pii">🔒 PII Protected</span>'
            if meta_html:
                st.markdown(meta_html, unsafe_allow_html=True)
                
        # Add Like/Dislike buttons for Assistant answers
        if msg["role"] == "assistant":
            feedback = st.feedback("thumbs", key=f"feedback_{i}")
            if feedback is not None:
                st.toast("Thanks for the feedback! It helps improve the AI.", icon="✅")

# ─────────────────────────────────────────────────────────────────────────────
# 9. CHAT INPUT LOGIC
# ─────────────────────────────────────────────────────────────────────────────
user_query = st.chat_input("Ask about visas, permits, insurance...")

# Handle suggestion clicks
if st.session_state.pending_input:
    user_query = st.session_state.pending_input
    st.session_state.pending_input = None

if user_query:
    # Mostramos el mensaje del usuario inmediatamente
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_query)

    # Procesamos con la IA
    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("Consulting Czech immigration guidelines..."):
            try:
                # LLAMADA AL CEREBRO (rag_engine.py maneja el idioma, PII y la búsqueda)
                answer, meta = st.session_state.chat_engine.ask(user_query)

                st.markdown(answer)
                
                # Guardamos en el historial del frontend
                st.session_state.messages.append({"role": "user", "content": user_query, "meta": meta})
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Rerun para que se pinten los badges de PII/Idioma correctamente
                st.rerun()

            except Exception as e:
                st.error("⚠️ **System Error:** I couldn't process your request right now.")
                st.info("Check your terminal for detailed error logs.")
                with st.expander("Technical details for developers"):
                    st.code(str(e))