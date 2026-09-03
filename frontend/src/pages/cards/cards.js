import { apiRequest } from '../../core/api.js';
import { renderHeader } from '../../components/header.js';

let cartoesEncontradosPluggy = [];

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
            container.innerHTML = '<p class="text-slate-400 text-sm py-10 col-span-full text-center">Nenhum cartão cadastrado.</p>';
            return;
        }

        container.innerHTML = cartoes.map(card => {
            const isInter = card.bank_name?.toLowerCase().includes('inter');
            const isSantander = card.bank_name?.toLowerCase().includes('santander');
            const badgeCor = isInter ? 'bg-orange-50 text-orange-600 border-orange-200' : isSantander ? 'bg-red-50 text-red-600 border-red-200' : 'bg-slate-100 text-slate-600 border-slate-200';

            return `
                <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                        <div class="flex items-center gap-2 min-w-0 pr-2">
                            <span class="text-xs px-2 py-0.5 rounded border font-semibold ${badgeCor}">${card.bank_name}</span>
                            <h3 class="font-bold text-slate-800 text-base truncate">${card.card_name}</h3>
                        </div>
                        <button onclick="window.abrirModalEdicao('${card.id}', '${card.card_name}', '${card.bank_name}')" class="p-1.5 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition" title="Editar Cartão">
                            <span class="material-symbols-outlined text-base">edit</span>
                        </button>
                    </div>

                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between py-1 border-b border-slate-50">
                            <span class="text-slate-400 font-medium">ID do Cartão:</span>
                            <span class="font-mono text-slate-700 font-semibold">${card.id}</span>
                        </div>
                        <div class="flex justify-between py-1 border-b border-slate-50">
                            <span class="text-slate-400 font-medium">Banco Conector:</span>
                            <span class="font-semibold text-slate-700">${card.bank_name}</span>
                        </div>
                        <div class="flex justify-between py-1 border-b border-slate-50">
                            <span class="text-slate-400 font-medium">Pluggy Account ID:</span>
                            <span class="font-mono text-slate-500 truncate max-w-[180px]" title="${card.pluggy_account_id || 'N/A'}">${card.pluggy_account_id || 'N/A'}</span>
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

// Funções de Edição
window.abrirModalEdicao = (id, nomeCartao, nomeBanco) => {
    document.getElementById('card-id-edit').value = id;
    document.getElementById('card-name-input').value = nomeCartao;
    document.getElementById('bank-name-input').value = nomeBanco;
    document.getElementById('modal-editar-cartao')?.classList.remove('hidden');
};

window.fecharModalEdicao = () => {
    document.getElementById('modal-editar-cartao')?.classList.add('hidden');
};

window.salvarDadosCartao = async () => {
    const id = document.getElementById('card-id-edit').value;
    const cardName = document.getElementById('card-name-input').value.trim();
    const bankName = document.getElementById('bank-name-input').value.trim();

    if (!cardName || !bankName) {
        alert('Preencha o nome do cartão e do banco.');
        return;
    }

    try {
        await apiRequest(`/invoices/cards/${id}`, 'PATCH', { card_name: cardName, bank_name: bankName });
        window.fecharModalEdicao();
        await carregarCartoes();
    } catch (err) {
        alert(`Erro ao salvar: ${err.message}`);
    }
};

// Funções de Criação
window.abrirModalNovoCartao = () => {
    document.getElementById('input-item-id').value = '';
    window.voltarParaPasso1();
    document.getElementById('modal-novo-cartao')?.classList.remove('hidden');
};

window.fecharModalNovoCartao = () => {
    document.getElementById('modal-novo-cartao')?.classList.add('hidden');
};

window.voltarParaPasso1 = () => {
    document.getElementById('passo-1-item-id')?.classList.remove('hidden');
    document.getElementById('passo-2-selecao-cartao')?.classList.add('hidden');
};

// Passo 1: Busca na API da Pluggy via Backend
window.buscarCartoesDoItem = async () => {
    const itemId = document.getElementById('input-item-id').value.trim();
    const btn = document.getElementById('btn-buscar-cartoes');

    if (!itemId) {
        alert('Por favor, informe o Pluggy Item ID.');
        return;
    }

    try {
        btn.disabled = true;
        btn.innerText = 'Consultando Pluggy...';

        cartoesEncontradosPluggy = await apiRequest(`/invoices/pluggy/accounts/${encodeURIComponent(itemId)}`);

        if (!cartoesEncontradosPluggy || cartoesEncontradosPluggy.length === 0) {
            alert('Nenhum cartão de crédito foi encontrado para este Item ID.');
            return;
        }

        const select = document.getElementById('select-cartao-encontrado');
        select.innerHTML = cartoesEncontradosPluggy.map((c, index) => `
            <option value="${index}">${c.name} (${c.number})</option>
        `).join('');

        const primeiro = cartoesEncontradosPluggy[0];
        document.getElementById('new-bank-name').value = primeiro.bank_name || 'Banco';
        document.getElementById('new-card-name').value = primeiro.name;

        select.onchange = (e) => {
            const selecionado = cartoesEncontradosPluggy[e.target.value];
            if (selecionado) {
                document.getElementById('new-bank-name').value = selecionado.bank_name || 'Banco';
                document.getElementById('new-card-name').value = selecionado.name;
            }
        };

        document.getElementById('passo-1-item-id').classList.add('hidden');
        document.getElementById('passo-2-selecao-cartao').classList.remove('hidden');

    } catch (err) {
        alert(`Falha ao buscar cartões: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined text-base">search</span> Buscar Cartões Vinculados';
    }
};

// Passo 2: Salva no Supabase
window.criarNovoCartao = async () => {
    const itemId = document.getElementById('input-item-id').value.trim();
    const selectIndex = document.getElementById('select-cartao-encontrado').value;
    const cartaoSelecionado = cartoesEncontradosPluggy[selectIndex];

    const bankName = document.getElementById('new-bank-name').value.trim();
    const cardName = document.getElementById('new-card-name').value.trim();

    if (!cartaoSelecionado || !bankName || !cardName) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
    }

    try {
        await apiRequest('/invoices/cards', 'POST', {
            bank_name: bankName,
            card_name: cardName,
            pluggy_item_id: itemId,
            pluggy_account_id: cartaoSelecionado.pluggy_account_id
        });

        window.fecharModalNovoCartao();
        await carregarCartoes();
    } catch (err) {
        alert(`Erro ao cadastrar cartão: ${err.message}`);
    }
};

document.addEventListener('DOMContentLoaded', init);