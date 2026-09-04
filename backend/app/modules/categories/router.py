from fastapi import APIRouter, Depends, Query
from typing import List
from app.modules.invoices.schemas import CategoryResponse
from app.modules.invoices.service import InvoiceService

router = APIRouter(prefix="/api/v1/categories", tags=["Categorias"])

def get_service():
    return InvoiceService()

@router.get("", response_model=List[CategoryResponse])
def listar_categorias_globais(
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: InvoiceService = Depends(get_service)
):
    return service.obter_categorias()