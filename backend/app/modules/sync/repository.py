from typing import List, Dict
from app.core.database import supabase

class SyncRepository:
    @staticmethod
    def obter_cartoes_conectados() -> List[dict]:
        res = supabase.table("cards").select("*, items(*)").order("name").execute()
        return res.data or []

    @staticmethod
    def obter_transacoes_existentes_dict() -> Dict[str, dict]:
        """Retorna um dicionário id -> dados atuais com paginação para superar o limite do Supabase."""
        todos = {}
        offset = 0
        limit = 1000
        
        while True:
            res = supabase.table("transactions").select(
                "id, bill_id, category_id, description, amount, status, installment_number, total_installments"
            ).range(offset, offset + limit - 1).execute()
            
            data = res.data or []
            if not data:
                break
                
            for t in data:
                todos[str(t["id"])] = t
                
            if len(data) < limit:
                break
                
            offset += limit
            
        return todos

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