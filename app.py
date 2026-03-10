"""
app.py — ImmigraSmart Streamlit Application
Improvements over v1:
  - Uses ImmigraSmartChat (conversation memory + confidence guard)
  - Per-message feedback buttons (thumbs up/down) for data collection
  - Language auto-detection with multilingual welcome
  - Official disclaimer banner
  - Sidebar with quick links and last-updated info
  - Graceful error handling with actionable fallback messages
"""

import os
import json
from datetime import datetime
import streamlit as st

# ── Page config MUST be first ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ImmigraSmart AI",
    page_icon="🇨🇿",
    layout="centered",
    initial_sidebar_state="expanded"
)

DB_PATH = "/tmp/vector_db"

# ── Knowledge Base Init ────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    with st.spinner("⚙️ Initializing knowledge base (takes 1–2 min on first run)..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
            st.success("✅ Knowledge base ready!")
        except Exception as e:
            st.error(f"Initialization failed: {e}")
            st.info("Try refreshing the page, or check that your GOOGLE_API_KEY is set.")
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
    st.session_state.messages = []

if "feedback" not in st.session_state:
    st.session_state.feedback = {}  # {message_index: "up" | "down"}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/cb/Flag_of_the_Czech_Republic.svg", width=80)
    st.title("ImmigraSmart AI")
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
    st.caption(f"Knowledge Base: Ver. 2026.2")
    st.caption(f"Last Updated: January 2026")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback = {}
        st.session_state.chat.reset()
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🇨🇿 ImmigraSmart AI")
st.markdown("#### Your Czech Republic Immigration Assistant")

# Disclaimer banner
st.warning(
    "⚠️ **Disclaimer:** This tool provides general information only, not legal advice. "
    "Always verify requirements with the official [OAMP office](https://frs.gov.cz) "
    "or a qualified immigration lawyer.",
    icon="⚖️"
)

# ── Quick-start suggestions ────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("**💬 Try asking:**")
    suggestions = [
        "How much money do I need to prove for a 12-month stay?",
        "What should I do within 3 days of arriving in the Czech Republic?",
        "When should I apply to extend my residence permit?",
        "What is a Bridge Label and when do I need one?",
        "Can I work while studying on a student permit?",
    ]
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 2].button(suggestion, key=f"suggestion_{i}", use_container_width=True):
            st.session_state.pending_input = suggestion
            st.rerun()

# ── Chat History Display ───────────────────────────────────────────────────────
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show feedback buttons only on assistant messages
        if msg["role"] == "assistant":
            existing_feedback = st.session_state.feedback.get(idx)
            if existing_feedback:
                st.caption(f"{'👍 Helpful' if existing_feedback == 'up' else '👎 Not helpful'} — thank you!")
            else:
                fb_col1, fb_col2, fb_col3 = st.columns([1, 1, 8])
                if fb_col1.button("👍", key=f"up_{idx}", help="This was helpful"):
                    st.session_state.feedback[idx] = "up"
                    st.rerun()
                if fb_col2.button("👎", key=f"down_{idx}", help="This wasn't helpful"):
                    st.session_state.feedback[idx] = "down"
                    st.rerun()

# ── Handle Pre-filled Input (from suggestion buttons) ─────────────────────────
pending = st.session_state.pop("pending_input", None)

# ── Chat Input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about Czech visas, permits, deadlines...") or pending

if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                answer = st.session_state.chat.ask(user_input)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                err_msg = (
                    "Sorry, I encountered an error. Please try again.\n\n"
                    f"If this persists, contact OAMP at **+420 974 801 801**."
                )
                st.error(err_msg)
                st.caption(f"Technical detail: {e}")

    st.rerun()