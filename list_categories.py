import requests

class PluggyCategoriasClient:
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

    def obter_todas_categorias(self):
        """
        Busca e retorna a lista completa de categorias oficiais da Pluggy.
        Como a documentação aponta para uma PageResponseCategories, lidaremos
        com a paginação caso exista.
        """
        print("Buscando a árvore de categorias...")
        url = f"{self.BASE_URL}/categories"
        
        todas_categorias = []
        # Embora o endpoint /categories costumava trazer tudo em uma página só, 
        # a documentação lista parâmetros de paginação (page, totalPages). 
        # Implementar paginação garante que não vamos perder dados.
        pagina_atual = 1
        
        while True:
            params = {"page": pagina_atual}
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                resultados = data.get("results", [])
                todas_categorias.extend(resultados)
                
                total_paginas = data.get("totalPages", 1)
                
                if pagina_atual >= total_paginas:
                    break
                
                pagina_atual += 1

            except requests.exceptions.RequestException as e:
                print(f"Erro ao buscar categorias: {e}")
                if e.response is not None:
                     print(f"Detalhes: {e.response.text}")
                break

        return todas_categorias


if __name__ == "__main__":
    # Substitua com suas credenciais reais da aplicação
    MEU_CLIENT_ID = "07f0966b-7334-4b85-a94e-f698c09067a4"
    MEU_CLIENT_SECRET = "IEMfJhXXwtNtn4ICJvT-e8rwumX1lEVOty0VZ7xCmQU"

    cliente = PluggyCategoriasClient(client_id=MEU_CLIENT_ID, client_secret=MEU_CLIENT_SECRET)
    
    categorias = cliente.obter_todas_categorias()

    print(f"\n✅ Total de Categorias Encontradas: {len(categorias)}")
    print("=" * 80)
    print(f"{'ID':<12} | {'NOME (INGLÊS)':<25} | {'NOME (PT-BR)':<20} | {'ID PAI'}")
    print("-" * 80)
    
    # Ordenando pelo ID para que as subcategorias (ex: 01010000) fiquem logo abaixo da sua categoria pai (01000000)
    categorias_ordenadas = sorted(categorias, key=lambda x: x.get("id", ""))

    for cat in categorias_ordenadas:
        cat_id = cat.get("id")
        desc_en = cat.get("description", "N/A")
        # Nem todas categorias podem ter a tradução, então o fallback é o inglês
        desc_pt = cat.get("descriptionTranslated", desc_en) 
        pai_id = cat.get("parentId", "RAIZ (Nenhum)")
        
        # Recorta a string se for muito longa para não quebrar o alinhamento da tabela no console
        print(f"{cat_id:<12} | {desc_en[:25]:<25} | {desc_pt[:20]:<20} | {pai_id}")
    
    print("=" * 80)
    print("Para popular seu banco Supabase, você usaria o ID acima na coluna 'id', ")
    print("o NOME (PT-BR) na coluna 'description_translated' e o ID PAI na coluna 'parent_id'.")