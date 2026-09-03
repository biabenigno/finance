import logging
import requests
from typing import List
from app.core.config import settings
from app.modules.sync.repository import SyncRepository
from app.modules.sync.schemas import SyncResponse, SyncResumoItem, SyncPreviewItem

logger = logging.getLogger("uvicorn.error")

class SyncService:
    def __init__(self):
        self.repository = SyncRepository()

    def executar_sincronizacao(self, user_id: str) -> SyncResponse:
        cards_raw = self.repository.obter_cartoes_conectados()
        user_cards = [
            c for c in cards_raw 
            if (c.get("items") or {}).get("user_id") == user_id and c.get("pluggy_account_id")
        ]

        if not user_cards:
            return SyncResponse(
                status="sucesso",
                resumo=SyncResumoItem(total_consultadas=0, total_ja_existentes=0, total_novas=0, excedente_preview=0),
                preview_novas_transacoes=[]
            )

        # 1. Autenticação na Pluggy
        try:
            auth_resp = requests.post(
                "https://api.pluggy.ai/auth",
                json={"clientId": settings.PLUGGY_CLIENT_ID, "clientSecret": settings.PLUGGY_CLIENT_SECRET},
                timeout=10
            )
            auth_resp.raise_for_status()
            api_key = auth_resp.json().get("apiKey")
        except Exception as e:
            raise ValueError(f"Falha na autenticação Pluggy: {str(e)}")

        headers = {"X-API-KEY": api_key, "Accept": "application/json"}

        # 2. ETAPA 1: Puxa e salva TODAS as faturas de todos os cartões primeiro
        bills_to_upsert = []
        for card in user_cards:
            account_id = card.get("pluggy_account_id")
            card_id = card.get("id")

            try:
                bills_resp = requests.get(
                    "https://api.pluggy.ai/bills",
                    headers=headers,
                    params={"accountId": account_id},
                    timeout=15
                )
                if bills_resp.status_code == 200:
                    for b in bills_resp.json().get("results", []):
                        if b.get("id") and b.get("dueDate"):
                            bills_to_upsert.append({
                                "id": b.get("id"),
                                "card_id": card_id,
                                "due_date": str(b.get("dueDate"))[:10],
                                "total_amount": float(b.get("totalAmount") or 0)
                            })
            except Exception as e:
                logger.error(f"[SYNC BILLS ERROR] {e}")

        # Grava as faturas imediatamente no Supabase
        if bills_to_upsert:
            self.repository.salvar_faturas_em_lote(bills_to_upsert)

        # 3. ETAPA 2: Puxa e salva as transações vinculadas
        ids_existentes = self.repository.obter_ids_transacoes_existentes()
        records_to_upsert = []
        novas_preview = []
        todas_coletadas = 0
        ja_existentes = 0

        for card in user_cards:
            account_id = card.get("pluggy_account_id")
            card_id = card.get("id")
            bank_name = (card.get("items") or {}).get("bank_name") or card.get("name") or "Cartão"

            cursor = None
            while True:
                url = f"https://api.pluggy.ai/v2/transactions?accountId={account_id}"
                if cursor:
                    url += f"&cursor={cursor}"

                try:
                    res = requests.get(url, headers=headers, timeout=20)
                    if res.status_code != 200:
                        break

                    data = res.json()
                    results = data.get("results") or []
                    if not results:
                        break

                    for tx in results:
                        todas_coletadas += 1
                        tx_id = tx.get("id")
                        metadata = tx.get("creditCardMetadata") or {}
                        bill_id = tx.get("billId") or metadata.get("billId")

                        is_nova = tx_id not in ids_existentes
                        if is_nova:
                            ids_existentes.add(tx_id)
                        else:
                            ja_existentes += 1

                        amount = float(tx.get("amount") or 0)
                        records_to_upsert.append({
                            "id": tx_id,
                            "card_id": card_id,
                            "bill_id": bill_id,
                            "category_id": tx.get("categoryId"),
                            "description": tx.get("description", "Sem descrição"),
                            "amount": amount,
                            "date": tx.get("date"),
                            "status": tx.get("status", "PENDING")
                        })

                        if is_nova:
                            novas_preview.append(SyncPreviewItem(
                                id=str(tx_id),
                                banco=bank_name,
                                data=str(tx.get("date", ""))[:10],
                                descricao=tx.get("description", "Sem descrição"),
                                valor=abs(amount)
                            ))

                    cursor = data.get("nextCursor") or (data.get("pagination") or {}).get("nextCursor")
                    if not cursor:
                        break
                except Exception as e:
                    logger.error(f"[SYNC TX ERROR] {e}")
                    break

        self.repository.salvar_transacoes_em_lote(records_to_upsert)
        total_novas = len(novas_preview)

        return SyncResponse(
            status="sucesso",
            resumo=SyncResumoItem(
                total_consultadas=todas_coletadas,
                total_ja_existentes=ja_existentes,
                total_novas=total_novas,
                excedente_preview=max(0, total_novas - 5)
            ),
            preview_novas_transacoes=novas_preview[:5]
        ) 