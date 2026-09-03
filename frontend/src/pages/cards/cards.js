import { apiRequest } from '../../core/api.js';
import { renderHeader } from '../../components/header.js';

async function init() {
    await renderHeader('cards');
    await carregarCartoes();
}

async function carregarCartoes() {
    const container = document.getElementById('lista-cartoes-gerenciamento');
    if (!container) return;

    try {
        const cartoes = await apiRequest('/invoices/cards');

        if (!cartoes || cartoes.length === 0) {
            container.innerHTML = '<p class="text-slate-400 text-sm py-10 col-span-full text-center">Nenhum cartão cadastrado no momento.</p>';
            return;
        }

        container.innerHTML = cartoes.map(card => {
            const isInter = card.bank_name.toLowerCase().includes('inter');
            const isSantander = card.bank_name.toLowerCase().includes('santander');
            const badgeCor = isInter ? 'bg-orange-50 text-orange-600 border-orange-200' : isSantander ? 'bg-red-50 text-red-600 border-red-200' : 'bg-slate-100 text-slate-600 border-slate-200';

            return `
                <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                        <div class="flex items-center gap-2 min-w-0 pr-2">
                            <span class="text-xs px-2 py-0.5 rounded border font-semibold ${badgeCor}">Cartão</span>
                            <h3 class="font-bold text-slate-800 text-base truncate">${card.bank_name}</h3>
                        </div>
                        <button onclick="window.abrirModalEdicao('${card.id}', '${card.bank_name}')" class="p-1.5 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition" title="Alterar Nome">
                            <span class="material-symbols-outlined text-base">edit</span>
                        </button>
                    </div>

                    <!-- Dados Imutáveis -->
                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between py-1 border-b border-slate-50">
                            <span class="text-slate-400 font-medium">ID Interno:</span>
                            <span class="font-mono text-slate-700 font-semibold">${card.id}</span>
                        </div>
                        <div class="flex justify-between py-1 border-b border-slate-50">
                            <span class="text-slate-400 font-medium">Pluggy Account ID:</span>
                            <span class="font-mono text-slate-500 truncate max-w-[200px]" title="${card.pluggy_account_id || 'N/A'}">${card.pluggy_account_id || 'N/A'}</span>
                        </div>
                        <div class="flex justify-between py-1 border-b border-slate-50">
                            <span class="text-slate-400 font-medium">Item ID (Conector):</span>
                            <span class="font-mono text-slate-500">${card.item_id || 'N/A'}</span>
                        </div>
                        <div class="flex justify-between py-1">
                            <span class="text-slate-400 font-medium">Data de Cadastro:</span>
                            <span class="text-slate-600">${card.created_at ? new Date(card.created_at).toLocaleDateString('pt-BR') : 'Desconhecida'}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Erro ao carregar cartões:', err);
        container.innerHTML = `<p class="text-rose-500 text-sm py-10 col-span-full text-center">Falha ao carregar dados: ${err.message}</p>`;
    }
}

window.abrirModalEdicao = (id, nomeAtual) => {
    document.getElementById('card-id-edit').value = id;
    document.getElementById('card-name-input').value = nomeAtual;
    document.getElementById('modal-editar-cartao')?.classList.remove('hidden');
};

window.fecharModalEdicao = () => {
    document.getElementById('modal-editar-cartao')?.classList.add('hidden');
};

window.salvarNomeCartao = async () => {
    const id = document.getElementById('card-id-edit').value;
    const novoNome = document.getElementById('card-name-input').value.trim();

    if (!novoNome) {
        alert('Por favor, informe um nome válido.');
        return;
    }

    try {
        await apiRequest(`/invoices/cards/${id}`, 'PATCH', { bank_name: novoNome });
        window.fecharModalEdicao();
        await carregarCartoes(); // Atualiza a lista na tela
    } catch (err) {
        console.error('Erro ao renomear cartão:', err);
        alert(`Erro ao salvar: ${err.message}`);
    }
};

document.addEventListener('DOMContentLoaded', init);