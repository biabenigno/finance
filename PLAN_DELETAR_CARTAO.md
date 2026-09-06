# Plano de Implementação: Exclusão de Cartões e Transações em Cascata

Este documento especifica o fluxo técnico e visual para permitir a exclusão de um cartão de crédito no painel de gerenciamento, garantindo que todas as faturas e transações associadas a ele sejam permanentemente removidas em cascata, mediante confirmação explícita do usuário.

## 1. Mapeamento de Exclusão em Cascata

Ao excluir um cartão (cards.id), a remoção deve respeitar a integridade referencial do Supabase, deletando os registros dependentes na seguinte ordem:

- `card_splits`: remove alocações de compras compartilhadas vinculadas às transações do cartão.
- `transactions`: remove todas as compras e estornos gravados para o `card_id`.
- `bills`: remove os registros de faturas vinculadas ao `card_id`.
- `cards`: exclui o registro do cartão de crédito.
- `items` (opcional): caso o conector (`items.id`) não possua outros cartões vinculados, o item da Pluggy/banco conector também pode ser desvinculado.

## 2. Alterações no Backend (FastAPI)

### Repositório

Arquivo: `backend/app/modules/invoices/repository.py`

Adicionar o método estático para executar a exclusão ordenada das tabelas filhas e do cartão:

```python
    @staticmethod
    def deletar_cartao_e_dependencias(card_id: str) -> bool:
        # 1. Busca os IDs das transações vinculadas ao cartão
        res_txs = supabase.table("transactions").select("id").eq("card_id", card_id).execute()
        tx_ids = [t["id"] for t in (res_txs.data or [])]

        # 2. Deleta os vínculos de divisão de cartão (card_splits)
        if tx_ids:
            supabase.table("card_splits").delete().in_("transaction_id", tx_ids).execute()

        # 3. Deleta todas as transações do cartão
        supabase.table("transactions").delete().eq("card_id", card_id).execute()

        # 4. Deleta todas as faturas (bills) do cartão
        supabase.table("bills").delete().eq("card_id", card_id).execute()

        # 5. Obtém o item_id antes de deletar o cartão para verificar se o banco conector fica órfão
        res_card = supabase.table("cards").select("item_id").eq("id", card_id).execute()
        item_id = res_card.data[0]["item_id"] if res_card.data else None

        # 6. Deleta o cartão
        res_del = supabase.table("cards").delete().eq("id", card_id).execute()

        # 7. Se houver item_id e nenhum outro cartão o utilizar, deleta o item
        if item_id:
            res_other_cards = supabase.table("cards").select("id").eq("item_id", item_id).execute()
            if not res_other_cards.data:
                supabase.table("items").delete().eq("id", item_id).execute()

        return bool(res_del.data)

    ```

    ### Serviço

    Arquivo: `backend/app/modules/invoices/service.py`

Adicionar a chamada de regra de negócio:

    ```python
    def excluir_cartao(self, card_id: str):
        sucesso = self.repository.deletar_cartao_e_dependencias(card_id)
        if not sucesso:
            raise ValueError("Cartão não encontrado ou falha ao excluir.")
        return {"status": "sucesso", "mensagem": "Cartão e transações excluídos com sucesso."}

    ```

    ### Roteador

    Arquivo: `backend/app/modules/invoices/router.py`

Criar o endpoint HTTP DELETE:

    ```python
@router.delete("/cards/{card_id}")
def excluir_cartao(
    card_id: str,
    service: InvoiceService = Depends(get_service)
):
    return service.excluir_cartao(card_id=card_id)

```

## 3. Alterações no Frontend

### Visualização do cartão

Arquivo: `frontend/src/pages/cards/cards.js`

Incluir um botão com ícone de lixeira no cabeçalho do card de cada cartão listado:

```javascript
// Exemplo de botão inserido ao lado do botão de editar
<button onclick="window.abrirModalExclusaoCartao('${card.id}', '${card.card_name}')" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition" title="Excluir Cartão">
    <span class="material-symbols-outlined text-base">delete</span>
</button>

```

