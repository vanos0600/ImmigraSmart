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
    persist_dir = "/tmp/vector_db"
    print("📂 Iniciando proceso de ingesta robusta...")
    
    if not os.path.exists("data"):
        os.makedirs("data")
        return

    txt_loader = DirectoryLoader('data/', glob="./*.txt", loader_cls=TextLoader)
    pdf_loader = DirectoryLoader('data/', glob="./*.pdf", loader_cls=PyPDFLoader)
    raw_documents = txt_loader.load() + pdf_loader.load()
    
    if not raw_documents:
        print("❌ No hay documentos.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=50)
    chunks = text_splitter.split_documents(raw_documents)

    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=api_key
    )
    
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    # Ingesta por bloques para evitar el Error 504
    print(f"🧠 Generando vectores para {len(chunks)} fragmentos en bloques...")
    
    # Creamos la base de datos con el primer bloque
    vector_db = Chroma.from_documents(
        documents=chunks[:10],
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    # Añadimos el resto con pausas
    for i in range(10, len(chunks), 10):
        batch = chunks[i:i+10]
        vector_db.add_documents(batch)
        print(f"   --- Procesados {i+len(batch)} de {len(chunks)}...")
        time.sleep(1) # Pausa de seguridad

    print("✅ Ingesta completada con éxito.")

if __name__ == "__main__":
    main()