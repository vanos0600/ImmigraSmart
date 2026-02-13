import os
import shutil
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def main():
    # Usamos /tmp para Linux/Streamlit Cloud
    persist_dir = "/tmp/vector_db"
    print("Starting injection...")
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Repositroy created 'data'. Add your files.")
        return

    # Carga de documentos
    txt_loader = DirectoryLoader('data/', glob="./*.txt", loader_cls=TextLoader)
    pdf_loader = DirectoryLoader('data/', glob="./*.pdf", loader_cls=PyPDFLoader)
    raw_documents = txt_loader.load() + pdf_loader.load()
    
    if not raw_documents:
        print("Not cuments found in 'data/'.")
        return

    # Fragmentación más pequeña (500) para procesar rápido
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = text_splitter.split_documents(raw_documents)

    api_key = os.getenv("GOOGLE_API_KEY")
    
    # Configuración de Embeddings con alta tolerancia al tiempo (Timeout)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=api_key,
        task_type="retrieval_document"
    )
    
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    print(f"Generating vector {len(chunks)} ...")
    
    # Ingesta por bloques de 5 con pausas de 2 segundos para evitar Error 504
    vector_db = Chroma.from_documents(
        documents=chunks[:5],
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    for i in range(5, len(chunks), 5):
        batch = chunks[i:i+5]
        vector_db.add_documents(batch)
        print(f"   --- Processed {i+len(batch)} de {len(chunks)}...")
        time.sleep(2) # Pausa de seguridad para la API de Google

    print("Ingest completed successfully /tmp/vector_db.")

if __name__ == "__main__":
    main()