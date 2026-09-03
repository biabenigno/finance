from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.modules.invoices.schemas import (
    BillResponse,
    CategoryResponse,
    ToggleIgnoreResponse,
    TransactionResponse,
    CategorySummaryResponse,
    CardResponse,
    CardUpdate,
    CardCreate
)
from app.modules.invoices.service import InvoiceService

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

def get_service():
    return InvoiceService()

@router.get("/bills", response_model=List[BillResponse])
def listar_faturas(card_id: Optional[str] = Query(None), user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"), service: InvoiceService = Depends(get_service)):
    return service.obter_faturas(user_id=user_id, card_id=card_id)

@router.get("/transactions", response_model=List[TransactionResponse])
def listar_transacoes(
    fatura: Optional[str] = Query(None, description="'atual', mês YYYY-MM ou bill_id"),
    card_id: Optional[str] = Query(None),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):
    return service.obter_transacoes(user_id=user_id, fatura=fatura, card_id=card_id)

@router.get("/categories", response_model=List[CategoryResponse])
def listar_categorias(service: InvoiceService = Depends(get_service)):
    return service.obter_categorias()

@router.get("/categories-summary", response_model=CategorySummaryResponse)
def obter_resumo_categorias(
    fatura: Optional[str] = Query(None, description="'atual', mês YYYY-MM ou bill_id"),
    card_id: Optional[str] = Query(None),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):
    return service.obter_resumo_categorias_fatura(user_id=user_id, fatura=fatura, card_id=card_id)

@router.patch("/transactions/{transaction_id}/ignore", response_model=ToggleIgnoreResponse)
def alternar_transacao_ignorada(transaction_id: str, is_ignored: bool = Query(...), service: InvoiceService = Depends(get_service)):
    return service.alternar_ignorada(transaction_id=transaction_id, is_ignored=is_ignored)

@router.get("/cards", response_model=List[CardResponse])
def listar_cartoes(service: InvoiceService = Depends(get_service)):
    return service.obter_cartoes()

@router.post("/cards", response_model=CardResponse)
def criar_cartao(payload: CardCreate, service: InvoiceService = Depends(get_service)):
    return service.criar_cartao(payload)

@router.patch("/cards/{card_id}", response_model=CardResponse)
def renomear_cartao(card_id: str, payload: CardUpdate, service: InvoiceService = Depends(get_service)):
    return service.atualizar_cartao(card_id=card_id, payload=payload)

@router.get("/pluggy/accounts/{item_id}")
def buscar_contas_pluggy(item_id: str, service: InvoiceService = Depends(get_service)):
    return service.buscar_cartoes_pluggy_por_item(item_id)