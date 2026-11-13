import { apiRequest } from '../../core/api.js';
import { renderHeader } from '../../components/header.js';

// ============================================================================
// Estado
// ============================================================================

let pessoaAtual = null;              // { id, name, ... }
let lancamentoManualEmEdicao = null; // ID do manual_debt em edição (null = criação)
let mesesFatura = [];               // meses com card_splits da pessoa atual
let mesFaturaSelecionado = '';      // mês YYYY-MM selecionado no drawer
let compraSelecionada = null;       // transação selecionada no modal de compra

const mesAtual = new Date().toISOString().slice(0, 7); // YYYY-MM

// ============================================================================
// Utilitários
// ============================================================================

const fmt = (v) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v) || 0);

function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatarData(d) {
    if (!d) return '';
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return '';
    const temHora = typeof d === 'string' && /T|\s\d{2}:/.test(d);
    return temHora
        ? dt.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
        : dt.toLocaleDateString('pt-BR');
}

function bancoBadgeClass(bank) {
    const b = (bank || '').toLowerCase();
    if (b.includes('inter'))     return 'bg-orange-50 text-orange-700 border-orange-200';
    if (b.includes('santander')) return 'bg-red-50 text-red-700 border-red-200';
    return 'bg-slate-100 text-slate-600 border-slate-200';
}

function nomeMesFormatado(yyyymm) {
    const [ano, num] = yyyymm.split('-');
    const d = new Date(Number(ano), Number(num) - 1, 1);
    const nome = d.toLocaleString('pt-BR', { month: 'long' });
    return nome.charAt(0).toUpperCase() + nome.slice(1) + ' ' + ano;
}

// ============================================================================
// Confirmação genérica
// ============================================================================

function confirmar(titulo, mensagem) {
    return new Promise((resolve) => {
        const modal    = document.getElementById('confirm-modal');
        const titleEl  = document.getElementById('confirm-title');
        const msgEl    = document.getElementById('confirm-message');
        const okBtn    = document.getElementById('confirm-ok');
        const cancelBtn = document.getElementById('confirm-cancel');

        titleEl.textContent = titulo;
        msgEl.textContent   = mensagem;
        modal.classList.remove('hidden');
        modal.classList.add('flex');

        function fechar(res) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            resolve(res);
        }
        const onOk     = () => fechar(true);
        const onCancel = () => fechar(false);
        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
    });
}

// ============================================================================
// Grid de pessoas
// ============================================================================

