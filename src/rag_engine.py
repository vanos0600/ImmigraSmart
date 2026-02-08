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

    # 2. Load Vector DB
    vector_db = Chroma(
        persist_directory="vector_db/",
        embedding_function=embeddings
    )

    # 3. Setup LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )

    # 4. Prompt
    template = """
    You are 'Immigrasmart', an expert AI Visa Consultant for the Czech Republic.
    Use the following pieces of retrieved context to answer the user's question.
    If the answer is not in the context, say you don't know based on official documents.

    CONTEXT:
    {context}

    QUESTION: 
    {input}

    ANSWER:
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    # 5. Build the Chain using LCEL (Bypassing langchain.chains)
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # This is the modern chain structure
    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain