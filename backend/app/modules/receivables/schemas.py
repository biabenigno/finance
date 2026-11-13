"""
Schemas Pydantic para o módulo Receivables (A Receber).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Schemas para Receivable People
# ============================================================================

class ReceivablePeopleBase(BaseModel):
    """Base para criação/edição de pessoa."""
    name: str = Field(..., min_length=1, max_length=255)


class ReceivablePeopleCreate(ReceivablePeopleBase):
    """Schema para criação de pessoa."""
    pass


class ReceivablePeopleResponse(ReceivablePeopleBase):
    """Schema de retorno para pessoa."""
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Schemas para Card Splits
# ============================================================================

class CardSplitBase(BaseModel):
    """Base para alocação de divisão de compra."""
    transaction_id: str
    person_id: str
    reference_month: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    is_integral: bool
    amount_person: Decimal = Field(..., gt=0)
    total_transaction_amount: Decimal = Field(..., gt=0)

    @field_validator("amount_person", "total_transaction_amount", mode="before")
    @classmethod
    def parse_decimal(cls, v):
        """Converte para Decimal se necessário."""
        if isinstance(v, str):
            return Decimal(v)
        return v


class CardSplitCreate(CardSplitBase):
    """Schema para criação/atualização de card split."""
    pass


class CardSplitResponse(CardSplitBase):
    """Schema de retorno para card split."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CardSplitWithTransactionDetails(CardSplitResponse):
    """Card split com detalhes da transação."""
    description: str
    date: datetime
    bank: str


# ============================================================================
# Schemas para Manual Debts
# ============================================================================

class ManualDebtBase(BaseModel):
    """Base para lançamento manual."""
    type: str = Field(..., pattern="^(charge|payment)$")
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=255)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_decimal(cls, v):
        """Converte para Decimal se necessário."""
        if isinstance(v, str):
            return Decimal(v)
        return v


class ManualDebtCreate(ManualDebtBase):
    """Schema para criação de lançamento manual."""
    person_id: str


class ManualDebtUpdate(BaseModel):
    """Schema para edição de lançamento manual."""
    type: Optional[str] = Field(None, pattern="^(charge|payment)$")
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=255)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_decimal(cls, v):
        """Converte para Decimal se necessário."""
        if v is not None and isinstance(v, str):
            return Decimal(v)
        return v


class ManualDebtResponse(ManualDebtBase):
    """Schema de retorno para lançamento manual."""
    id: str
    person_id: str
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Schemas consolidados para resumo e detalhes
# ============================================================================

class PersonCardSummary(BaseModel):
    """Resumo de cartão para uma pessoa em um período."""
    person_id: str
    person_name: str
    card_total: Decimal = Field(default=0)
    split_count: int = 0


class PersonManualSummary(BaseModel):
    """Resumo de saldo manual para uma pessoa."""
    person_id: str
    person_name: str
    manual_total: Decimal = Field(default=0)


class ReceivableSummaryItem(BaseModel):
    """Item do resumo consolidado de A Receber."""
    id: str
    name: str
    card_total: Decimal = Field(default=0)
    manual_total: Decimal = Field(default=0)

    class Config:
        from_attributes = True


class PersonDetailResponse(BaseModel):
    """Detalhes completos de uma pessoa incluindo cartão e saldo manual."""
    id: str
    name: str
    card_total: Decimal = Field(default=0)
    manual_total: Decimal = Field(default=0)
    card_splits: list[CardSplitWithTransactionDetails] = []
    manual_debts: list[ManualDebtResponse] = []
    available_months: list[str] = []

    class Config:
        from_attributes = True


class CardTransactionForAllocation(BaseModel):
    """Compra de cartão disponível para alocação."""
    id: str
    description: str
    amount: Decimal
    date: datetime
    bank: str
    card_name: Optional[str] = None
    card_id: Optional[str] = None
    is_linked: bool = False  # Indica se já está vinculada
    linked_to_person: bool = False  # Indica se está vinculada a esta pessoa específica


# ============================================================================
# Schemas de Validação
# ============================================================================

class AllocationValidationError(BaseModel):
    """Erro de validação de alocação."""
    message: str
    field: Optional[str] = None
