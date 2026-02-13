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
    persist_dir = "/tmp/vector_db"
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )

    vector_db = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

    # Modelo Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0, 
        google_api_key=api_key
    )

    template = """
    You are 'Immigrasmart', a professional AI Visa Consultant for the Czech Republic.
    Use ONLY the provided context to answer. If the answer is not there, say you don't know.

    CONTEXT:
    {context}

    QUESTION: 
    {input}

    ANSWER:
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    retriever = vector_db.as_retriever(search_kwargs={"k": 10})

    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain