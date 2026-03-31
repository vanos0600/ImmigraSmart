import os
from supabase import create_client, Client
from langchain_core.messages import HumanMessage, AIMessage

class ChatDatabase:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    def save_message(self, session_id: str, role: str, content: str):
        """Guarda un mensaje en la nube de Supabase"""
        try:
            self.supabase.table("chat_history").insert({
                "session_id": session_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"Error guardando en DB: {e}")

    def load_history(self, session_id: str):
        """Recupera los mensajes guardados para esta sesión"""
        try:
            response = self.supabase.table("chat_history") \
                .select("role", "content") \
                .eq("session_id", session_id) \
                .order("created_at", desc=True) \
                .limit(20) \
                .execute()
            
            # Los invertimos para que estén en orden cronológico
            raw_msgs = reversed(response.data)
            
            history = []
            for msg in raw_msgs:
                if msg["role"] == "user":
                    history.append(HumanMessage(content=msg["content"]))
                else:
                    history.append(AIMessage(content=msg["content"]))
            return history
        except Exception as e:
            print(f"Error cargando DB: {e}")
            return []