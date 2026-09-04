import { apiRequest } from '../../core/api.js';
import { renderHeader } from '../../components/header.js';
import { renderPaymentHistoryChart } from '../../components/charts.js?v=2';

const USER_ID = 'd262bc6c-d58b-4f4e-99b4-505202b646ba';
let pagamentosAtuais = [];

function moeda(valor) {
    return Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function dataFormatada(data) {
    if (!data) return '';
    return new Date(`${data}T00:00:00`).toLocaleDateString('pt-BR');
}

function mesAtual() {
    const agora = new Date();
    return `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, '0')}`;
}

function nomeMes(referenceMonth) {
    if (!referenceMonth) return '';
    const [ano, numero] = referenceMonth.split('-').map(Number);
    const mes = new Date(ano, numero - 1, 1).toLocaleDateString('pt-BR', { month: 'long' });
    return mes.charAt(0).toUpperCase() + mes.slice(1);
}

async function init() {
    await renderHeader('payments');
    
    document.getElementById('payment-form')?.addEventListener('submit', salvarPagamento);
    document.getElementById('pagamentos-mes')?.addEventListener('change', () => carregarPagamentosTela(true));
    
    document.getElementById('payment-due-day')?.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        if (!isNaN(val)) {
            if (val > 31) e.target.value = 31;
            else if (val < 1) e.target.value = 1;
        }
    });

    await carregarCategoriasPagamento();
    await carregarPagamentosTela(true);
    await carregarGraficoHistorico();
}

function atualizarMesesDisponiveis(meses, mesSelecionado) {
    const select = document.getElementById('pagamentos-mes');
    if (!select) return;
    
    const mesesUnicos = [...new Set(meses || [mesAtual()])].sort().reverse();
    select.innerHTML = mesesUnicos.map(m => {
        const [ano, num] = m.split('-').map(Number);
        const dataData = new Date(ano, num - 1, 1);
        const nome = dataData.toLocaleString('pt-BR', { month: 'long' });
        return `<option value="${m}" ${m === mesSelecionado ? 'selected' : ''}>${nome.charAt(0).toUpperCase() + nome.slice(1)} ${ano}</option>`;
    }).join('');
}

function statusInfo(pagamento) {
    if (pagamento.status === 'paid') {
        return { texto: `Pago em ${dataFormatada(pagamento.paid_at?.slice(0, 10))}`, classe: 'text-emerald-700 bg-emerald-50 border-emerald-200' };
    }
    if (pagamento.is_overdue) {
        const texto = pagamento.is_stacked ? `Atrasado - ${nomeMes(pagamento.reference_month)}` : 'Atrasado';
        return { texto, classe: 'text-rose-700 bg-rose-50 border-rose-200' };
    }
    return { texto: 'A vencer', classe: 'text-amber-700 bg-amber-50 border-amber-200' };
}

function renderizarCardHtml(pagamento) {
    const status = statusInfo(pagamento);
    const parcela = pagamento.total_installments
        ? `${pagamento.installment_number || '-'} / ${pagamento.total_installments}`
        : 'Indeterminado';
    const pago = pagamento.status === 'paid';

    return `
        <article id="pagamento-card-${pagamento.id}" class="relative bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:border-slate-300 transition">
            <button type="button" onclick="window.marcarPagamentoComoPago(event, '${pagamento.id}');" title="${pago ? 'Desfazer pagamento' : 'Marcar como pago'}" class="absolute top-4 right-4 w-8 h-8 rounded-full border ${pago ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300 bg-white text-slate-400 hover:border-emerald-500 hover:text-emerald-600'} flex items-center justify-center transition">
                <span class="material-symbols-outlined text-[18px]">check</span>
            </button>
            <div class="min-w-0 pr-12">
                <div class="flex flex-wrap items-center gap-2">
                    <h3 class="font-semibold text-slate-800 text-sm">${pagamento.name}</h3>
                    <span class="text-[10px] px-2 py-0.5 rounded-full border font-semibold ${status.classe}">${status.texto}</span>
                </div>
                <p class="text-xs text-slate-500 mt-1">${pagamento.description || 'Conta recorrente'} • ${pagamento.category_name}</p>
                <p class="text-[11px] text-slate-400 mt-2">Parcela: ${parcela} • Vencimento: ${dataFormatada(pagamento.due_date)}</p>
            </div>
            <div class="flex items-center justify-between gap-4 mt-4 pt-3 border-t border-slate-100">
                <strong class="text-base text-slate-800">${moeda(pagamento.amount)}</strong>
                <button type="button" onclick="window.editarValorPagamento('${pagamento.id}')" title="Editar valor" class="p-1.5 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition">
                    <span class="material-symbols-outlined text-lg">settings</span>
                </button>
            </div>
        </article>
    `;
}

