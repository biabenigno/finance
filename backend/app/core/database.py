from supabase import create_client, Client
from app.core.config import settings

# Instancia o cliente do Supabase para exportação global
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)