### Modal de confirmação

Arquivo: `frontend/src/pages/cards/cards.html`

Adicionar o componente de confirmação com destaque visual de alerta (vermelho/rose):

```html
<!-- Modal Confirmar Exclusão de Cartão -->
<div id="modal-confirmar-exclusao-cartao" class="fixed inset-0 z-50 hidden bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-md p-6 text-center space-y-4">
        <div class="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
            <span class="material-symbols-outlined text-2xl">warning</span>
        </div>
        <div>
            <h3 class="text-lg font-bold text-slate-800">Excluir Cartão e Transações</h3>
            <p id="msg-confirmacao-exclusao-cartao" class="text-xs text-slate-600 mt-2 leading-relaxed">
                Tem certeza que deseja excluir o cartão <strong id="nome-cartao-excluir"></strong>?
                <br><br>
                <span class="text-rose-600 font-semibold">Atenção:</span> Todas as faturas, lançamentos e históricos vinculados a este cartão serão <strong class="text-rose-600">permanentemente apagados</strong>.
            </p>
        </div>
        <input type="hidden" id="card-id-delete">
        <div class="flex items-center justify-center gap-3 pt-2">
            <button onclick="window.fecharModalExclusaoCartao()" class="w-full py-2.5 px-4 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-xl transition border border-slate-200">
                Cancelar
            </button>
            <button id="btn-confirmar-deletar-cartao" onclick="window.executarExclusaoCartao()" class="w-full py-2.5 px-4 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition shadow-sm">
                Sim, excluir tudo
            </button>
        </div>
    </div>
</div>

```

### Lógica JavaScript

Arquivo: `frontend/src/pages/cards/cards.js`

Implementar os manipuladores de evento para o modal e integração com a API:

```javascript
let cartaoIdParaExcluir = null;

window.abrirModalExclusaoCartao = (id, nomeCartao) => {
    cartaoIdParaExcluir = id;
    const nomeEl = document.getElementById('nome-cartao-excluir');
    if (nomeEl) nomeEl.textContent = nomeCartao;
    document.getElementById('modal-confirmar-exclusao-cartao')?.classList.remove('hidden');
};

window.fecharModalExclusaoCartao = () => {
    cartaoIdParaExcluir = null;
    document.getElementById('modal-confirmar-exclusao-cartao')?.classList.add('hidden');
};

window.executarExclusaoCartao = async () => {
    if (!cartaoIdParaExcluir) return;
    const btn = document.getElementById('btn-confirmar-deletar-cartao');
    
    try {
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Excluindo...';
        }
        await apiRequest(`/invoices/cards/${cartaoIdParaExcluir}`, 'DELETE');
        window.fecharModalExclusaoCartao();
        await carregarCartoes(); // Recarrega a grade de cartões
    } catch (err) {
        alert(`Erro ao excluir cartão: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Sim, excluir tudo';
        }
    }
};

```

## 4. Roteiro de Implementação

### Backend

- Implementar `deletar_cartao_e_dependencias` em `backend/app/modules/invoices/repository.py`.
- Adicionar `excluir_cartao` em `backend/app/modules/invoices/service.py`.
- Adicionar o endpoint `DELETE /api/v1/invoices/cards/{card_id}` em `backend/app/modules/invoices/router.py`.

### Frontend

- Adicionar o HTML do modal em `frontend/src/pages/cards/cards.html`.
- Atualizar a renderização dos cards em `frontend/src/pages/cards/cards.js` para incluir o botão de exclusão.
- Adicionar as funções `abrirModalExclusaoCartao`, `fecharModalExclusaoCartao` e `executarExclusaoCartao` em `frontend/src/pages/cards/cards.js`.

### Validação

- Criar ou identificar um cartão de teste no painel.
- Confirmar a exclusão pelo modal.
- Verificar se o cartão sumiu da tela.
- Verificar se as faturas, transações e vínculos correspondentes foram removidos do Supabase.