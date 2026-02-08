import streamlit as st
import os
from src.rag_engine import get_rag_chain

# Configuración de la página
st.set_page_config(page_title="Immigrasmart AI", page_icon="🇨🇿")

st.title("🇨🇿 Immigrasmart AI")
st.markdown("### Tu consultor experto en visados para República Checa")

# Verificación de que la base de datos existe
if not os.path.exists("vector_db"):
    st.warning("⚠️ Base de datos no encontrada. Por favor, corre 'python src/ingest.py' primero.")
    st.stop()

# Inicializar el motor RAG en la sesión de Streamlit para que sea persistente
if "rag_chain" not in st.session_state:
    with st.spinner("Cargando motor de inteligencia..."):
        st.session_state.rag_chain = get_rag_chain()

# Inicializar el historial de mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial del chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada del usuario (Chat Input)
if prompt := st.chat_input("Pregunta sobre requisitos de residencia, plazos o documentos..."):
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta del asistente
    import streamlit as st
import os
from src.rag_engine import get_rag_chain

# 1. Page Configuration
st.set_page_config(page_title="Immigrasmart AI", page_icon="🇨🇿")

st.title("🇨🇿 Immigrasmart AI")
st.markdown("### Your Expert Visa Consultant for the Czech Republic")

# 2. Safety Check: Ensure Vector DB exists
if not os.path.exists("vector_db"):
    st.warning("⚠️ Knowledge base not found. Please run 'python src/ingest.py' first.")
    st.stop()

# 3. Initialize the RAG Chain in Session State
# This prevents the app from reloading the model on every click
if "rag_chain" not in st.session_state:
    with st.spinner("Initializing AI Engine..."):
        st.session_state.rag_chain = get_rag_chain()

# 4. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. User Input Logic
if prompt := st.chat_input("Ask about visa requirements, deadlines, or documents..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 7. Assistant Response Logic (LCEL Version)
    with st.chat_message("assistant"):
        with st.spinner("Consulting official Czech immigration data..."):
            try:
                # In LCEL, .invoke() returns the string answer directly
                # because we added the StrOutputParser() in rag_engine.py
                answer = st.session_state.rag_chain.invoke(prompt)
                
                # Display the answer
                st.markdown(answer)
                
                # Add assistant message to history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.info("Technical Tip: Ensure your GOOGLE_API_KEY is correct in the .env file.")