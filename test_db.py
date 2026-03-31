import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar las variables de tu archivo .env
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

try:
    # Intentar conectar
    supabase: Client = create_client(url, key)
    
    # Intentar leer la tabla que acabamos de crear
    respuesta = supabase.table("chat_history").select("*").execute()
    
    print("✅ ¡ÉXITO TOTAL! Conexión a Supabase establecida.")
    print(f"Datos en la tabla (debe estar vacía por ahora): {respuesta.data}")
    
except Exception as e:
    print("❌ Oh no, algo falló al conectar:")
    print(e)