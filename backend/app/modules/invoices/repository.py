from datetime import date, datetime
from typing import List, Optional
from app.core.database import supabase

class InvoiceRepository:
    @staticmethod
    def obter_card_ids_do_usuario(user_id: str) -> List[str]:
        """Retorna todos os UUIDs de cartões vinculados ao usuário."""
        res_items = supabase.table("items").select("id").eq("user_id", user_id).execute()
        item_ids = [item["id"] for item in (res_items.data or [])]
        if not item_ids:
            return []
        
        res_cards = supabase.table("cards").select("id").in_("item_id", item_ids).execute()
        return [card["id"] for card in (res_cards.data or [])]

    @staticmethod
    def listar_faturas_usuario(user_id: str, card_id: Optional[str] = None) -> List[dict]:
        """Busca faturas do usuário ou de um cartão específico[cite: 7, 9, 10]."""
        user_card_ids = InvoiceRepository.obter_card_ids_do_usuario(user_id)
        if not user_card_ids:
            return []

        target_ids = [card_id] if card_id and card_id in user_card_ids else user_card_ids

        res = supabase.table("bills") \
            .select("*, cards(*, items(*))") \
            .in_("card_id", target_ids) \
            .order("due_date", desc=True) \
            .execute()
        return res.data or []

    @staticmethod
    def listar_categorias() -> List[dict]:
        res = supabase.table("categories").select("*").order("description").execute()
        return res.data or []

    @staticmethod
    def listar_transacoes(user_id: str, fatura: Optional[str] = None, card_id: Optional[str] = None) -> List[dict]:
        user_card_ids = InvoiceRepository.obter_card_ids_do_usuario(user_id)
        if not user_card_ids:
            return []

        target_ids = [card_id] if card_id and card_id in user_card_ids else user_card_ids

        # 1. Lançamentos em Aberto (Sem fatura atribuída)
        if not fatura or fatura == "atual":
            res = supabase.table("transactions") \
                .select("*, cards(*, items(*)), categories(*)") \
                .in_("card_id", target_ids) \
                .is_("bill_id", "null") \
                .order("date", desc=True) \
                .execute()
            return res.data or []

        # 2. Busca faturas pelo ID ou pelo mês de vencimento.
        bills_query = supabase.table("bills") \
            .select("id") \
            .in_("card_id", target_ids)

        try:
            mes_inicio = datetime.strptime(fatura, "%Y-%m").date()
            mes_fim = date(
                mes_inicio.year + (mes_inicio.month == 12),
                1 if mes_inicio.month == 12 else mes_inicio.month + 1,
                1,
            )
            bills_query = bills_query.gte("due_date", mes_inicio.isoformat()) \
                .lt("due_date", mes_fim.isoformat())
        except ValueError:
            bills_query = bills_query.eq("id", fatura)

        bills_res = bills_query.execute()

        bill_ids = [b["id"] for b in (bills_res.data or [])]
        if not bill_ids:
            return []

        # 3. Retorna apenas transações com os bill_ids encontrados[cite: 7]
        res = supabase.table("transactions") \
            .select("*, cards(*, items(*)), categories(*)") \
            .in_("card_id", target_ids) \
            .in_("bill_id", bill_ids) \
            .order("date", desc=True) \
            .execute()
        return res.data or []

    @staticmethod
    def alternar_ignorada(transaction_id: str, is_ignored: bool) -> Optional[dict]:
        res = supabase.table("transactions") \
            .update({"is_ignored": is_ignored}) \
            .eq("id", transaction_id) \
            .execute()
        return res.data[0] if res.data else None

    @staticmethod
    def listar_cartoes() -> List[dict]:
        res = supabase.table("cards").select("*, items(*)").order("name").execute()
        return res.data or []

    @staticmethod
    def atualizar_cartao(card_id: str, card_name: Optional[str] = None, bank_name: Optional[str] = None) -> Optional[dict]:
        card_res = supabase.table("cards").select("*, items(*)").eq("id", card_id).execute()
        if not card_res.data:
            return None
        card_atual = card_res.data[0]
        
        if card_name:
            supabase.table("cards").update({"name": card_name}).eq("id", card_id).execute()
        
        item_id = card_atual.get("item_id")
        if bank_name and item_id:
            supabase.table("items").update({"bank_name": bank_name}).eq("id", item_id).execute()

        res_final = supabase.table("cards").select("*, items(*)").eq("id", card_id).execute()
        return res_final.data[0] if res_final.data else None

    @staticmethod
    def criar_cartao(card_name: str, bank_name: str, user_id: str, pluggy_account_id: Optional[str] = None, pluggy_item_id: Optional[str] = None) -> dict:
        pluggy_item = pluggy_item_id or f"manual_{bank_name.lower().replace(' ', '_')}"
        item_res = supabase.table("items").upsert({
            "user_id": user_id,
            "bank_name": bank_name,
            "pluggy_item_id": pluggy_item,
            "status": "UPDATED"
        }, on_conflict="pluggy_item_id").execute()
        item_id = item_res.data[0]["id"]

        card_payload = {
            "item_id": item_id,
            "name": card_name,
            "pluggy_account_id": pluggy_account_id
        }

        if pluggy_account_id:
            card_res = supabase.table("cards").upsert(card_payload, on_conflict="pluggy_account_id").execute()
        else:
            card_res = supabase.table("cards").insert(card_payload).execute()
        
        card_novo = card_res.data[0]
        card_novo["items"] = item_res.data[0]
        return card_novo