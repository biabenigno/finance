from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.modules.invoices.schemas import (
    BillResponse,
    CategoryResponse,
    ToggleIgnoreResponse,
    TransactionResponse,
    CategorySummaryResponse,
    CardResponse,
    CardUpdateName
)
from app.modules.invoices.service import InvoiceService

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

def get_service():
    return InvoiceService()

# 1. LISTAR FATURAS
@router.get("/bills", response_model=List[BillResponse])
def listar_faturas(
    card_id: Optional[str] = Query(None, description="Filtrar por ID do cartão"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):
    return service.obter_faturas(user_id=user_id, card_id=card_id)

# 2. LISTAR TRANSAÇÕES POR FATURA
@router.get("/transactions", response_model=List[TransactionResponse])
def listar_transacoes(
    bill_id: Optional[str] = Query(None, description="ID da fatura"),
    card_id: Optional[str] = Query(None, description="Filtrar por cartão"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):
    return service.obter_transacoes(user_id=user_id, bill_id=bill_id, card_id=card_id)

# 3. LISTAR CATEGORIAS
@router.get("/categories", response_model=List[CategoryResponse])
def listar_categorias(service: InvoiceService = Depends(get_service)):
    return service.obter_categorias()

# 4. RESUMO POR CATEGORIA
@router.get("/categories-summary", response_model=CategorySummaryResponse)
def obter_resumo_categorias(
    bill_id: Optional[str] = Query(None, description="ID da fatura"),
    card_id: Optional[str] = Query(None, description="Filtrar por cartão"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):
    return service.obter_resumo_categorias_fatura(user_id=user_id, bill_id=bill_id, card_id=card_id)

# 5. ALTERNAR STATUS IGNORED
@router.patch("/transactions/{transaction_id}/ignore", response_model=ToggleIgnoreResponse)
def alternar_transacao_ignorada(
    transaction_id: str,
    is_ignored: bool = Query(..., description="True para desconsiderar, False para incluir"),
    service: InvoiceService = Depends(get_service)
):
    return service.alternar_ignorada(transaction_id=transaction_id, is_ignored=is_ignored)

# 6. GERENCIAR CARTÕES
@router.get("/cards", response_model=List[CardResponse])
def listar_cartoes(service: InvoiceService = Depends(get_service)):
    return service.obter_cartoes()

@router.patch("/cards/{card_id}", response_model=CardResponse)
def renomear_cartao(
    card_id: str, 
    payload: CardUpdateName, 
    service: InvoiceService = Depends(get_service)
):
    return service.renomear_cartao(card_id=card_id, novo_nome=payload.bank_name)