import requests

class PluggyClient:
    BASE_URL = "https://api.pluggy.ai"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = None
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._authenticate()

    def _authenticate(self):
        print("Autenticando na Pluggy...")
        url = f"{self.BASE_URL}/auth"
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            self.api_key = data.get("apiKey")
            self.headers["X-API-KEY"] = self.api_key
            print("Autenticação realizada com sucesso!\n")
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao autenticar: {e}")
            raise SystemExit(e)

    def listar_cartoes_do_item(self, item_id):
        print(f"Buscando cartões de crédito para o Item: {item_id}...")
        url_accounts = f"{self.BASE_URL}/accounts"
        params = {"itemId": item_id, "type": "CREDIT"}
        
        try:
            response = requests.get(url_accounts, headers=self.headers, params=params)
            response.raise_for_status()
            contas = response.json().get("results", [])
            cartoes = [c for c in contas if c.get("subtype") == "CREDIT_CARD"]
            return cartoes
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar contas do item: {e}")
            return []

    def obter_todas_faturas(self, account_id):
        """
        Busca e retorna todas as faturas da conta ordenadas da mais recente para a mais antiga.
        """
        print(f"Buscando todas as faturas para a Conta: {account_id}...")
        url_bills = f"{self.BASE_URL}/bills"
        params = {"accountId": account_id}

        try:
            response = requests.get(url_bills, headers=self.headers, params=params)
            response.raise_for_status()
            
            faturas = response.json().get("results", [])
            return sorted(faturas, key=lambda x: x.get("dueDate", ""), reverse=True)

        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar faturas: {e}")
            return []

    def obter_transacoes_da_conta(self, account_id):
        """
        Busca TODAS as transações da conta na API v2.
        """
        print(f"\nBuscando histórico de transações da conta {account_id} (API v2)...")
        url_transactions = f"{self.BASE_URL}/v2/transactions"
        
        todas_transacoes = []
        cursor = None
        
        while True:
            params = {"accountId": account_id}
            if cursor:
                params["cursor"] = cursor

            try:
                response = requests.get(url_transactions, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                resultados_pagina = data.get("results", [])
                todas_transacoes.extend(resultados_pagina)
                
                if data.get("nextCursor"):
                     cursor = data.get("nextCursor")
                elif data.get("pagination") and data["pagination"].get("nextCursor"):
                     cursor = data["pagination"].get("nextCursor")
                else:
                     break

            except requests.exceptions.RequestException as e:
                print(f"Erro ao buscar transações na API v2: {e}")
                break

        return todas_transacoes


if __name__ == "__main__":
    MEU_CLIENT_ID = "07f0966b-7334-4b85-a94e-f698c09067a4"
    MEU_CLIENT_SECRET = "IEMfJhXXwtNtn4ICJvT-e8rwumX1lEVOty0VZ7xCmQU"
    MEU_ITEM_ID = "cd103ee1-49a4-44df-a1df-2b4901a64089"

    cliente = PluggyClient(client_id=MEU_CLIENT_ID, client_secret=MEU_CLIENT_SECRET)
    
    meus_cartoes = cliente.listar_cartoes_do_item(item_id=MEU_ITEM_ID)

    if meus_cartoes:
        cartao_alvo = meus_cartoes[0]
        account_id = cartao_alvo.get("id")
        
        # 1. Puxa todas as faturas
        faturas = cliente.obter_todas_faturas(account_id=account_id)
        
        # Pega a última fatura FECHADA (que é a primeira da lista, índice 0)
        ultima_fatura_fechada = faturas[0] if faturas else None
        
        # 2. Puxa TODAS as transações
        todas_transacoes = cliente.obter_transacoes_da_conta(account_id=account_id)
        
        print(f"\nTotal histórico de transações: {len(todas_transacoes)}")
        print("=" * 75)
        
        # ==========================================
        # ANÁLISE 1: A FATURA ABERTA (Mês Atual)
        # ==========================================
        print("\n🔎 FATURA ABERTA (Transações ainda sem fatura consolidada):")
        # Transações que NÃO TÊM billId são a fatura aberta
        transacoes_abertas = [tx for tx in todas_transacoes if tx.get("billId") is None]
        
        # Opcional: ordenar da mais recente para a mais antiga
        transacoes_abertas.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        total_parcial = sum(tx.get("amount", 0) for tx in transacoes_abertas)
        print(f"Total Parcial Gasto: R$ {total_parcial:.2f} ({len(transacoes_abertas)} compras)")
        print("-" * 75)
        
        for idx, tx in enumerate(transacoes_abertas[:10], start=1): # Mostra só as 10 últimas pra não poluir
            data = tx.get("date", "")[:10]
            desc = tx.get("description", "Sem descrição")[:25]
            val = tx.get("amount", 0.0)
            status = tx.get("status", "N/A")
            print(f"{idx:02d} | {data} | {desc:<25} | R$ {val:>8.2f} | {status}")
        
        if len(transacoes_abertas) > 10:
             print(f"... e mais {len(transacoes_abertas) - 10} transações pendentes.")
        
        # ==========================================
        # ANÁLISE 2: A ÚLTIMA FATURA FECHADA (Agosto)
        # ==========================================
        if ultima_fatura_fechada:
            bill_id = ultima_fatura_fechada.get("id")
            venc = ultima_fatura_fechada.get("dueDate", "")[:10]
            val_total = ultima_fatura_fechada.get("totalAmount")
            
            print(f"\n\n📘 ÚLTIMA FATURA FECHADA (Vencimento: {venc}):")
            print(f"ID: {bill_id}")
            print(f"Valor Fechado Oficial: R$ {val_total}")
            
            # Filtra as transações que têm O MESMO ID da última fatura fechada
            txs_fechadas = [tx for tx in todas_transacoes if tx.get("billId") == bill_id]
            print(f"Transações vinculadas a esta fatura: {len(txs_fechadas)}")
            print("-" * 75)
            
            for idx, tx in enumerate(txs_fechadas, start=1):
                data = tx.get("date", "")[:10]
                desc = tx.get("description", "Sem descrição")[:25]
                val = tx.get("amount", 0.0)
                print(f"{idx:02d} | {data} | {desc:<25} | R$ {val:>8.2f}")
        print("=" * 75)