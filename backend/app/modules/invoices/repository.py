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
        """Busca as transações vinculadas a uma fatura ou em aberto"""
        query = supabase.table("transactions") \
            .select("*, cards!inner(name, items!inner(bank_name, user_id)), categories(description, color)") \
            .eq("cards.items.user_id", user_id)
        if card_id:
            query = query.eq("card_id", card_id)
        if bill_id:
            query = query.eq("bill_id", bill_id)
        else:
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

    @staticmethod
    def listar_cartoes() -> List[dict]:
        """Listagem de todos os cartões cadastrados e seus detalhes"""
        res = supabase.table("cards").select("*, items(*)").order("bank_name").execute()
        return res.data or []

    @staticmethod
    def atualizar_nome_cartao(card_id: str, new_name: str) -> Optional[dict]:
        """Atualiza o nome de exibição do cartão"""
        res = supabase.table("cards") \
            .update({"bank_name": new_name}) \
            .eq("id", card_id) \
            .execute()
        return res.data[0] if res.data else None