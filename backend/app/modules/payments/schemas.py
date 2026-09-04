from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime, date

class ExpenseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    due_day: int
    current_amount: float
    total_installments: Optional[int] = None
    start_installment: Optional[int] = None

class MonthlyPaymentUpdate(BaseModel):
    amount: float

class CategorySimple(BaseModel):
    id: str
    name: str

class PaymentItem(BaseModel):
    id: str
    expense_id: str
    name: str
    description: Optional[str] = ""
    category_id: Optional[str] = None
    category_name: str = "Geral"
    due_day: int
    due_date: str
    reference_month: str
    amount: float
    status: str
    paid_at: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    is_overdue: bool = False
    is_stacked: bool = False

class PaymentsKPIs(BaseModel):
    total_a_pagar_mes: float
    total_em_aberto: float
    total_pago: float
    total_em_atraso: float

class PaymentsDashboardResponse(BaseModel):
    mes: str
    meses_disponiveis: List[str]
    kpis: PaymentsKPIs
    pendencias_anteriores: List[PaymentItem]
    pagamentos_mes: List[PaymentItem]

class HistoryItem(BaseModel):
    mes: str
    previsto: float
    realizado: float

class HistoryResponse(BaseModel):
    historico: List[HistoryItem]