async function carregarPessoas() {
    const grid = document.getElementById('receivable-grid');
    grid.innerHTML = '<div class="col-span-full text-center py-8 text-slate-500"><p>Carregando pessoas...</p></div>';

    try {
        const pessoas = await apiRequest(`/receivables/summary?mes=${mesAtual}`);

        if (!pessoas || pessoas.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12 border-2 border-dashed border-slate-300 rounded-xl">
                    <p class="text-slate-500">Nenhuma pessoa cadastrada ainda.</p>
                    <p class="text-slate-400 text-sm mt-1">Clique em <strong>Adicionar Pessoa</strong> para começar.</p>
                </div>`;
            return;
        }

        grid.innerHTML = pessoas.map((p) => `
            <button
                onclick="window.abrirPessoa('${escHtml(p.id)}')"
                class="card-financeiro p-5 text-left hover:shadow-md hover:-translate-y-0.5 transition-all duration-150 flex flex-col gap-2 w-full"
            >
                <p class="font-semibold text-slate-800 text-base">${escHtml(p.name)}</p>
                <div class="flex flex-col gap-1 mt-1">
                    <div class="flex justify-between items-center text-sm">
                        <span class="text-slate-500">Cartão · Fatura atual</span>
                        <span class="font-semibold text-sky-700">${fmt(p.card_total)}</span>
                    </div>
                    <div class="flex justify-between items-center text-sm">
                        <span class="text-slate-500">Saldo Devedor</span>
                        <span class="font-semibold text-amber-700">${fmt(p.manual_total)}</span>
                    </div>
                </div>
            </button>`).join('');
    } catch (err) {
        grid.innerHTML = `<div class="col-span-full text-center py-8 text-rose-600"><p>Erro ao carregar pessoas: ${escHtml(err.message)}</p></div>`;
    }
}

// ============================================================================
// Drawer — abrir / fechar
// ============================================================================

window.abrirPessoa = async function (id) {
    pessoaAtual = { id };
    mesFaturaSelecionado = mesAtual;

    const drawer   = document.getElementById('person-drawer');
    const nameEl   = document.getElementById('person-drawer-name');
    const monthSel = document.getElementById('person-month');

    nameEl.textContent = 'Carregando...';
    drawer.classList.remove('translate-x-full');

    document.getElementById('card-splits-list').innerHTML  = '<p class="text-slate-400 text-sm">Carregando extratos...</p>';
    document.getElementById('manual-debts-list').innerHTML = '';
    document.getElementById('card-total').textContent      = 'R$ 0,00';
    document.getElementById('manual-total').textContent    = 'R$ 0,00';

    try {
        const mesesData = await apiRequest(`/receivables/people/${id}/card-months`);
        mesesFatura = mesesData.months || [];

        if (mesesFatura.includes(mesAtual)) {
            mesFaturaSelecionado = mesAtual;
        } else if (mesesFatura.length > 0) {
            mesFaturaSelecionado = mesesFatura[0];
        } else {
            mesFaturaSelecionado = mesAtual;
        }

        const mesesOpcoes = Array.from(new Set([mesAtual, ...mesesFatura])).sort().reverse();
        monthSel.innerHTML = mesesOpcoes.map((m) =>
            `<option value="${m}" ${m === mesFaturaSelecionado ? 'selected' : ''}>${nomeMesFormatado(m)}</option>`
        ).join('');

        await renderizarPessoa();
    } catch (err) {
        document.getElementById('card-splits-list').innerHTML =
            `<p class="text-rose-600 text-sm">Erro: ${escHtml(err.message)}</p>`;
    }
};

function fecharPessoa() {
    document.getElementById('person-drawer').classList.add('translate-x-full');
    pessoaAtual = null;
}

// ============================================================================
// Renderização dos detalhes
// ============================================================================

async function renderizarPessoa() {
    if (!pessoaAtual) return;

    try {
        const data = await apiRequest(
            `/receivables/people/${pessoaAtual.id}?mes=${mesFaturaSelecionado}`
        );

        pessoaAtual = { ...pessoaAtual, ...data };
        document.getElementById('person-drawer-name').textContent = data.name;
        document.getElementById('card-total').textContent         = fmt(data.card_total);
        document.getElementById('manual-total').textContent       = fmt(data.manual_total);

        renderizarCardSplits(data.card_splits || []);
        renderizarManualDebts(data.manual_debts || []);
    } catch (err) {
        document.getElementById('card-splits-list').innerHTML =
            `<p class="text-rose-600 text-sm">Erro: ${escHtml(err.message)}</p>`;
    }
}

function renderizarCardSplits(splits) {
    const lista = document.getElementById('card-splits-list');
    if (!splits.length) {
        lista.innerHTML = '<p class="text-slate-400 text-sm">Nenhuma compra vinculada neste mês.</p>';
        return;
    }

    lista.innerHTML = splits.map((s) => {
        const isIntegral = s.is_integral;
        const tipoBadge  = isIntegral
            ? 'bg-green-100 text-green-700 border-green-200'
            : 'bg-amber-100 text-amber-700 border-amber-200';
        const tipoLabel  = isIntegral ? 'Integral' : 'Parcial';
        const bankClass  = bancoBadgeClass(s.bank);

        return `
        <article class="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
            <div class="flex items-center justify-between gap-2 mb-1">
                <div class="flex items-center gap-1.5 flex-wrap">
                    <span class="text-[9px] px-1.5 py-0.5 rounded border font-semibold ${bankClass}">${escHtml(s.bank)}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded border font-semibold ${tipoBadge}">${tipoLabel}</span>
                </div>
                <div class="relative">
                    <button
                        onclick="window.toggleSplitMenu('${s.id}')"
                        class="p-1 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <span class="material-symbols-outlined text-slate-500 text-base">settings</span>
                    </button>
                    <div id="split-menu-${s.id}" class="hidden absolute right-0 top-7 z-10 bg-white border border-slate-200 rounded-lg shadow-lg py-1 min-w-[160px]">
                        <button
                            onclick="window.editarSplit('${s.id}', ${s.amount_person}, ${s.total_transaction_amount}, ${s.is_integral})"
                            class="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 text-slate-700"
                        >Editar valor</button>
                        <button
                            onclick="window.excluirSplit('${s.id}')"
                            class="w-full text-left px-4 py-2 text-sm hover:bg-rose-50 text-rose-600"
                        >Excluir vínculo</button>
                    </div>
                </div>
            </div>
            <p class="font-semibold text-sky-700">${fmt(s.amount_person)}</p>
            ${!isIntegral ? `<p class="text-xs text-slate-500">Total original: ${fmt(s.total_transaction_amount)}</p>` : ''}
            <p class="text-sm text-slate-700 mt-0.5">${escHtml(s.description)}</p>
            <p class="text-xs text-slate-400 mt-0.5">${formatarData(s.date)}</p>
        </article>`;
    }).join('');
}

window.toggleSplitMenu = function (id) {
    const menu = document.getElementById(`split-menu-${id}`);
    if (!menu) return;
    document.querySelectorAll('[id^="split-menu-"], [id^="debt-menu-"]').forEach((m) => {
        if (m.id !== `split-menu-${id}`) m.classList.add('hidden');
    });
    menu.classList.toggle('hidden');
};

function renderizarManualDebts(debts) {
    const lista = document.getElementById('manual-debts-list');
    if (!debts.length) {
        lista.innerHTML = '<p class="text-slate-400 text-sm">Nenhum lançamento manual registrado.</p>';
        return;
    }

    lista.innerHTML = debts.map((d) => {
        const isCharge = d.type === 'charge';
        const sinal    = isCharge ? '+' : '-';
        const corValor = isCharge ? 'text-sky-700' : 'text-green-700';

        return `
        <div class="flex items-start justify-between gap-2 p-3 border border-slate-200 rounded-xl bg-white shadow-sm">
            <div class="min-w-0">
                <p class="font-semibold ${corValor} text-sm">${sinal} ${fmt(d.amount)}</p>
                ${d.description ? `<p class="text-sm text-slate-700 truncate">${escHtml(d.description)}</p>` : ''}
                <p class="text-xs text-slate-400 mt-0.5">${formatarData(d.occurred_at)}</p>
            </div>
            <div class="relative shrink-0">
                <button
                    onclick="window.toggleDebtMenu('${d.id}')"
                    class="p-1 hover:bg-slate-100 rounded-lg transition-colors"
                >
                    <span class="material-symbols-outlined text-slate-500 text-base">settings</span>
                </button>
                <div id="debt-menu-${d.id}" class="hidden absolute right-0 top-7 z-10 bg-white border border-slate-200 rounded-lg shadow-lg py-1 min-w-[180px]">
                    <button
                        onclick="window.editarManual('${d.id}', '${d.type}', ${d.amount}, '${escHtml(d.description || '')}')"
                        class="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 text-slate-700"
                    >Editar informações</button>
                    <button
                        onclick="window.excluirManual('${d.id}')"
                        class="w-full text-left px-4 py-2 text-sm hover:bg-rose-50 text-rose-600"
                    >Excluir lançamento</button>
                </div>
            </div>
        </div>`;
    }).join('');
}

window.toggleDebtMenu = function (id) {
    const menu = document.getElementById(`debt-menu-${id}`);
    if (!menu) return;
    document.querySelectorAll('[id^="split-menu-"], [id^="debt-menu-"]').forEach((m) => {
        if (m.id !== `debt-menu-${id}`) m.classList.add('hidden');
    });
    menu.classList.toggle('hidden');
};

// Fecha menus ao clicar fora
document.addEventListener('click', (e) => {
    if (!e.target.closest('[id^="split-menu-"],[id^="debt-menu-"],[onclick*="toggleSplitMenu"],[onclick*="toggleDebtMenu"]')) {
        document.querySelectorAll('[id^="split-menu-"],[id^="debt-menu-"]').forEach((m) => m.classList.add('hidden'));
    }
});

// ============================================================================
// Modal: Nova Pessoa
// ============================================================================

function abrirModalPessoa() {
    const modal = document.getElementById('person-modal');
    const input = document.getElementById('new-person-name');
    input.value = '';
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => input.focus(), 50);
}

function fecharModalPessoa() {
    const modal = document.getElementById('person-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function cadastrarPessoa() {
    const input = document.getElementById('new-person-name');
    const nome  = input.value.trim();
    if (!nome) { input.focus(); return; }

    try {
        await apiRequest('/receivables/people', 'POST', { name: nome });
        fecharModalPessoa();
        await carregarPessoas();
    } catch (err) {
        alert(`Erro ao cadastrar: ${err.message}`);
    }
}

// ============================================================================
// Modal: Lançamento Manual
// ============================================================================

function abrirManual(tipo) {
    lancamentoManualEmEdicao = null;
    const titulos = { charge: 'Adicionar Cobrança', payment: 'Registrar Pagamento' };

    document.getElementById('manual-modal-title').textContent    = titulos[tipo] || 'Lançamento';
    document.getElementById('manual-type').value                 = tipo;
    document.getElementById('manual-amount').value               = '';
    document.getElementById('manual-description').value          = '';

    const modal = document.getElementById('manual-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => document.getElementById('manual-amount').focus(), 50);
}

window.editarManual = function (id, tipo, valor, descricao) {
    document.getElementById(`debt-menu-${id}`)?.classList.add('hidden');

    lancamentoManualEmEdicao = id;
    document.getElementById('manual-modal-title').textContent = 'Editar Informações';
    document.getElementById('manual-type').value              = tipo;
    document.getElementById('manual-amount').value            = valor;
    document.getElementById('manual-description').value       = descricao;

    const modal = document.getElementById('manual-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => document.getElementById('manual-amount').focus(), 50);
};

function fecharManualModal() {
    document.getElementById('manual-modal').classList.add('hidden');
    document.getElementById('manual-modal').classList.remove('flex');
    lancamentoManualEmEdicao = null;
}

async function confirmarManual() {
    const tipo   = document.getElementById('manual-type').value;
    const amount = parseFloat(document.getElementById('manual-amount').value);
    const desc   = document.getElementById('manual-description').value.trim();

    if (!amount || amount <= 0) {
        alert('Informe um valor maior que zero.');
        return;
    }

    try {
        if (lancamentoManualEmEdicao) {
            await apiRequest(`/receivables/manual/${lancamentoManualEmEdicao}`, 'PUT', {
                type: tipo,
                amount,
                description: desc || null,
            });
        } else {
            await apiRequest('/receivables/manual', 'POST', {
                person_id:   pessoaAtual.id,
                type:        tipo,
                amount,
                description: desc || null,
            });
        }

        fecharManualModal();
        await renderizarPessoa();
        await carregarPessoas();
    } catch (err) {
        alert(`Erro: ${err.message}`);
    }
}

window.excluirManual = async function (id) {
    document.getElementById(`debt-menu-${id}`)?.classList.add('hidden');
    const ok = await confirmar('Excluir lançamento', 'Tem certeza que deseja excluir este lançamento?');
    if (!ok) return;

    try {
        await apiRequest(`/receivables/manual/${id}`, 'DELETE');
        await renderizarPessoa();
        await carregarPessoas();
    } catch (err) {
        alert(`Erro: ${err.message}`);
    }
};

// ============================================================================
// Modal: Vínculo de Compra
// ============================================================================

async function abrirCompras() {
    compraSelecionada = null;

    const modal = document.getElementById('card-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    document.getElementById('card-modal-title').textContent = 'Compras da Fatura';
    document.getElementById('card-search-section').classList.remove('hidden');
    document.getElementById('card-list-section').classList.remove('hidden');
    document.getElementById('card-split-section').classList.add('hidden');
    document.getElementById('card-list-actions').classList.remove('hidden');
    document.getElementById('card-purchase-search').value = '';

    document.querySelector('input[name="split-type"][value="integral"]').checked = true;
    document.getElementById('split-amount-section').classList.add('hidden');
    document.getElementById('split-amount').value = '';

    // Carregar opções de cartões
    await carregarOpcoesCartoes();
    await carregarCompras();
}

async function carregarOpcoesCartoes() {
    const select = document.getElementById('card-filter-select');
    if (!select) return;

    try {
        const cartoes = await apiRequest('/invoices/cards');
        let optionsHtml = '<option value="">Todos os cartões</option>';
        (cartoes || []).forEach(card => {
            const nome = card.name || 'Cartão';
            const banco = card.bank_name ? ` (${card.bank_name})` : '';
            optionsHtml += `<option value="${card.id}">${escHtml(nome + banco)}</option>`;
        });
        select.innerHTML = optionsHtml;
    } catch (err) {
        console.warn('Não foi possível carregar cartões:', err);
    }
}

async function carregarCompras() {
    const lista = document.getElementById('card-list-section');
    const busca = document.getElementById('card-purchase-search').value.trim();
    const cardId = document.getElementById('card-filter-select')?.value || '';
    lista.innerHTML = '<p class="text-center text-slate-400 text-sm py-4">Carregando compras...</p>';

    try {
        let url = `/receivables/people/${pessoaAtual.id}/card-transactions?mes=${mesFaturaSelecionado}`;
        if (busca) url += `&busca=${encodeURIComponent(busca)}`;
        if (cardId) url += `&card_id=${encodeURIComponent(cardId)}`;

        const transacoes = await apiRequest(url);

        if (!transacoes.length) {
            lista.innerHTML = '<p class="text-center text-slate-400 text-sm py-4">Nenhuma compra encontrada.</p>';
            return;
        }

        lista.innerHTML = transacoes.map((t) => {
            const disabled  = t.is_linked;
            const opacidade = disabled ? 'opacity-50' : 'hover:bg-slate-50 cursor-pointer';
            const badge     = t.is_linked
                ? '<span class="ml-auto text-xs text-slate-400 italic shrink-0">Já vinculada</span>'
                : '';

            const rotuloCartao = t.card_name && t.card_name !== t.bank ? ` • ${escHtml(t.card_name)}` : '';

            return `
            <div
                onclick="${!disabled ? `window.selecionarCompra('${t.id}', '${escHtml(t.description)}', ${t.amount}, '${t.date}', '${escHtml(t.bank)}')` : ''}"
                class="flex items-start gap-3 p-3 border border-slate-200 rounded-lg ${opacidade} transition-colors"
            >
                <div class="min-w-0 flex-1">
                    <p class="text-sm font-semibold text-slate-800 truncate">${escHtml(t.description)}</p>
                    <div class="flex items-center gap-2 mt-0.5">
                        <span class="text-[9px] px-1.5 py-0.5 rounded border font-semibold ${bancoBadgeClass(t.bank)}">${escHtml(t.bank)}</span>
                        <span class="text-xs text-slate-500">${formatarData(t.date)}${rotuloCartao}</span>
                    </div>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                    <span class="font-semibold text-sm text-slate-700">${fmt(t.amount)}</span>
                    ${badge}
                </div>
            </div>`;
        }).join('');
    } catch (err) {
        lista.innerHTML = `<p class="text-rose-600 text-sm py-4 text-center">${escHtml(err.message)}</p>`;
    }
}

window.selecionarCompra = function (id, descricao, valor, data, bank) {
    compraSelecionada = { id, descricao, valor, data, bank };

    document.getElementById('card-modal-title').textContent = 'Definir Divisão';
    document.getElementById('card-search-section').classList.add('hidden');
    document.getElementById('card-list-section').classList.add('hidden');
    document.getElementById('card-list-actions').classList.add('hidden');
    document.getElementById('card-split-section').classList.remove('hidden');

    document.getElementById('card-split-description').textContent = descricao;
    document.getElementById('card-split-value').textContent       = `Valor total: ${fmt(valor)}`;
    document.getElementById('card-split-date').textContent        = formatarData(data);

    document.querySelector('input[name="split-type"][value="integral"]').checked = true;
    document.getElementById('split-amount-section').classList.add('hidden');
    document.getElementById('split-amount').value = '';
};

function voltarListaCompras() {
    compraSelecionada = null;
    document.getElementById('card-modal-title').textContent = 'Compras da Fatura';
    document.getElementById('card-search-section').classList.remove('hidden');
    document.getElementById('card-list-section').classList.remove('hidden');
    document.getElementById('card-list-actions').classList.remove('hidden');
    document.getElementById('card-split-section').classList.add('hidden');
}

function fecharCardModal() {
    const modal = document.getElementById('card-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    compraSelecionada = null;
    // Restaura estado inicial
    document.getElementById('card-search-section').classList.remove('hidden');
    document.getElementById('card-list-section').classList.remove('hidden');
    document.getElementById('card-list-actions').classList.remove('hidden');
    document.getElementById('card-split-section').classList.add('hidden');
}

async function confirmarSplit() {
    if (!compraSelecionada) return;

    const tipoSplit  = document.querySelector('input[name="split-type"]:checked').value;
    const isIntegral = tipoSplit === 'integral';
    let amountPerson = Number(compraSelecionada.valor);

    if (!isIntegral) {
        amountPerson = parseFloat(document.getElementById('split-amount').value);
        if (!amountPerson || amountPerson <= 0) {
            alert('Informe um valor maior que zero.');
            return;
        }
        if (amountPerson > Number(compraSelecionada.valor)) {
            alert('O valor da pessoa não pode exceder o valor total da compra.');
            return;
        }
    }

    // Se vem de edição via editarSplit, usa o split_id existente para identificar a transação
    const transactionId = compraSelecionada._splitId
        ? compraSelecionada._originalTransactionId
        : compraSelecionada.id;

    try {
        await apiRequest('/receivables/card-splits', 'POST', {
            transaction_id:           transactionId,
            person_id:                pessoaAtual.id,
            reference_month:          mesFaturaSelecionado,
            is_integral:              isIntegral,
            amount_person:            amountPerson,
            total_transaction_amount: Number(compraSelecionada.valor),
        });

        fecharCardModal();
        await renderizarPessoa();
        await carregarPessoas();
    } catch (err) {
        alert(`Erro: ${err.message}`);
    }
}

window.editarSplit = function (id, amountPerson, total, isIntegral) {
    document.getElementById(`split-menu-${id}`)?.classList.add('hidden');

    // Abre modal direto no formulário de divisão
    compraSelecionada = { id: null, valor: total, _splitId: id };

    document.getElementById('card-modal-title').textContent = 'Editar Divisão';
    document.getElementById('card-search-section').classList.add('hidden');
    document.getElementById('card-list-section').classList.add('hidden');
    document.getElementById('card-list-actions').classList.add('hidden');
    document.getElementById('card-split-section').classList.remove('hidden');

    document.getElementById('card-split-description').textContent = '';
    document.getElementById('card-split-value').textContent       = `Valor total: ${fmt(total)}`;
    document.getElementById('card-split-date').textContent        = '';

    if (isIntegral) {
        document.querySelector('input[name="split-type"][value="integral"]').checked = true;
        document.getElementById('split-amount-section').classList.add('hidden');
    } else {
        document.querySelector('input[name="split-type"][value="partial"]').checked = true;
        document.getElementById('split-amount-section').classList.remove('hidden');
        document.getElementById('split-amount').value = amountPerson;
    }

    const modal = document.getElementById('card-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
};

window.excluirSplit = async function (id) {
    document.getElementById(`split-menu-${id}`)?.classList.add('hidden');
    const ok = await confirmar('Excluir vínculo', 'Tem certeza que deseja remover este vínculo de compra?');
    if (!ok) return;

    try {
        await apiRequest(`/receivables/card-splits/${id}`, 'DELETE');
        await renderizarPessoa();
        await carregarPessoas();
    } catch (err) {
        alert(`Erro: ${err.message}`);
    }
};

// ============================================================================
// Inicialização e eventos
// ============================================================================

async function init() {
    await renderHeader('receivables');
    await carregarPessoas();

    // Cabeçalho
    document.getElementById('new-person-btn').addEventListener('click', abrirModalPessoa);

    // Modal nova pessoa
    document.getElementById('person-modal-confirm').addEventListener('click', cadastrarPessoa);
    document.querySelectorAll('.person-modal-cancel').forEach((btn) =>
        btn.addEventListener('click', fecharModalPessoa)
    );
    document.getElementById('new-person-name').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') cadastrarPessoa();
    });

    // Drawer — fechar
    document.getElementById('close-drawer-btn').addEventListener('click', fecharPessoa);

    // Drawer — seletor de mês
    document.getElementById('person-month').addEventListener('change', (e) => {
        mesFaturaSelecionado = e.target.value;
        renderizarPessoa();
    });

    // Drawer — vincular compra
    document.getElementById('card-search-btn').addEventListener('click', abrirCompras);

    // Drawer — lançamentos manuais
    document.getElementById('manual-charge-btn').addEventListener('click', () => abrirManual('charge'));
    document.getElementById('manual-payment-btn').addEventListener('click', () => abrirManual('payment'));

    // Modal manual
    document.getElementById('manual-modal-confirm').addEventListener('click', confirmarManual);
    document.querySelectorAll('.manual-modal-cancel').forEach((btn) =>
        btn.addEventListener('click', fecharManualModal)
    );

    // Modal card — filtro por cartão
    document.getElementById('card-filter-select')?.addEventListener('change', carregarCompras);

    // Modal card — busca ao digitar
    document.getElementById('card-purchase-search').addEventListener('input', carregarCompras);

    // Modal card — voltar
    document.getElementById('card-split-back').addEventListener('click', voltarListaCompras);

    // Modal card — confirmar split
    document.getElementById('card-split-confirm').addEventListener('click', confirmarSplit);

    // Modal card — cancelar
    document.querySelectorAll('.card-modal-cancel').forEach((btn) =>
        btn.addEventListener('click', fecharCardModal)
    );

    // Modal card — tipo de divisão
    document.querySelectorAll('input[name="split-type"]').forEach((radio) =>
        radio.addEventListener('change', (e) => {
            const secao = document.getElementById('split-amount-section');
            if (e.target.value === 'partial') {
                secao.classList.remove('hidden');
                document.getElementById('split-amount').focus();
            } else {
                secao.classList.add('hidden');
                document.getElementById('split-amount').value = '';
            }
        })
    );
}

document.addEventListener('DOMContentLoaded', init);
