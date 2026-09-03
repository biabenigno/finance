from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.modules.invoices.schemas import (
    BillResponse,
    CategoryResponse,
    ToggleIgnoreResponse,
    TransactionResponse,
    CategorySummaryResponse
)  # <-- Adicionado o ')' aqui
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
):  # <-- Adicionado o ':' aqui
    """Lista todas as faturas fechadas salvas no banco para o usuário"""
    return service.obter_faturas(user_id=user_id, card_id=card_id)

# 2. LISTAR TRANSAÇÕES POR FATURA (OU PENDENTES)
@router.get("/transactions", response_model=List[TransactionResponse])
def listar_transacoes(
    bill_id: Optional[str] = Query(None, description="ID da fatura. Se omitted/null, traz as pendentes (fatura aberta)"),
    card_id: Optional[str] = Query(None, description="Filtrar por cartão específico"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):  # <-- Adicionado o ':' aqui
    """Retorna a lista de transações vinculadas a uma fatura ou em aberto (bill_id=null)"""
    return service.obter_transacoes(user_id=user_id, bill_id=bill_id, card_id=card_id)

# 3. LISTAR CATEGORIAS
@router.get("/categories", response_model=List[CategoryResponse])
def listar_categorias(service: InvoiceService = Depends(get_service)):
    """Lista todas as categorias mestre do sistema"""
    return service.obter_categorias()

# 4. RESUMO DE VALORES DA FATURA POR CATEGORIA
@router.get("/categories-summary", response_model=CategorySummaryResponse)
def obter_resumo_categorias(
    bill_id: Optional[str] = Query(None, description="ID da fatura. Se omitted/null, traz os valores da fatura aberta"),
    card_id: Optional[str] = Query(None, description="Filtrar por cartão específico"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):  # <-- Adicionado o ':' aqui
    """Agrupa e soma os gastos de uma fatura por categoria para renderização de gráficos"""
    return service.obter_resumo_categorias_fatura(user_id=user_id, bill_id=bill_id, card_id=card_id)

# 5. ALTERNAR STATUS DE DESCONSIDERAR TRANSAÇÃO
@router.patch("/transactions/{transaction_id}/ignore", response_model=ToggleIgnoreResponse)
def alternar_transacao_ignorada(
    transaction_id: str,
    is_ignored: bool = Query(..., description="True para desconsiderar, False para incluir"),
    service: InvoiceService = Depends(get_service)
):
    """Marca ou desmarca uma transação para ser ignorada no gráfico de categorias e nos totais"""
    return service.alternar_ignorada(transaction_id=transaction_id, is_ignored=is_ignored)