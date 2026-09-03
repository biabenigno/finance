import requests
from supabase import create_client, Client

# ==========================================
# 1. CREDENCIAIS
# ==========================================
PLUGGY_CLIENT_ID = "07f0966b-7334-4b85-a94e-f698c09067a4"
PLUGGY_CLIENT_SECRET = "IEMfJhXXwtNtn4ICJvT-e8rwumX1lEVOty0VZ7xCmQU"
MEU_ITEM_ID = "cd103ee1-49a4-44df-a1df-2b4901a64089"

SUPABASE_URL = "https://dhwlcympxwynndnmcxwc.supabase.co"
SUPABASE_KEY = "sb_secret_w3TPLGrTQc5YSHIkhRCZKA_8E-2Jksn" 
MEU_USER_ID = "d262bc6c-d58b-4f4e-99b4-505202b646ba" 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ServicoSincronizacao:
    BASE_URL = "https://api.pluggy.ai"

    def __init__(self):
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self._autenticar()

    def _autenticar(self):
        print("🔄 [1/6] Autenticando na Pluggy...")
        response = requests.post(f"{self.BASE_URL}/auth", json={"clientId": PLUGGY_CLIENT_ID, "clientSecret": PLUGGY_CLIENT_SECRET}, headers=self.headers)
        response.raise_for_status()
        self.headers["X-API-KEY"] = response.json().get("apiKey")

    def sincronizar_categorias_rapido(self):
        print("🔄 [2/6] Garantindo que todas as categorias existem no banco...")
        response = requests.get(f"{self.BASE_URL}/categories", headers=self.headers)
        categorias = response.json().get("results", [])
        
        payload = [{"id": c.get("id"), "description": c.get("description")} for c in categorias]
        supabase.table("categories").upsert(payload, ignore_duplicates=True).execute()

    def garantir_item_e_cartao(self, item_id, user_id):
        print(f"🔄 [3/6] Verificando Item e Cartão no banco...")
        
        res_item = requests.get(f"{self.BASE_URL}/items/{item_id}", headers=self.headers).json()
        
        item_db = supabase.table("items").upsert(
            {
                "user_id": user_id,
                "pluggy_item_id": item_id,
                "bank_name": res_item.get("connector", {}).get("name", "Banco"),
                "status": res_item.get("status", "UPDATED")
            },
            on_conflict="pluggy_item_id"
        ).execute()
        item_uuid = item_db.data[0]['id']

        res_accounts = requests.get(f"{self.BASE_URL}/accounts", headers=self.headers, params={"itemId": item_id, "type": "CREDIT"}).json()
        cartoes = [c for c in res_accounts.get("results", []) if c.get("subtype") == "CREDIT_CARD"]
        
        cartoes_db = []
        for cartao in cartoes:
            c_db = supabase.table("cards").upsert(
                {
                    "item_id": item_uuid,
                    "pluggy_account_id": cartao.get("id"),
                    "name": cartao.get("name", "Cartão de Crédito"),
                    "last_digits": cartao.get("number", "****"),
                    "credit_limit": cartao.get("creditData", {}).get("creditLimit", 0)
                },
                on_conflict="pluggy_account_id"
            ).execute()
            cartoes_db.append(c_db.data[0])
            
        return cartoes_db

    def sincronizar_faturas(self, account_id, card_uuid):
        print(f"🔄 [4/6] Sincronizando Faturas (Bills)...")
        res_bills = requests.get(f"{self.BASE_URL}/bills", headers=self.headers, params={"accountId": account_id}).json()
        faturas = res_bills.get("results", [])
        
        payload_faturas = []
        for fatura in faturas:
            payload_faturas.append({
                "id": fatura.get("id"),
                "card_id": card_uuid,
                "due_date": fatura.get("dueDate", "")[:10],
                "total_amount": fatura.get("totalAmount", 0)
            })
            
        if payload_faturas:
            supabase.table("bills").upsert(payload_faturas).execute()
        print(f"   ✅ {len(payload_faturas)} faturas atualizadas no banco.")

    def sincronizar_transacoes(self, account_id, card_uuid, data_corte=None):
        """
        Sincroniza transações extraindo o billId tanto da raiz quanto de creditCardMetadata.
        """
        print(f"🔄 [5/6] Buscando Transações na Pluggy (Filtro 'from': {data_corte or 'Desativado/Sandbox'})...")
        url = f"{self.BASE_URL}/v2/transactions"
        cursor = None
        todas_transacoes = []
        
        while True:
            params = {"accountId": account_id}
            if data_corte:
                params["from"] = data_corte
                
            if cursor: 
                params["cursor"] = cursor
                
            res = requests.get(url, headers=self.headers, params=params).json()
            todas_transacoes.extend(res.get("results", []))
            
            cursor = res.get("nextCursor") or (res.get("pagination") or {}).get("nextCursor")
            if not cursor: 
                break

        print(f"   ↳ Total bruto retornado pela API da Pluggy: {len(todas_transacoes)}")

        if data_corte:
            res_faturas = supabase.table("bills").select("id").filter("card_id", "eq", card_uuid).filter("due_date", "gte", "2026-06-01").execute()
            faturas_validas_ids = {f["id"] for f in res_faturas.data}

            transacoes_filtradas = []
            for tx in todas_transacoes:
                metadata = tx.get("creditCardMetadata") or {}
                bill_id = tx.get("billId") or metadata.get("billId")
                if bill_id is None or bill_id in faturas_validas_ids:
                    transacoes_filtradas.append(tx)
        else:
            transacoes_filtradas = todas_transacoes

        print(f"🔄 [6/6] Salvando/Atualizando {len(transacoes_filtradas)} transações no banco...")
        
        tamanho_lote = 100
        for i in range(0, len(transacoes_filtradas), tamanho_lote):
            lote = transacoes_filtradas[i:i + tamanho_lote]
            payload_tx = []
            
            for tx in lote:
                # EXTRAÇÃO INTELIGENTE DO BILL_ID:
                # Busca na raiz ou dentro do objeto creditCardMetadata
                metadata = tx.get("creditCardMetadata") or {}
                bill_id_extraido = tx.get("billId") or metadata.get("billId")

                payload_tx.append({
                    "id": tx.get("id"),
                    "card_id": card_uuid,
                    "bill_id": bill_id_extraido, # Agora captura o ID onde quer que ele esteja no JSON!
                    "category_id": tx.get("categoryId"),
                    "description": tx.get("description", "Sem descrição"),
                    "amount": tx.get("amount", 0),
                    "date": tx.get("date"),
                    "status": tx.get("status", "PENDING")
                })
            
            supabase.table("transactions").upsert(payload_tx).execute()
            
        print("   ✅ Transações salvas no Supabase com sucesso!")
# ==========================================
# EXECUÇÃO DO BOTÃO
# ==========================================
if __name__ == "__main__":
    print("🚀 INICIANDO SINCRONIZAÇÃO...\n")
    
    servico = ServicoSincronizacao()
    servico.sincronizar_categorias_rapido() 
    cartoes_banco = servico.garantir_item_e_cartao(item_id=MEU_ITEM_ID, user_id=MEU_USER_ID)
    
    for cartao_db in cartoes_banco:
        pluggy_account_id = cartao_db['pluggy_account_id']
        card_uuid_interno = cartao_db['id']
        
        print(f"\n--- Sincronizando Cartão: {cartao_db['name']} ---")
        
        servico.sincronizar_faturas(account_id=pluggy_account_id, card_uuid=card_uuid_interno)
        
        # Para testar no Sandbox, usamos data_corte=None.
        # Quando for para produção com bancos reais, mude para: data_corte="2026-05-01"
        servico.sincronizar_transacoes(
            account_id=pluggy_account_id, 
            card_uuid=card_uuid_interno, 
            data_corte=None
        )
        
    print("\n🎉 SINCRONIZAÇÃO FINALIZADA COM SUCESSO!")