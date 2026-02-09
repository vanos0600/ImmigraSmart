import streamlit as st
import os
from src.rag_engine import get_rag_chain

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Immigrasmart AI", page_icon="🇨🇿")

st.title("🇨🇿 Immigrasmart AI")
st.markdown("### Your Expert Visa Consultant for the Czech Republic")

# --- 2. AUTO-INGEST (SOLUCIÓN PARA LA NUBE) ---
# Si la carpeta vector_db no existe, la creamos automáticamente
if not os.path.exists("vector_db"):
    with st.spinner("Initializing knowledge base for the first time... This may take a minute."):
        try:
            from src.ingest import main as run_ingest
            run_ingest()
            st.success("Knowledge base initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize knowledge base: {e}")
            st.stop()

# --- 3. INICIALIZAR EL MOTOR RAG ---
if "rag_chain" not in st.session_state:
    with st.spinner("Connecting to Gemini AI Engine..."):
        try:
            st.session_state.rag_chain = get_rag_chain()
        except Exception as e:
            st.error(f"Error starting AI Engine: {e}")
            st.stop()

# --- 4. HISTORIAL DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. LÓGICA DE PREGUNTAS ---
if prompt := st.chat_input("Ask about visa requirements, deadlines, or documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consulting official Czech immigration data..."):
            try:
                # Invocamos la cadena (LCEL)
                answer = st.session_state.rag_chain.invoke(prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.info("Check your GOOGLE_API_KEY in Streamlit Secrets.")