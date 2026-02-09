import os
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def main():
    # Usamos /tmp para evitar conflictos de permisos y versiones en la nube
    persist_dir = "/tmp/vector_db"
    
    print("📂 Iniciando proceso de ingesta en /tmp/vector_db...")
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Carpeta 'data' creada. Asegúrate de tener archivos ahí.")
        return

    # Carga de archivos
    txt_loader = DirectoryLoader('data/', glob="./*.txt", loader_cls=TextLoader)
    pdf_loader = DirectoryLoader('data/', glob="./*.pdf", loader_cls=PyPDFLoader)
    raw_documents = txt_loader.load() + pdf_loader.load()
    
    if not raw_documents:
        print("❌ Error: No se encontraron documentos en la carpeta 'data/'.")
        return

    # Fragmentación
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(raw_documents)

    # Configuración de Embeddings
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=api_key
    )
    
    # Limpieza absoluta para matar el error _type
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    # Creación de la base de datos vectorial
    print(f"🧠 Generando vectores para {len(chunks)} fragmentos...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    print("✅ Ingesta completada con éxito en el servidor.")

if __name__ == "__main__":
    main()