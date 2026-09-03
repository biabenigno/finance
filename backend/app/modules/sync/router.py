from fastapi import APIRouter, Depends, Query
from app.modules.sync.schemas import SyncResponse
from app.modules.sync.service import SyncService

router = APIRouter(prefix="/api/v1/sync", tags=["Sync"])

def get_service():
    return SyncService()

@router.post("", response_model=SyncResponse)
def sincronizar_dados(
    user_id: str = Query("d262bc6c-d58b-4f4e-99b4-505202b646ba"),
    service: SyncService = Depends(get_service)
):
    """Realiza a varredura completa na Pluggy e atualiza o Supabase."""
    return service.executar_sincronizacao(user_id=user_id)