function renderizarPagamentos(data) {
    const todos = [...(data.pendencias_anteriores || []), ...(data.pagamentos_mes || [])];
    pagamentosAtuais = todos.sort((a, b) => (a.status === 'paid' ? 1 : 0) - (b.status === 'paid' ? 1 : 0));
    
    const lista = document.getElementById('lista-pagamentos');
    if (!lista) return;

    if (!pagamentosAtuais.length) {
        lista.innerHTML = '<p class="text-xs text-slate-400 text-center py-12 col-span-full">Nenhuma conta cadastrada para este período.</p>';
        return;
    }
    lista.innerHTML = pagamentosAtuais.map(renderizarCardHtml).join('');
}

function renderizarKpis(kpis) {
    if (!kpis) return;
    document.getElementById('kpi-contas').textContent = moeda(kpis.total_a_pagar_mes);
    document.getElementById('kpi-aberto').textContent = moeda(kpis.total_em_aberto);
    document.getElementById('kpi-pago').textContent = moeda(kpis.total_pago);
    document.getElementById('kpi-atraso').textContent = moeda(kpis.total_em_atraso);
}

async function carregarPagamentosTela(mostrarLoading = false, reRenderLista = true) {
    const mes = document.getElementById('pagamentos-mes')?.value || mesAtual();
    const lista = document.getElementById('lista-pagamentos');

    if (mostrarLoading && lista) {
        lista.innerHTML = '<p class="text-xs text-slate-400 text-center py-12 col-span-full">Carregando pagamentos...</p>';
    }

    try {
        const data = await apiRequest(`/payments?user_id=${USER_ID}&mes=${encodeURIComponent(mes)}`);
        atualizarMesesDisponiveis(data.meses_disponiveis, data.mes);
        renderizarKpis(data.kpis);
        if (reRenderLista) renderizarPagamentos(data);
    } catch (error) {
        if (lista && (mostrarLoading || !pagamentosAtuais.length)) {
            lista.innerHTML = `<p class="text-xs text-rose-500 text-center py-12 col-span-full">Falha ao carregar: ${error.message}</p>`;
        }
    }
}

async function carregarCategoriasPagamento() {
    const select = document.getElementById('payment-category-select');
    if (!select) return;
    try {
        const categorias = await apiRequest(`/payments/categories?user_id=${USER_ID}`);
        select.innerHTML = '<option value="">Selecione uma categoria</option>' + 
            categorias.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    } catch (err) {
        console.error('Erro ao carregar categorias:', err);
    }
}

function abrirModalPagamento(pagamento = null) {
    const modal = document.getElementById('payment-modal');
    const form = document.getElementById('payment-form');
    if (!modal || !form) return;

    form.reset();
    const isEdit = Boolean(pagamento);

    document.getElementById('payment-expense-id').value = pagamento?.expense_id || '';
    document.getElementById('payment-monthly-id').value = pagamento?.id || '';
    document.getElementById('payment-name').value = pagamento?.name || '';
    document.getElementById('payment-description').value = pagamento?.description || '';
    document.getElementById('payment-due-day').value = pagamento?.due_day || '';
    document.getElementById('payment-amount').value = pagamento?.amount || '';
    document.getElementById('payment-category-select').value = pagamento?.category_id || '';
    document.getElementById('payment-total-installments').value = pagamento?.total_installments || '';
    document.getElementById('payment-start-installment').value = pagamento?.installment_number || '';
    document.getElementById('payment-modal-title').textContent = isEdit ? 'Editar valor da fatura' : 'Nova conta recorrente';

    document.querySelectorAll('.payment-contract-field').forEach(el => el.classList.toggle('hidden', isEdit));

    const nameInput = document.getElementById('payment-name');
    const dueDayInput = document.getElementById('payment-due-day');
    if (nameInput) nameInput.required = !isEdit;
    if (dueDayInput) dueDayInput.required = !isEdit;

    const btnExcluir = document.getElementById('btn-excluir-conta');
    if (btnExcluir) btnExcluir.classList.toggle('hidden', !isEdit);

    modal.classList.remove('hidden');
}

window.fecharModalPagamento = () => {
    document.getElementById('payment-modal')?.classList.add('hidden');
};

window.abrirModalConfirmacaoExclusao = () => {
    const nomeConta = document.getElementById('payment-name').value || 'esta conta';
    const msgEl = document.getElementById('confirm-delete-message');
    if (msgEl) {
        msgEl.innerHTML = `Tem certeza que deseja excluir <strong>${nomeConta}</strong>?<br><span class="text-[11px] text-slate-400 mt-1 block">A fatura do mês atual será removida e o histórico de meses anteriores será preservado.</span>`;
    }
    document.getElementById('confirm-delete-modal')?.classList.remove('hidden');
};

