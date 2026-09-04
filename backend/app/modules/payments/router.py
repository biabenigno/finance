from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.modules.payments.schemas import (
    ExpenseCreate,
    MonthlyPaymentUpdate,
    PaymentsDashboardResponse,
    HistoryResponse,
    CategorySimple
)
from app.modules.payments.service import PaymentsService

router = APIRouter(prefix="/api/v1/payments", tags=["Pagamentos"])

def get_service():
    return PaymentsService()

@router.get("", response_model=PaymentsDashboardResponse)
def obter_pagamentos(
    mes: Optional[str] = Query(None, description="Mês no formato YYYY-MM"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    return service.obter_dashboard(user_id=user_id, mes=mes)

@router.get("/categories", response_model=List[CategorySimple])
def obter_categorias_pagamento(
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    return service.obter_categorias()

@router.post("/expenses")
def criar_despesa_recorrente(
    payload: ExpenseCreate,
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    return service.criar_despesa(user_id=user_id, payload=payload)

@router.put("/monthly/{monthly_id}")
def atualizar_valor_mensal(
    monthly_id: str,
    payload: MonthlyPaymentUpdate,
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    return service.atualizar_valor_mensal(monthly_id=monthly_id, user_id=user_id, payload=payload)

@router.patch("/monthly/{monthly_id}/pay")
def alternar_pagamento(
    monthly_id: str,
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    return service.alternar_status_pagamento(monthly_id=monthly_id, user_id=user_id)

@router.delete("/expenses/{expense_id}")
def excluir_despesa(
    expense_id: str,
    mes: str = Query(..., description="Mês de corte YYYY-MM"),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    service.excluir_despesa(expense_id=expense_id, user_id=user_id, mes=mes)
    return {"status": "sucesso", "mensagem": "Conta desativada com sucesso"}

@router.get("/history", response_model=HistoryResponse)
def obter_historico(
    ano: int = Query(2026),
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: PaymentsService = Depends(get_service)
):
    return service.obter_historico(user_id=user_id, ano=ano)