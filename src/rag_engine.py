import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_rag_chain():
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # 1. Setup Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )

    # 2. Load Vector DB - Ajustado para compatibilidad total
    # Eliminamos el "/" final de la ruta para que coincida con ingest.py
    vector_db = Chroma(
        persist_directory="vector_db", 
        embedding_function=embeddings
    )

    # 3. Setup LLM (Cambiado a 1.5-flash para mayor estabilidad en la nube)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0, 
        google_api_key=api_key
    )

    # 4. Prompt Reforzado
    template = """
    You are 'Immigrasmart', a strict and professional AI Visa Consultant for the Czech Republic.
    Your mission is to provide information based ONLY on the provided legal context.

    STRICT RULES:
    1. If the information is not present in the CONTEXT below, you must say: "I am sorry, but I do not have official information regarding this in my current database."
    2. Do NOT use your general knowledge about other countries.
    3. Always stick to the facts, dates, and fees mentioned in the context.

    CONTEXT:
    {context}

    QUESTION: 
    {input}

    ANSWER:
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    # 5. Build the Chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain