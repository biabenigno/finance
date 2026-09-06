import requests
from typing import List, Optional
from app.core.config import settings
from app.modules.invoices.repository import InvoiceRepository
from app.modules.invoices.schemas import (
    BillResponse,
    CategoryResponse,
    ToggleIgnoreResponse,
    TransactionResponse,
    CategorySummaryResponse,
    CategorySummaryItem,
    CardResponse,
    CardUpdate,
    CardCreate
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
                description=c.get("description_translated") or c["description"],  # Prioriza tradução em PT-BR
                description_translated=c.get("description_translated"),
                color=c.get("color") or "#94a3b8",
                parent_id=c.get("parent_id")
            )
            for c in cats_raw
        ]

    def obter_transacoes(self, user_id: str, fatura: Optional[str] = None, card_id: Optional[str] = None) -> List[TransactionResponse]:
        txs_raw = self.repository.listar_transacoes(user_id, fatura, card_id)
        resultado = []
        for tx in txs_raw:
            cat_data = tx.get("categories") or {}
            card_data = tx.get("cards") or {}
            item_data = card_data.get("items") or {}

            # Prioriza a coluna description_translated, usando description e 'Outros' como fallbacks
            category_name = cat_data.get("description_translated") or cat_data.get("description") or "Outros"

            resultado.append(
                    TransactionResponse(
                    id=tx["id"],
                    description=tx["description"],
                    amount=float(tx["amount"]),
                    date=tx["date"],
                    status=tx["status"],
                    card_id=tx["card_id"],
                    bank_name=item_data.get("bank_name", "Banco"),
                    card_name=card_data.get("name", "Cartão"),
                    bill_id=tx.get("bill_id"),
                    category_id=tx.get("category_id"),
                    category_name=category_name,
                    category_color=cat_data.get("color") or "#94a3b8",
                    is_ignored=tx.get("is_ignored", False),
                    installment_number=tx.get("installment_number"),
                    total_installments=tx.get("total_installments")
                )
            )
        return resultado

    def obter_resumo_categorias_fatura(self, user_id: str, fatura: Optional[str] = None, card_id: Optional[str] = None) -> CategorySummaryResponse:
        transacoes_brutas = self.obter_transacoes(user_id, fatura, card_id)
        transacoes = [tx for tx in transacoes_brutas if tx.category_id != "05100000" and not tx.is_ignored]
        
        total_fatura = sum(tx.amount for tx in transacoes)
        total_despesas_brutas = sum(tx.amount for tx in transacoes if tx.amount > 0)
        agrupado = {}
        for tx in transacoes:
            cat_id = tx.category_id if tx.category_id else "outros"
            cat_nome = tx.category_name if tx.category_id else "Outros"
            cat_cor = tx.category_color if tx.category_id else "#94a3b8"
            if cat_id not in agrupado:
                agrupado[cat_id] = {"id": cat_id, "nome": cat_nome, "cor": cat_cor, "total": 0.0, "transacoes": []}
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
            bill_id=fatura,
            is_pending=(fatura == "atual" or not fatura),
            total_bill=round(total_fatura, 2),
            categories=lista_categorias
        )

    def alternar_ignorada(self, transaction_id: str, is_ignored: bool) -> ToggleIgnoreResponse:
        tx_atualizada = self.repository.alternar_ignorada(transaction_id, is_ignored)
        if not tx_atualizada:
            raise ValueError("Transação não encontrada")
        status_msg = "desconsiderada das análises" if is_ignored else "reincluída nas análises"
        return ToggleIgnoreResponse(id=transaction_id, is_ignored=is_ignored, message=f"Transação {status_msg} com sucesso.")

    def obter_cartoes(self) -> List[CardResponse]:
        raw_cards = self.repository.listar_cartoes()
        resultado = []
        for c in raw_cards:
            item_info = c.get("items") or {}
            resultado.append(
                CardResponse(
                    id=c["id"],
                    card_name=c.get("name") or "Cartão sem Nome",
                    bank_name=item_info.get("bank_name") or "Banco sem Nome",
                    pluggy_account_id=c.get("pluggy_account_id"),
                    item_id=c.get("item_id"),
                    created_at=c.get("created_at")
                )
            )
        return resultado

    def atualizar_cartao(self, card_id: str, payload: CardUpdate) -> CardResponse:
        card_atualizado = self.repository.atualizar_cartao(card_id, card_name=payload.card_name, bank_name=payload.bank_name)
        if not card_atualizado:
            raise ValueError("Cartão não encontrado.")
        item_info = card_atualizado.get("items") or {}
        return CardResponse(
            id=card_atualizado["id"],
            card_name=card_atualizado.get("name") or "Cartão sem Nome",
            bank_name=item_info.get("bank_name") or "Banco sem Nome",
            pluggy_account_id=card_atualizado.get("pluggy_account_id"),
            item_id=card_atualizado.get("item_id"),
            created_at=card_atualizado.get("created_at")
        )

    def excluir_cartao(self, card_id: str) -> dict:
        resultado = self.repository.deletar_cartao_e_dependencias(card_id)
        if not resultado or not resultado["deleted"]:
            raise ValueError("Cartão não encontrado ou falha ao excluir.")
        return {
            "status": "sucesso",
            "mensagem": "Cartão e transações excluídos com sucesso.",
            "transacoes_deletadas": resultado["deleted_transactions"],
        }

    def criar_cartao(self, payload: CardCreate) -> CardResponse:
        card_novo = self.repository.criar_cartao(
            card_name=payload.card_name,
            bank_name=payload.bank_name,
            user_id=payload.user_id,
            pluggy_account_id=payload.pluggy_account_id,
            pluggy_item_id=payload.pluggy_item_id
        )
        item_info = card_novo.get("items") or {}
        return CardResponse(
            id=card_novo["id"],
            card_name=card_novo.get("name") or "Cartão sem Nome",
            bank_name=item_info.get("bank_name") or "Banco sem Nome",
            pluggy_account_id=card_novo.get("pluggy_account_id"),
            item_id=card_novo.get("item_id"),
            created_at=card_novo.get("created_at")
        )

    def buscar_cartoes_pluggy_por_item(self, item_id: str) -> List[dict]:
        try:
            auth_resp = requests.post(
                "https://api.pluggy.ai/auth",
                json={"clientId": settings.PLUGGY_CLIENT_ID, "clientSecret": settings.PLUGGY_CLIENT_SECRET},
                timeout=10
            )
            auth_resp.raise_for_status()
            api_key = auth_resp.json().get("apiKey")

            headers = {"X-API-KEY": api_key, "Accept": "application/json"}
            accounts_resp = requests.get(
                "https://api.pluggy.ai/accounts",
                headers=headers,
                params={"itemId": item_id.strip(), "type": "CREDIT"},
                timeout=10
            )
            accounts_resp.raise_for_status()
            
            results = accounts_resp.json().get("results", [])
            cartoes_encontrados = []
            for acc in results:
                if acc.get("subtype") == "CREDIT_CARD" or acc.get("type") == "CREDIT":
                    cartoes_encontrados.append({
                        "pluggy_account_id": acc.get("id"),
                        "name": acc.get("name") or "Cartão de Crédito",
                        "number": acc.get("number") or "****",
                        "bank_name": acc.get("connector", {}).get("name") if isinstance(acc.get("connector"), dict) else "Banco"
                    })
            
            return cartoes_encontrados
        except Exception as e:
            raise ValueError(f"Erro ao consultar o Item ID na Pluggy: {str(e)}")