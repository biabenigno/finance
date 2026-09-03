from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime, date

class BillResponse(BaseModel):
    id: str
    card_id: str
    card_name: str
    bank_name: str
    due_date: date
    total_amount: float

class CategoryResponse(BaseModel):
    id: str
    description: str
    description_translated: Optional[str] = None
    color: str
    parent_id: Optional[str] = None

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
    is_ignored: bool = False

class ToggleIgnoreResponse(BaseModel):
    id: str
    is_ignored: bool
    message: str

class CategorySummaryItem(BaseModel):
    category_id: str
    category_name: str
    category_color: str
    total_amount: float
    percentage: float
    transactions: List[TransactionResponse]

class CategorySummaryResponse(BaseModel):
    bill_id: Optional[str] = None
    is_pending: bool
    total_bill: float
    categories: List[CategorySummaryItem]

class CardResponse(BaseModel):
    id: Union[int, str]
    card_name: str
    bank_name: str
    pluggy_account_id: Optional[str] = None
    item_id: Optional[Union[int, str]] = None
    created_at: Optional[datetime] = None

class CardUpdate(BaseModel):
    card_name: Optional[str] = None
    bank_name: Optional[str] = None

class CardCreate(BaseModel):
    card_name: str
    bank_name: str
    user_id: Optional[str] = "d262bc6c-d58b-4f4e-99b4-505202b646ba"
    pluggy_account_id: Optional[str] = None
    pluggy_item_id: Optional[str] = None