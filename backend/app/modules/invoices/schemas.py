from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

# 1. Faturas (Bills)
class BillResponse(BaseModel):
    id: str
    card_id: str
    card_name: str
    bank_name: str
    due_date: date
    total_amount: float

# 2. Categorias
class CategoryResponse(BaseModel):
    id: str
    description: str
    description_translated: Optional[str] = None
    color: str
    parent_id: Optional[str] = None

# 3. Transações
class TransactionResponse(BaseModel):
    id: str
    description: str
    amount: float
    date: datetime
    status: str
    card_id: str
    bank_name: str
    bill_id: Optional[str] = None
    category_id: Optional[str] = None
    category_name: str
    category_color: str
    is_ignored: bool = False  # <-- Nova coluna adicionada

class ToggleIgnoreResponse(BaseModel):
    id: str
    is_ignored: bool
    message: str

# 4. Resumo de Gastos por Categoria da Fatura
class CategorySummaryItem(BaseModel):
    category_id: str
    category_name: str
    category_color: str
    total_amount: float
    percentage: float
    transactions: List[TransactionResponse]  # <-- Adicionado lista de transações

class CategorySummaryResponse(BaseModel):
    bill_id: Optional[str] = None
    is_pending: bool
    total_bill: float
    categories: List[CategorySummaryItem]