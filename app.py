import sys
import os
import streamlit as st
from pypdf import PdfReader
import streamlit.components.v1 as components

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
# 4. SESSION STATE INITIALIZATION
# Must be done early — before any widget reads these values.
# ─────────────────────────────────────────────────────────────────────────────
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

if "uploaded_doc_text" not in st.session_state:
    st.session_state.uploaded_doc_text = None

if "user" not in st.session_state:
    st.session_state.user = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ─────────────────────────────────────────────────────────────────────────────
# 5. AUTHENTICATION & SUPABASE CLIENT
# ─────────────────────────────────────────────────────────────────────────────
from supabase import create_client, Client
from dotenv import load_dotenv

# Load local .env file (development)
load_dotenv()

# Inject Streamlit Cloud secrets into environment variables (production)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    if "SUPABASE_URL" in st.secrets:
        os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
    if "SUPABASE_KEY" in st.secrets:
        os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

@st.cache_resource
def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing Supabase credentials. Check your .env file or Streamlit secrets.")
    return create_client(url, key)

supabase_auth = get_supabase_client()

# ─────────────────────────────────────────────────────────────────────────────
# 6. SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🇨🇿 ImmigraSmart")
    st.caption("Czech Republic · AI Assistant")

    # Only show user info if logged in
    if st.session_state.user is not None:
        st.caption(f"👤 User: `{st.session_state.user.email}`")
        if st.session_state.session_id:
            st.caption(f"🔑 Session: `{str(st.session_state.session_id)[:8]}...`")

        if st.button("🚪 Sign Out", use_container_width=True):
            supabase_auth.auth.sign_out()
            st.session_state.user = None
            st.session_state.session_id = None
            st.session_state.pop("chat_engine", None)
            st.rerun()
    else:
        st.caption("🔴 Status: Not signed in")

    st.divider()

    # New Conversation button
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.uploaded_doc_text = None
        if "chat_engine" in st.session_state:
            st.session_state.chat_engine.reset()
        st.rerun()

    st.divider()

    # Document upload
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

    # Essential portals
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
# 7. LOGIN / REGISTRATION SCREEN
# Shown only when the user is not authenticated. st.stop() blocks the rest.
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.title("🔐 Sign in to ImmigraSmart")
    st.markdown("Sign in to access your AI legal assistant and save your consultation history.")

    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        login_email = st.text_input("Email address", key="login_email")
        login_pass  = st.text_input("Password", type="password", key="login_pass")

        if st.button("Sign In", type="primary"):
            if not login_email or not login_pass:
                st.error("Please enter both your email and password.")
            else:
                with st.spinner("Verifying credentials..."):
                    try:
                        res = supabase_auth.auth.sign_in_with_password(
                            {"email": login_email, "password": login_pass}
                        )
                        st.session_state.user       = res.user
                        st.session_state.session_id = res.user.id
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "invalid login credentials" in error_msg or "invalid" in error_msg:
                            st.error(
                                "❌ Incorrect email or password. Please try again, "
                                "or create a new account in the **Create Account** tab."
                            )
                        elif "email not confirmed" in error_msg:
                            st.warning(
                                "📧 Your email address hasn't been confirmed yet. "
                                "Please check your inbox and click the confirmation link first."
                            )
                        elif "rate limit" in error_msg:
                            st.error(
                                "⏳ Too many login attempts. Please wait a few minutes before trying again."
                            )
                        else:
                            st.error(f"Sign-in failed: {str(e)}")

    with tab_register:
        reg_email = st.text_input("Email address", key="reg_email")
        reg_pass  = st.text_input(
            "Password (min. 6 characters)", type="password", key="reg_pass"
        )

        if st.button("Create Account"):
            # Basic client-side validation before hitting Supabase
            if not reg_email or "@" not in reg_email:
                st.error("Please enter a valid email address.")
            elif len(reg_pass) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                with st.spinner("Creating your account..."):
                    try:
                        res = supabase_auth.auth.sign_up(
                            {"email": reg_email, "password": reg_pass}
                        )
                        # Auto-login if Supabase returns a session immediately
                        # (happens when email confirmation is disabled in Supabase settings)
                        if res.session:
                            st.session_state.user       = res.user
                            st.session_state.session_id = res.user.id
                            st.rerun()
                        else:
                            # Email confirmation is required — ask user to verify first
                            st.success(
                                "✅ Account created! Please check your inbox to confirm "
                                "your email address, then come back and sign in."
                            )
                    except Exception as e:
                        error_msg = str(e).lower()

                        if "rate limit" in error_msg or "email rate limit exceeded" in error_msg:
                            st.error(
                                "⏳ **Too many sign-up attempts.**\n\n"
                                "Supabase limits how many registration emails can be sent per hour. "
                                "Please wait a few minutes and try again — or sign in if you already "
                                "have an account."
                            )
                        elif "already registered" in error_msg or "user already exists" in error_msg:
                            st.warning(
                                "📧 This email is already registered. "
                                "Please go to the **Sign In** tab instead."
                            )
                        elif "password" in error_msg:
                            st.error(
                                "🔑 Password does not meet requirements. "
                                "Please use at least 6 characters."
                            )
                        elif "invalid email" in error_msg:
                            st.error("📧 That email address doesn't look valid. Please double-check it.")
                        else:
                            st.error(f"Registration failed: {str(e)}")

    # Stop here — nothing below runs until the user is authenticated
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 8. RAG ENGINE INITIALIZATION
# Only runs after the user has successfully authenticated.
# ─────────────────────────────────────────────────────────────────────────────
if "chat_engine" not in st.session_state:
    try:
        from rag_engine import ImmigraSmartChat
        with st.spinner("⏳ Connecting to the legal knowledge base..."):
            st.session_state.chat_engine = ImmigraSmartChat(
                session_id=st.session_state.session_id
            )
    except Exception as e:
        st.error(f"🚨 Initialization error: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 9. MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.caption("🇨🇿 CZECH REPUBLIC · OFFICIAL IMMIGRATION GUIDANCE")
st.title("ImmigraSmart AI")
st.markdown(
    "Your AI-powered guide for navigating visas, residence permits, "
    "and integration in the Czech Republic."
)

st.warning(
    "⚠️ **Important notice:** This assistant provides general guidance based on "
    "public documents — not legal advice. Always verify with "
    "[OAMP](https://frs.gov.cz) before acting."
)

# ─────────────────────────────────────────────────────────────────────────────
# 10. EMPTY STATE & QUICK SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.chat_engine.chat_history:
    st.info(
        "🏛️ **How can I help you today?**\n"
        "Ask about visas, residence permits, health insurance, or financial requirements."
    )

    st.write("### 💡 Quick Questions")
    cols = st.columns(2)
    for i, text in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(text, use_container_width=True):
                # Strip the leading emoji + space before sending
                st.session_state.pending_input = text.split(" ", 1)[1]
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 11. CHAT HISTORY DISPLAY
# Reads from the engine's history (synced with Supabase).
# ─────────────────────────────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.chat_engine.chat_history):

    # Map LangChain roles (human/ai) to Streamlit roles (user/assistant)
    role   = "user" if msg.type == "human" else "assistant"
    avatar = "🧑‍💼" if role == "user" else "🏛️"

    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.content)

        # Metadata badges for user messages
        if role == "user" and hasattr(msg, "additional_kwargs"):
            meta     = msg.additional_kwargs.get("meta", {})
            meta_html = ""
            if meta.get("language") and meta["language"] != "en":
                meta_html += f'<span class="badge-lang">🌐 {meta["language"].upper()}</span> '
            if meta.get("pii_detected"):
                meta_html += '<span class="badge-pii">🔒 PII Protected</span>'
            if meta_html:
                st.markdown(meta_html, unsafe_allow_html=True)

        # Feedback thumbs for assistant messages
        if role == "assistant":
            feedback = st.feedback(
                "thumbs", key=f"fb_{st.session_state.session_id}_{i}"
            )
            if feedback is not None:
                st.toast("Thanks! Your feedback helps improve ImmigraSmart.", icon="✅")

