import streamlit as st
import os
from src.rag_engine import get_rag_chain

st.set_page_config(page_title="Immigrasmart AI", page_icon="🇨🇿")

st.title("🇨🇿 Immigrasmart AI")
st.markdown("### Your Expert Visa Consultant (Powered by Gemini 2.0)")

# Ruta temporal en el servidor
DB_PATH = "/tmp/vector_db"

# PASO CRÍTICO: Auto-ingesta si la base de datos no está en /tmp
if not os.path.exists(DB_PATH):
    with st.spinner("🚀 System cold start: Initializing Czech Knowledge Base..."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
            st.success("System ready!")
        except Exception as e:
            st.error(f"Initialization failed: {e}")
            st.stop()

# Cargar motor
if "rag_chain" not in st.session_state:
    try:
        st.session_state.rag_chain = get_rag_chain()
    except Exception as e:
        st.error(f"Error starting AI engine: {e}")
        st.stop()

# Historial
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask about residence permits, deadlines..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing official documents..."):
            try:
                answer = st.session_state.rag_chain.invoke(prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Connection error: {e}")