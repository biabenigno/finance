import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.modules.invoices.router import router as invoices_router
from app.modules.sync.router import router as sync_router
from app.modules.payments.router import router as payments_router
from app.modules.categories.router import router as categories_router
from app.modules.receivables.router import router as receivables_router

app = FastAPI(title="Finanças API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra todos os roteadores da API
app.include_router(invoices_router)
app.include_router(sync_router)
app.include_router(payments_router)
app.include_router(categories_router)
app.include_router(receivables_router)

# Mapeia a pasta estática do Frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")