from fastapi import FastAPI
from app.modules.invoices.router import router as invoices_router

# A variável OBRIGATORIAMENTE precisa se chamar "app"
app = FastAPI(
    title="Finanças API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Registro do módulo de faturas
app.include_router(invoices_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API rodando perfeitamente!"}