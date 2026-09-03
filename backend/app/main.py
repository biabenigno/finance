from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.invoices.router import router as invoices_router

app = FastAPI(title="Finanças API", version="1.0.0")

# Libera o acesso para o Live Server / Front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoices_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API rodando perfeitamente!"}