# ─────────────────────────────────────────────────────────────────────────────
# 12. CHAT INPUT
# ─────────────────────────────────────────────────────────────────────────────
user_query = st.chat_input("Ask your question about visas, permits, or insurance...")

# Handle suggestion button clicks
if st.session_state.pending_input:
    user_query = st.session_state.pending_input
    st.session_state.pending_input = None

if user_query:
    # Show the user's message immediately
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_query)

    # Generate and display the assistant's response
    with st.chat_message("assistant", avatar="🏛️"):
        with st.spinner("Consulting official Czech immigration guides..."):
            try:
                answer, meta = st.session_state.chat_engine.ask(
                    user_query,
                    user_document=st.session_state.uploaded_doc_text
                )

                st.markdown(answer)

                # Metadata badges
                meta_html = ""
                lang = meta.get("language", "en")
                if lang != "en":
                    meta_html += f'<span class="badge-lang">🌐 {lang.upper()}</span> '
                if meta.get("pii_detected"):
                    meta_html += '<span class="badge-pii">🔒 PII Protected</span>'
                if meta_html:
                    st.markdown(meta_html, unsafe_allow_html=True)

            except Exception as e:
                st.error("⚠️ **System Error:** Could not process your request.")
                with st.expander("Error details"):
                    st.code(str(e))

    # Rerun outside the chat_message block so the history re-renders cleanly
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 13. AUTO-SCROLL
# Must be at the TOP LEVEL of the file — NOT inside any if/with/except block.
# Waits 500 ms for Streamlit to finish rendering before scrolling down.
# ─────────────────────────────────────────────────────────────────────────────
components.html(
    """
    <script>
        const scrollToBottom = () => {
            const containers = window.parent.document.querySelectorAll(
                '.main, [data-testid="stMain"], [data-testid="stAppViewContainer"]'
            );
            containers.forEach(container => {
                container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
            });
        };
        setTimeout(scrollToBottom, 500);
    </script>
    """,
    height=0,
)