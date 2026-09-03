import { apiRequest } from '../../core/api.js';
import { renderHeader } from '../../components/header.js';
import { renderChart } from '../../components/charts.js';

const USER_ID = 'd262bc6c-d58b-4f4e-99b4-505202b646ba';
let resumoCategoriasAtuais = [];
let bancoFiltro = ''; // <-- Declaração da variável no escopo do módulo

async function init() {
    // 1. Lê parâmetro 'banco' da URL (ex: ?banco=Santander)
    const urlParams = new URLSearchParams(window.location.search);
    bancoFiltro = urlParams.get('banco') || '';

    // 2. Renderiza Topbar dinâmica (aguarda a busca dos cartões)
    await renderHeader('invoices');

    // 3. Atualiza o título da página
    const tituloEl = document.getElementById('titulo-pagina-fatura');
    if (tituloEl) {
        tituloEl.textContent = bancoFiltro ? `Fatura ${bancoFiltro}` : 'Total Cartões';
    }

    await carregarOpcoesMeses();
    await carregarDados();

    document.getElementById('filtro-mes')?.addEventListener('change', carregarDados);
}

async function carregarOpcoesMeses() {
    try {
        const faturas = await apiRequest(`/invoices/bills?user_id=${USER_ID}`);
        const select = document.getElementById('filtro-mes');
        if (!select) return;

        const mesesSet = new Set(faturas.map(f => f.due_date ? f.due_date.slice(0, 7) : ''));
        const mesesOrdenados = Array.from(mesesSet).filter(Boolean).sort().reverse();

        select.innerHTML = '<option value="">Todas as Faturas</option>';
        mesesOrdenados.forEach(mes => {
            const [ano, num] = mes.split('-');
            const dataData = new Date(Number(ano), Number(num) - 1, 1);
            const nomeMes = dataData.toLocaleString('pt-BR', { month: 'long' });
            const nomeFormatado = nomeMes.charAt(0).toUpperCase() + nomeMes.slice(1);

            const opt = document.createElement('option');
            opt.value = mes;
            opt.textContent = `${nomeFormatado} ${ano}`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Erro ao carregar faturas:', err);
    }
}

async function carregarDados() {
    const selectMes = document.getElementById('filtro-mes');
    const mesSelecionado = selectMes ? selectMes.value : '';

    try {
        let transacoes = await apiRequest(`/invoices/transactions?user_id=${USER_ID}`);

        // Filtro por Mês
        if (mesSelecionado) {
            transacoes = transacoes.filter(tx => tx.date && tx.date.startsWith(mesSelecionado));
        }

        // Filtro por Banco
        if (bancoFiltro) {
            transacoes = transacoes.filter(tx => 
                tx.bank_name && tx.bank_name.toLowerCase().includes(bancoFiltro.toLowerCase())
            );
        }

        renderTransacoes(transacoes);

        const resumo = await apiRequest(`/invoices/categories-summary?user_id=${USER_ID}`);
        
        // Recalcula o total conforme os filtros aplicados
        const totalCalculado = transacoes
            .filter(tx => tx.category_id !== "05100000" && !tx.is_ignored)
            .reduce((acc, tx) => acc + tx.amount, 0);

        const valorEl = document.getElementById('valor-total');
        if (valorEl) {
            valorEl.innerText = Number(totalCalculado).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        }

        resumoCategoriasAtuais = resumo.categories || [];
        renderChart('chartCategorias', resumoCategoriasAtuais);

    } catch (err) {
        console.error('Erro ao carregar dados:', err);
    }
}

function renderTransacoes(transacoes) {
    const container = document.getElementById('lista-transacoes');
    const contador = document.getElementById('contador-itens');
    if (!container) return;

    if (contador) contador.innerText = `${transacoes.length} itens`;

    if (!transacoes || transacoes.length === 0) {
        container.innerHTML = '<p class="text-center text-slate-400 text-xs py-10">Nenhum lançamento encontrado.</p>';
        return;
    }

    container.innerHTML = transacoes.map(tx => {
        const banco = tx.bank_name || 'Cartão';
        const isInter = banco.toLowerCase().includes('inter');
        const isSantander = banco.toLowerCase().includes('santander');
        
        const bancoBadgeClass = isInter 
            ? 'bg-orange-50 text-orange-600 border-orange-200' 
            : isSantander 
                ? 'bg-red-50 text-red-600 border-red-200' 
                : 'bg-slate-100 text-slate-600 border-slate-200';

        return `
            <div class="p-3 border-b border-slate-100 flex justify-between items-center ${tx.is_ignored ? 'opacity-40 bg-slate-50' : ''}">
                <div class="flex items-center gap-3 min-w-0 pr-2">
                    <button onclick="window.toggleIgnore('${tx.id}', ${!tx.is_ignored})" class="text-slate-400 hover:text-slate-600 shrink-0" title="${tx.is_ignored ? 'Reincluir' : 'Desconsiderar'}">
                        <span class="material-symbols-outlined text-base">${tx.is_ignored ? 'visibility_off' : 'visibility'}</span>
                    </button>
                    <div class="truncate">
                        <p class="text-sm font-medium ${tx.is_ignored ? 'line-through' : ''} truncate">${tx.description}</p>
                        <div class="flex items-center gap-1.5 mt-0.5">
                            <span class="text-[9px] px-1.5 py-0.2 rounded border font-semibold ${bancoBadgeClass}">${banco}</span>
                            <span class="text-[10px] text-slate-400"><span style="color:${tx.category_color}">●</span> ${tx.category_name}</span>
                        </div>
                    </div>
                </div>
                <span class="font-semibold text-sm whitespace-nowrap">R$ ${Number(tx.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
            </div>
        `;
    }).join('');
}

window.abrirModalCategoria = () => {
    const modal = document.getElementById('modal-categoria');
    const lista = document.getElementById('modal-categoria-lista');

    if (!resumoCategoriasAtuais || resumoCategoriasAtuais.length === 0) {
        lista.innerHTML = '<p class="text-center text-slate-400 text-xs py-6">Nenhuma categoria registrada.</p>';
    } else {
        lista.innerHTML = resumoCategoriasAtuais.map(cat => {
            const totalFmt = Number(cat.total_amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
            const pctFmt = Number(cat.percentage).toFixed(1);
            const txs = cat.transactions || [];

            return `
                <div class="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 space-y-2">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-200/60">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full shrink-0" style="background-color: ${cat.category_color}"></span>
                            <span class="font-bold text-xs text-slate-800">${cat.category_name}</span>
                            <span class="text-[10px] text-slate-400 font-medium">(${pctFmt}%)</span>
                        </div>
                        <span class="font-bold text-xs text-slate-700">R$ ${totalFmt}</span>
                    </div>

                    <div class="space-y-1.5">
                        ${txs.length === 0 ? '<p class="text-slate-400 text-[11px]">Sem lançamentos.</p>' : txs.map(tx => `
                            <div class="pt-1 flex justify-between items-center text-xs ${tx.is_ignored ? 'opacity-40' : ''}">
                                <div class="flex items-center gap-2 pr-2 min-w-0">
                                    <button onclick="window.toggleIgnore('${tx.id}', ${!tx.is_ignored}, true)" class="text-slate-400 hover:text-slate-600 shrink-0" title="${tx.is_ignored ? 'Reincluir' : 'Desconsiderar'}">
                                        <span class="material-symbols-outlined text-base">${tx.is_ignored ? 'visibility_off' : 'visibility'}</span>
                                    </button>
                                    <div class="truncate">
                                        <p class="font-medium text-slate-800 ${tx.is_ignored ? 'line-through' : ''} truncate">${tx.description}</p>
                                        <p class="text-[10px] text-slate-400">${new Date(tx.date).toLocaleDateString('pt-BR')} • ${tx.bank_name}</p>
                                    </div>
                                </div>
                                <span class="font-semibold ${tx.amount < 0 ? 'text-emerald-600' : 'text-slate-700'} shrink-0">
                                    R$ ${Number(tx.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }

    modal?.classList.remove('hidden');
};

window.fecharModalCategoria = () => {
    document.getElementById('modal-categoria')?.classList.add('hidden');
};

window.toggleIgnore = async (id, isIgnored, fromModal = false) => {
    try {
        await apiRequest(`/invoices/transactions/${id}/ignore?is_ignored=${isIgnored}`, 'PATCH');
        await carregarDados();
        
        if (fromModal) {
            window.abrirModalCategoria();
        }
    } catch (err) {
        console.error('Erro ao alternar transação:', err);
    }
};

document.addEventListener('DOMContentLoaded', init);