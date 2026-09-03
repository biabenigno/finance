from typing import List
from app.core.database import supabase

class SyncRepository:
    @staticmethod
    def obter_cartoes_conectados() -> List[dict]:
        """Busca cartões vinculados a contas ativas no banco."""
        res = supabase.table("cards").select("*, items(*)").order("name").execute()
        return res.data or []

    @staticmethod
    def obter_ids_transacoes_existentes() -> set:
        """Retorna o conjunto de IDs de transações já cadastradas no banco."""
        res = supabase.table("transactions").select("id").execute()
        return {t["id"] for t in (res.data or [])}

    @staticmethod
    def salvar_faturas_em_lote(bills: List[dict]):
        if bills:
            supabase.table("bills").upsert(bills).execute()

    @staticmethod
    def salvar_transacoes_em_lote(transactions: List[dict]):
        if transactions:
            batch_size = 100
            for i in range(0, len(transactions), batch_size):
                supabase.table("transactions").upsert(transactions[i:i + batch_size]).execute()