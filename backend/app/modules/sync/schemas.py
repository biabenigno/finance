from pydantic import BaseModel
from typing import List

class SyncResumoItem(BaseModel):
    total_consultadas: int
    total_ja_existentes: int
    total_novas: int
    excedente_preview: int

class SyncPreviewItem(BaseModel):
    id: str
    banco: str
    data: str
    descricao: str
    valor: float

class SyncResponse(BaseModel):
    status: str
    resumo: SyncResumoItem
    preview_novas_transacoes: List[SyncPreviewItem]