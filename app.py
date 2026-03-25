"""
app.py — ImmigraSmart Streamlit Application  (v3)
What's new vs v2:
  - Displays a gentle PII notice when personal data was scrubbed
  - Shows detected language badge next to user messages
  - Passes (answer, meta) from ImmigraSmartChat.ask()
  - All v2 features retained: feedback buttons, suggestions, sidebar, disclaimer
"""

import os
import streamlit as st

# ── Page config MUST be first ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ImmigraSmart AI",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded",
)

DB_PATH = "/tmp/vector_db"

LANG_FLAGS = {
    "cs": "🇨🇿", "sk": "🇸🇰", "es": "🇪🇸", "ar": "🇸🇦",
    "uk": "🇺🇦", "ru": "🇷🇺", "vi": "🇻🇳", "zh": "🇨🇳",
    "de": "🇩🇪", "fr": "🇫🇷", "en": "🇬🇧",
}

# ── Knowledge Base Init ────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    with st.spinner("⚙️ Initialising knowledge base (1–2 min on first run)..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
            st.success("✅ Knowledge base ready!")
        except Exception as e:
            st.error(f"Initialisation failed: {e}")
            st.info("Refresh the page or check your GOOGLE_API_KEY.")
            st.stop()

# ── Load Chat Engine ───────────────────────────────────────────────────────────
if "chat" not in st.session_state:
    try:
        from src.rag_engine import ImmigraSmartChat
        st.session_state.chat = ImmigraSmartChat()
    except Exception as e:
        st.error(f"Failed to start AI engine: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []   # list of {role, content, meta}

if "feedback" not in st.session_state:
    st.session_state.feedback = {}   # {msg_index: "up"|"down"}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🇨🇿 ImmigraSmart AI")
    st.caption("Czech Republic Immigration Assistant")
    st.divider()

    st.markdown("**🔗 Official Resources**")
    st.markdown("- [OAMP Appointments](https://frs.gov.cz)")
    st.markdown("- [Info Portal for Foreigners](https://ipc.gov.cz)")
    st.markdown("- [PVZP Insurance](https://pvzp.cz)")
    st.markdown("- [Free Legal Aid — SIMI](https://migrace.com)")
    st.markdown("- [Free Legal Aid — OPU](https://opu.cz)")
    st.divider()

    st.markdown("**📞 Emergency Contact**")
    st.markdown("OAMP Info Line: **+420 974 801 801**")
    st.divider()

    st.caption("Knowledge Base: Ver. 2026.2")
    st.caption("Last Updated: January 2026")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.session_state.chat.reset()
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🇨🇿 ImmigraSmart AI")
st.markdown("#### Your Czech Republic Immigration Assistant")

st.warning(
    "⚠️ **Disclaimer:** This tool provides general information only, not legal advice. "
    "Always verify with the official [OAMP office](https://frs.gov.cz) "
    "or a qualified immigration lawyer.",
    icon="⚖️",
)

# ── Quick-start suggestions (shown only on empty state) ───────────────────────
if not st.session_state.messages:
    st.markdown("**💬 Try asking:**")
    suggestions = [
        "How much money do I need for a 12-month stay?",
        "What should I do within 3 days of arriving?",
        "When should I apply to extend my residence permit?",
        "What is a Bridge Label and when do I need one?",
        "Can I work while studying on a student permit?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"sug_{i}", use_container_width=True):
            st.session_state.pending_input = s
            st.rerun()

# ── Chat History Display ───────────────────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):

        # Language badge on user messages
        if msg["role"] == "user":
            meta = msg.get("meta", {})
            lang = meta.get("language", "en")
            flag = LANG_FLAGS.get(lang, "🌐")
            if lang != "en":
                st.caption(f"{flag} Message detected in `{lang}`")

        st.markdown(msg["content"])

        # PII notice on user messages
        if msg["role"] == "user":
            meta = msg.get("meta", {})
            if meta.get("pii_detected"):
                entities = ", ".join(meta.get("pii_entities", []))
                st.info(
                    f"🔒 **Privacy notice:** I detected personal data "
                    f"({entities}) in your message and removed it before "
                    f"processing — it was never sent to the AI.",
                    icon="🔒",
                )

        # Feedback buttons on assistant messages
        if msg["role"] == "assistant":
            existing = st.session_state.feedback.get(idx)
            if existing:
                st.caption(f"{'👍 Helpful' if existing == 'up' else '👎 Not helpful'} — thank you!")
            else:
                c1, c2, _ = st.columns([1, 1, 8])
                if c1.button("👍", key=f"up_{idx}"):
                    st.session_state.feedback[idx] = "up"
                    st.rerun()
                if c2.button("👎", key=f"down_{idx}"):
                    st.session_state.feedback[idx] = "down"
                    st.rerun()

# ── Handle Pre-filled Input (suggestion buttons) ──────────────────────────────
pending = st.session_state.pop("pending_input", None)

# ── Chat Input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about Czech visas, permits, deadlines...") or pending

if user_input:
    # ── Show user message immediately ─────────────────────────────────────────
    with st.chat_message("user"):
        st.markdown(user_input)

    # ── Generate response ──────────────────────────────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                answer, meta = st.session_state.chat.ask(user_input)

                # Store user message WITH meta (for PII/lang badge on re-render)
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input,
                    "meta": meta,
                })

                st.markdown(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "meta": meta,
                })

            except Exception as e:
                err = (
                    "Sorry, something went wrong. Please try again.\n\n"
                    "If this persists, contact OAMP at **+420 974 801 801**."
                )
                st.error(err)
                st.caption(f"Technical detail: {e}")
                st.session_state.messages.append({
                    "role": "user", "content": user_input, "meta": {},
                })

    st.rerun()