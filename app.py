import streamlit as st
import os

# Configuración de página DEBE ser lo primero
st.set_page_config(page_title="Immigrasmart AI", page_icon="🇨🇿")

from src.rag_engine import get_rag_chain

st.title("🇨🇿 Immigrasmart AI")
st.markdown("### Your Expert Visa Consultant (Powered by Gemini 2.0)")

DB_PATH = "/tmp/vector_db"

# 1. AUTO-INGESTA
if not os.path.exists(DB_PATH):
    with st.spinner("Initializing Knowledge Base (this takes 1-2 mins)..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
            st.success("Knowledge base ready!")
        except Exception as e:
            st.error(f"Initialization failed: {e}")
            st.info("Try refreshing the page or check your Google API Key.")
            st.stop()

# 2. CARGAR MOTOR
if "rag_chain" not in st.session_state:
    try:
        st.session_state.rag_chain = get_rag_chain()
    except Exception as e:
        st.error(f"AI Engine Error: {e}")
        st.stop()

# 3. CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about Czech visas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = st.session_state.rag_chain.invoke(prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error: {e}")