import sys
import os
import streamlit as st
from pypdf import PdfReader
import streamlit.components.v1 as components  # <-- NUEVO: Para inyectar JavaScript
# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ImmigraSmart — Czech Republic",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. PATH SETUP (Connect to src folder)
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
# 4. INITIALIZE SESSION & BACKEND (ID FIJO PARA TESTING)
# ─────────────────────────────────────────────────────────────────────────────
import uuid

# A. Gestión de Identidad (FIJAMOS EL ID AQUÍ)
# Comentamos el UUID dinámico para que no cambie al refrescar
# if "session_id" not in st.session_state:
#     st.session_state.session_id = str(uuid.uuid4())

# Forzamos un ID de prueba único. 
# Puedes poner tu nombre o cualquier código que quieras.
st.session_state.session_id = "oskar_pro_test_001" 

# B. Estados de entrada y documentos
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "uploaded_doc_text" not in st.session_state:
    st.session_state.uploaded_doc_text = None

# C. Inyección de Secrets (Mantenemos esto igual)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass 

# D. Carga del Motor
if "chat_engine" not in st.session_state:
    try:
        from rag_engine import ImmigraSmartChat
        # Al pasarle "oskar_pro_test_001", el motor buscará ESE historial en Supabase
        st.session_state.chat_engine = ImmigraSmartChat(session_id=st.session_state.session_id)
    except Exception as e:
        st.error(f"🚨 Error: {e}")
        st.stop()
# ─────────────────────────────────────────────────────────────────────────────
# 5. SIDEBAR NAVIGATION & INFO
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🇨🇿 ImmigraSmart")
    st.caption("Czech Republic · AI Assistant")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`") # Muestra los primeros 8 caracteres
    
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.uploaded_doc_text = None # Limpiamos el PDF si hay nueva charla
        st.session_state.chat_engine.reset() 
        st.rerun()

    st.divider()
    
    # --- NUEVO: CARGA DE DOCUMENTOS (PDF) ---
    st.subheader("📄 Document Analysis")
    st.caption("Upload a lease or insurance contract")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            st.session_state.uploaded_doc_text = text
            st.success("✅ Document loaded into AI memory!")
        except Exception as e:
            st.error("Error reading PDF. Please try another file.")
            st.session_state.uploaded_doc_text = None
    else:
        st.session_state.uploaded_doc_text = None 

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
# Ahora preguntamos si el historial del MOTOR está vacío
if not st.session_state.chat_engine.chat_history:
    st.info("🏛️ **How can I help you today?**\nAsk about visas, residence permits, health insurance, or financial requirements.")
    
    st.write("### 💡 Quick Questions")
    cols = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(text, use_container_width=True):
                st.session_state.pending_input = text.split(" ", 1)[1] # Strip emoji
                st.rerun()
# ─────────────────────────────────────────────────────────────────────────────
# 8. CHAT HISTORY DISPLAY (Sincronizado con Supabase)
# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANTE: Ahora iteramos sobre el historial del MOTOR, no sobre la lista local
for i, msg in enumerate(st.session_state.chat_engine.chat_history):
    
    # 1. Mapeamos los roles de LangChain (human/ai) a los de Streamlit (user/assistant)
    role = "user" if msg.type == "human" else "assistant"
    avatar = "🧑‍💼" if role == "user" else "🏛️"
    
    with st.chat_message(role, avatar=avatar):
        # 2. Mostramos el contenido del mensaje
        st.markdown(msg.content)
        
        # 3. Badges de Metadatos (Opcional)
        # Nota: Como Supabase guarda solo texto, los badges históricos se verán 
        # en la sesión actual pero podrían no aparecer tras un refresh total 
        # a menos que los guardemos en la DB también (Fase C).
        if role == "user" and hasattr(msg, "additional_kwargs"):
            meta = msg.additional_kwargs.get("meta", {})
            meta_html = ""
            if meta.get("language") and meta["language"] != "en":
                meta_html += f'<span class="badge-lang">🌐 {meta["language"].upper()}</span> '
            if meta.get("pii_detected"):
                meta_html += '<span class="badge-pii">🔒 PII Protected</span>'
            if meta_html:
                st.markdown(meta_html, unsafe_allow_html=True)
                
        # 4. Botones de Feedback para las respuestas de la IA
        if role == "assistant":
            feedback = st.feedback("thumbs", key=f"fb_{st.session_state.session_id}_{i}")
            if feedback is not None:
                st.toast("¡Gracias! Tu feedback ayuda a mejorar ImmigraSmart.", icon="✅")

# ─────────────────────────────────────────────────────────────────────────────
# 9. CHAT INPUT LOGIC (Supabase Sincronizado)
# ─────────────────────────────────────────────────────────────────────────────
user_query = st.chat_input("Escribe tu duda sobre visas, permisos o seguros...")

# Manejo de clics en sugerencias
if st.session_state.pending_input:
    user_query = st.session_state.pending_input
    st.session_state.pending_input = None

if user_query:
    # 1. Mostramos el mensaje del usuario inmediatamente en la pantalla
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_query)

    # 2. Procesamos con la IA
    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("Consultando guías oficiales checas..."):
            try:
                # LLAMADA AL MOTOR 
                # Internamente, .ask() guarda en Supabase y actualiza su historial
                answer, meta = st.session_state.chat_engine.ask(
                    user_query,
                    user_document=st.session_state.uploaded_doc_text
                )

                # 3. Mostramos la respuesta
                st.markdown(answer)
                
                # 4. Mostramos los badges de metadatos (opcional, muy útil)
                meta_html = ""
                lang = meta.get("language", "en")
                if lang != "en":
                    meta_html += f'<span class="badge-lang">🌐 {lang.upper()}</span> '
                if meta.get("pii_detected"):
                    meta_html += '<span class="badge-pii">🔒 PII Protegido</span>'
                
                if meta_html:
                    st.markdown(meta_html, unsafe_allow_html=True)
                
                # 5. ¡IMPORTANTE! Forzamos el rerun. 
                # Al recargar, la SECCIÓN 8 leerá el nuevo historial del motor 
                # y todo se verá perfecto y ordenado.
                st.rerun()

            except Exception as e:
                st.error("⚠️ **System Error:** No pude procesar tu solicitud.")
                with st.expander("Detalles del error"):
                    st.code(str(e))
                    # ─────────────────────────────────────────────────────────────────────────────
# 10. AUTO-SCROLL MAGIC (UX IMPROVEMENT)
# ─────────────────────────────────────────────────────────────────────────────
# Este pequeño script de JS fuerza a la pantalla a bajar suavemente 
# hasta el último mensaje después de cada recarga.
# ─────────────────────────────────────────────────────────────────────────────
# 10. AUTO-SCROLL MAGIC (UX IMPROVEMENT - TIMEOUT VERSION)
# ─────────────────────────────────────────────────────────────────────────────
# Este script espera a que la página termine de renderizarse y luego fuerza el scroll.
components.html(
    """
    <script>
        // Función para bajar la pantalla
        const scrollToBottom = () => {
            // Buscamos los contenedores principales que usa Streamlit
            const containers = window.parent.document.querySelectorAll('.main, [data-testid="stMain"], [data-testid="stAppViewContainer"]');
            
            containers.forEach(container => {
                container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
            });
        };

        // Le damos 500 milisegundos de ventaja a Streamlit para que termine de cargar el texto
        setTimeout(scrollToBottom, 500);
    </script>
    """,
    height=0
)