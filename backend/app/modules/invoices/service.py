from typing import List, Optional
from app.modules.invoices.repository import InvoiceRepository
from app.modules.invoices.schemas import (
    BillResponse,
    CategoryResponse,
    ToggleIgnoreResponse,
    TransactionResponse,
    CategorySummaryResponse,
    CategorySummaryItem,
    CardResponse  # <-- Importação adicionada
)

class InvoiceService:
    def __init__(self):
        self.repository = InvoiceRepository()

    def obter_faturas(self, user_id: str, card_id: Optional[str] = None) -> List[BillResponse]:
        faturas_raw = self.repository.listar_faturas_usuario(user_id, card_id)
        resultado = []
        for f in faturas_raw:
            card_info = f.get("cards") or {}
            item_info = card_info.get("items") or {}
            resultado.append(
                BillResponse(
                    id=f["id"],
                    card_id=f["card_id"],
                    card_name=card_info.get("name", "Cartão"),
                    bank_name=item_info.get("bank_name", "Banco"),
                    due_date=f["due_date"],
                    total_amount=float(f["total_amount"])
                )
            )
        return resultado

    def obter_categorias(self) -> List[CategoryResponse]:
        cats_raw = self.repository.listar_categorias()
        return [
            CategoryResponse(
                id=c["id"],
                description=c["description"],
                description_translated=c.get("description_translated"),
                color=c.get("color") or "#94a3b8",
                parent_id=c.get("parent_id")
            )
            for c in cats_raw
        ]

    def obter_transacoes(
        self, 
        user_id: str, 
        bill_id: Optional[str] = None, 
        card_id: Optional[str] = None
    ) -> List[TransactionResponse]:
        txs_raw = self.repository.listar_transacoes(user_id, bill_id, card_id)
        resultado = []
        for tx in txs_raw:
            cat_data = tx.get("categories") or {}
            card_data = tx.get("cards") or {}
            item_data = card_data.get("items") or {}
            resultado.append(
                TransactionResponse(
                    id=tx["id"],
                    description=tx["description"],
                    amount=float(tx["amount"]),
                    date=tx["date"],
                    status=tx["status"],
                    card_id=tx["card_id"],
                    bank_name=item_data.get("bank_name", "Cartão"),
                    bill_id=tx.get("bill_id"),
                    category_id=tx.get("category_id"),
                    category_name=cat_data.get("description") or "Outros",
                    category_color=cat_data.get("color") or "#94a3b8",
                    is_ignored=tx.get("is_ignored", False)
                )
            )
        return resultado

    def obter_resumo_categorias_fatura(
        self, 
        user_id: str, 
        bill_id: Optional[str] = None, 
        card_id: Optional[str] = None
    ) -> CategorySummaryResponse:
        transacoes_brutas = self.obter_transacoes(user_id, bill_id, card_id)
        
        transacoes = [
            tx for tx in transacoes_brutas 
            if tx.category_id != "05100000" and not tx.is_ignored
        ]
        
        total_fatura = sum(tx.amount for tx in transacoes)
        total_despesas_brutas = sum(tx.amount for tx in transacoes if tx.amount > 0)

        agrupado = {}
        for tx in transacoes:
            cat_id = tx.category_id if tx.category_id else "outros"
            cat_nome = tx.category_name if tx.category_id else "Outros"
            cat_cor = tx.category_color if tx.category_id else "#94a3b8"

            if cat_id not in agrupado:
                agrupado[cat_id] = {
                    "id": cat_id,
                    "nome": cat_nome,
                    "cor": cat_cor,
                    "total": 0.0,
                    "transacoes": []
                }
            agrupado[cat_id]["total"] += tx.amount
            agrupado[cat_id]["transacoes"].append(tx)

        lista_categorias = []
        for item in agrupado.values():
            pct = (item["total"] / total_despesas_brutas * 100) if total_despesas_brutas > 0 else 0.0
            lista_categorias.append(
                CategorySummaryItem(
                    category_id=item["id"],
                    category_name=item["nome"],
                    category_color=item["cor"],
                    total_amount=round(item["total"], 2),
                    percentage=round(pct, 2),
                    transactions=item["transacoes"]
                )
            )

        lista_categorias.sort(key=lambda x: x.total_amount, reverse=True)

        return CategorySummaryResponse(
            bill_id=bill_id,
            is_pending=(bill_id is None),
            total_bill=round(total_fatura, 2),
            categories=lista_categorias
        )

    def alternar_ignorada(self, transaction_id: str, is_ignored: bool) -> ToggleIgnoreResponse:
        tx_atualizada = self.repository.alternar_ignorada(transaction_id, is_ignored)
        if not tx_atualizada:
            raise ValueError("Transação não encontrada")
        
        status_msg = "desconsiderada das análises" if is_ignored else "reincluída nas análises"
        return ToggleIgnoreResponse(
            id=transaction_id,
            is_ignored=is_ignored,
            message=f"Transação {status_msg} com sucesso."
        )

    def obter_cartoes(self) -> List[CardResponse]:
        raw_cards = self.repository.listar_cartoes()
        return [
            CardResponse(
                id=c["id"],
                bank_name=c.get("bank_name") or "Cartão sem nome",
                pluggy_account_id=c.get("pluggy_account_id"),
                item_id=c.get("item_id"),
                created_at=c.get("created_at")
            )
            for c in raw_cards
        ]

    def renomear_cartao(self, card_id: str, novo_nome: str) -> CardResponse:
        card_atualizado = self.repository.atualizar_nome_cartao(card_id, novo_nome)
        if not card_atualizado:
            raise ValueError("Cartão não encontrado.")
        return CardResponse(
            id=card_atualizado["id"],
            bank_name=card_atualizado["bank_name"],
            pluggy_account_id=card_atualizado.get("pluggy_account_id"),
            item_id=card_atualizado.get("item_id"),
            created_at=card_atualizado.get("created_at")
        )