window.fecharModalConfirmacaoExclusao = () => {
    document.getElementById('confirm-delete-modal')?.classList.add('hidden');
};

window.executarExclusaoContaConfirmada = async () => {
    const expenseId = document.getElementById('payment-expense-id').value;
    const mes = document.getElementById('pagamentos-mes')?.value || mesAtual();
    const btnConfirm = document.getElementById('btn-confirmar-exclusao-acao');

    if (!expenseId) return;

    try {
        if (btnConfirm) {
            btnConfirm.disabled = true;
            btnConfirm.textContent = 'Excluindo...';
        }
        await apiRequest(`/payments/expenses/${expenseId}?user_id=${USER_ID}&mes=${encodeURIComponent(mes)}`, 'DELETE');
        window.fecharModalConfirmacaoExclusao();
        window.fecharModalPagamento();
        await carregarPagamentosTela(false);
    } catch (error) {
        alert(`Erro ao excluir conta: ${error.message}`);
    } finally {
        if (btnConfirm) {
            btnConfirm.disabled = false;
            btnConfirm.textContent = 'Sim, excluir';
        }
    }
};

async function salvarPagamento(event) {
    if (event) event.preventDefault();
    const monthlyId = document.getElementById('payment-monthly-id').value;

    try {
        if (monthlyId) {
            await apiRequest(`/payments/monthly/${monthlyId}?user_id=${USER_ID}`, 'PUT', {
                amount: Number(document.getElementById('payment-amount').value)
            });
        } else {
            const totalParcelas = document.getElementById('payment-total-installments').value;
            const parcelaInicial = document.getElementById('payment-start-installment').value;

            if (Boolean(totalParcelas) !== Boolean(parcelaInicial)) {
                throw new Error('Preencha total de parcelas e parcela inicial juntos, ou deixe ambos vazios.');
            }

            const categoryVal = document.getElementById('payment-category-select').value;

            await apiRequest(`/payments/expenses?user_id=${USER_ID}`, 'POST', {
                name: document.getElementById('payment-name').value,
                description: document.getElementById('payment-description').value,
                category_id: categoryVal && categoryVal.trim() !== '' ? String(categoryVal).trim() : null,
                due_day: Number(document.getElementById('payment-due-day').value),
                current_amount: Number(document.getElementById('payment-amount').value),
                total_installments: Number(totalParcelas) || null,
                start_installment: Number(parcelaInicial) || null
            });
        }
        window.fecharModalPagamento();
        await carregarPagamentosTela(false);
    } catch (error) {
        alert(error.message);
    }
}

window.marcarPagamentoComoPago = async (event, id) => {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const pagamento = pagamentosAtuais.find(item => item.id === id);
    if (!pagamento) return;

    const statusAnterior = pagamento.status;
    const paidAtAnterior = pagamento.paid_at;
    const novoStatus = statusAnterior === 'paid' ? 'pending' : 'paid';

    pagamento.status = novoStatus;
    pagamento.paid_at = novoStatus === 'paid' ? new Date().toISOString() : null;

    const cardEl = document.getElementById(`pagamento-card-${id}`);
    if (cardEl) cardEl.outerHTML = renderizarCardHtml(pagamento);

    try {
        const res = await apiRequest(`/payments/monthly/${id}/pay?user_id=${USER_ID}`, 'PATCH');
        if (res.novo_status) {
            pagamento.status = res.novo_status;
            pagamento.paid_at = res.paid_at;
        }
        await carregarPagamentosTela(false, false);
        await carregarGraficoHistorico();
    } catch (error) {
        pagamento.status = statusAnterior;
        pagamento.paid_at = paidAtAnterior;
        const rolledCardEl = document.getElementById(`pagamento-card-${id}`);
        if (rolledCardEl) rolledCardEl.outerHTML = renderizarCardHtml(pagamento);
        alert(error.message);
    }
};

window.editarValorPagamento = (id) => {
    const pagamento = pagamentosAtuais.find(item => item.id === id);
    if (!pagamento) return;
    abrirModalPagamento(pagamento);
};

window.abrirNovoPagamento = () => {
    abrirModalPagamento();
};

async function carregarGraficoHistorico() {
    const canvas = document.getElementById('chart-pagamentos-historico');
    if (!canvas) return;

    try {
        const ano = new Date().getFullYear();
        const labelAno = document.getElementById('grafico-historico-ano');
        if (labelAno) labelAno.textContent = String(ano);

        const res = await apiRequest(`/payments/history?user_id=${USER_ID}&ano=${ano}`);
        renderPaymentHistoryChart('chart-pagamentos-historico', res.historico || []);
    } catch (err) {
        console.error('Erro ao carregar gráfico histórico de pagamentos:', err);
    }
}

document.addEventListener('DOMContentLoaded', init);