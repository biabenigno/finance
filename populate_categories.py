import requests
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÕES DE CREDENCIAIS
# ==========================================
PLUGGY_CLIENT_ID = "07f0966b-7334-4b85-a94e-f698c09067a4"
PLUGGY_CLIENT_SECRET = "IEMfJhXXwtNtn4ICJvT-e8rwumX1lEVOty0VZ7xCmQU"

SUPABASE_URL = "https://dhwlcympxwynndnmcxwc.supabase.co"
SUPABASE_KEY = "sb_secret_w3TPLGrTQc5YSHIkhRCZKA_8E-2Jksn"

# Inicializa o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class PluggyCategoriasLoader:
    BASE_URL = "https://api.pluggy.ai"

    def __init__(self, client_id, client_secret):
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._autenticar(client_id, client_secret)

    def _autenticar(self, client_id, client_secret):
        print("Autenticando na Pluggy...")
        url = f"{self.BASE_URL}/auth"
        payload = {"clientId": client_id, "clientSecret": client_secret}
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        self.headers["X-API-KEY"] = response.json().get("apiKey")
        print("Autenticação realizada com sucesso!\n")

    def buscar_categorias(self):
        print("Buscando categorias na API da Pluggy...")
        url = f"{self.BASE_URL}/categories"
        todas_categorias = []
        pagina_atual = 1

        while True:
            response = requests.get(url, headers=self.headers, params={"page": pagina_atual})
            response.raise_for_status()
            data = response.json()
            
            todas_categorias.extend(data.get("results", []))
            if pagina_atual >= data.get("totalPages", 1):
                break
            pagina_atual += 1

        return todas_categorias


def popular_supabase_categorias():
    # 1. Busca as categorias na API
    loader = PluggyCategoriasLoader(PLUGGY_CLIENT_ID, PLUGGY_CLIENT_SECRET)
    categorias_pluggy = loader.buscar_categorias()
    
    print(f"Total de {len(categorias_pluggy)} categorias capturadas.")
    print("Iniciando população no Supabase...\n")

    # 2. PASSO 1: Insere todas as categorias SEM o parent_id
    # Isso garante que todos os IDs existam no banco antes de criar os vínculos de hierarquia.
    payload_passo_1 = []
    for cat in categorias_pluggy:
        payload_passo_1.append({
            "id": cat.get("id"),
            "description": cat.get("description"),
            "description_translated": cat.get("descriptionTranslated", cat.get("description")),
            "parent_id": None # Força nulo na primeira passagem
        })

    print("Passo 1/2: Registrando/atualizando todas as categorias base...")
    response_p1 = supabase.table("categories").upsert(payload_passo_1).execute()
    print("Passo 1 concluído!")

    # 3. PASSO 2: Atualiza o parent_id para montar a árvore hierárquica
    payload_passo_2 = []
    for cat in categorias_pluggy:
        if cat.get("parentId"): # Só adiciona no lote quem realmente tem uma categoria Pai
            payload_passo_2.append({
                "id": cat.get("id"),
                "description": cat.get("description"),
                "description_translated": cat.get("descriptionTranslated", cat.get("description")),
                "parent_id": cat.get("parentId")
            })

    if payload_passo_2:
        print("Passo 2/2: Vinculando a hierarquia (Categorias Pais)...")
        response_p2 = supabase.table("categories").upsert(payload_passo_2).execute()
        print("Passo 2 concluído!")

    print("\n✅ Tabela 'categories' populada com sucesso no Supabase!")


if __name__ == "__main__":
    if SUPABASE_URL == "https://SEU_PROJETO.supabase.co":
        print("⚠️ Preencha as variáveis SUPABASE_URL e SUPABASE_KEY com os dados do seu projeto!")
    else:
        popular_supabase_categorias()