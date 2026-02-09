import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

# Cambiamos el nombre a main para que app.py lo encuentre fácil
def main():
    print("📂 Cargando base de conocimientos desde data/...")
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Carpeta 'data' creada. Coloca tus archivos ahí.")
        return

    # Cargamos archivos .txt y .pdf
    txt_loader = DirectoryLoader('data/', glob="./*.txt", loader_cls=TextLoader)
    pdf_loader = DirectoryLoader('data/', glob="./*.pdf", loader_cls=PyPDFLoader)
    
    raw_documents = txt_loader.load() + pdf_loader.load()
    
    if len(raw_documents) == 0:
        print("❌ No se encontraron documentos.")
        return

    print(f"   └── Fuentes encontradas: {len(raw_documents)}")

    # 2. División de texto
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(raw_documents)

    # 3. Embeddings
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=api_key
    )
    
    # 4. Guardar en base de datos vectorial
    print("🧠 Generando vectores y guardando en ChromaDB...")
    
    # Limpieza de seguridad para evitar el error de "_type"
    if os.path.exists("vector_db"):
        shutil.rmtree("vector_db")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="vector_db"
    )
    print("✅ ¡Ingesta completada!")

if __name__ == "__main__":
    main()