from typing import List, Optional
from app.core.database import supabase

class InvoiceRepository:

    @staticmethod
    def listar_faturas_usuario(user_id: str, card_id: Optional[str] = None) -> List[dict]:
        """Busca faturas salvas no banco vinculadas aos cartões do usuário"""
        query = supabase.table("bills") \
            .select("*, cards!inner(name, id, items!inner(bank_name, user_id))") \
            .eq("cards.items.user_id", user_id)

        if card_id:
            query = query.eq("card_id", card_id)

        res = query.order("due_date", desc=True).execute()
        return res.data or []

    @staticmethod
    def listar_categorias() -> List[dict]:
        """Busca todas as categorias cadastradas na tabela mestre"""
        res = supabase.table("categories").select("*").order("description").execute()
        return res.data or []

    @staticmethod
    def listar_transacoes(
        user_id: str, 
        bill_id: Optional[str] = None, 
        card_id: Optional[str] = None
    ) -> List[dict]:
        """
        Se bill_id for fornecido, busca as transações daquela fatura.
        Se bill_id for None, busca as transações PENDENTES/ABERTAS (bill_id IS NULL).
        """
        query = supabase.table("transactions") \
            .select("*, cards!inner(name, items!inner(bank_name, user_id)), categories(description, color)") \
            .eq("cards.items.user_id", user_id)

        if card_id:
            query = query.eq("card_id", card_id)

        if bill_id:
            query = query.eq("bill_id", bill_id)
        else:
            # Sem bill_id -> Busca Fatura Aberta / Compras Pendentes
            query = query.is_("bill_id", "null")

        res = query.order("date", desc=True).execute()
        return res.data or []
    
    @staticmethod
    def alternar_ignorada(transaction_id: str, is_ignored: bool) -> Optional[dict]:
        """Atualiza o campo is_ignored de uma transação específica"""
        res = supabase.table("transactions") \
            .update({"is_ignored": is_ignored}) \
            .eq("id", transaction_id) \
            .execute()
        return res.data[0] if res.data else None