import { apiRequest } from '../core/api.js';

const USER_ID = 'd262bc6c-d58b-4f4e-99b4-505202b646ba';

export async function renderHeader(activePage = 'invoices') {
    const container = document.getElementById('header-container');
    if (!container) return;

    const logoPath = '/assets/logo.gif';
    const invoicesPath = '/src/pages/invoices/invoices.html';
    const cardsPath = '/src/pages/cards/cards.html';
    const paymentsPath = '/src/pages/payments/payments.html';
    const receivablesPath = '/src/pages/receivables/receivables.html';

    container.innerHTML = `
        <header class="bg-white border-b border-slate-200 px-4 md:px-6 py-2.5 md:py-3 sticky top-0 z-20 shadow-sm">
            <div class="flex items-center justify-between max-w-6xl mx-auto">
                <div class="flex items-center gap-3 md:gap-8">
                    <button onclick="window.toggleMenuMobile()" class="p-1.5 text-slate-600 hover:bg-slate-100 rounded-lg md:hidden">
                        <span class="material-symbols-outlined text-2xl">menu</span>
                    </button>

                    <a href="${invoicesPath}" class="flex items-center">
                        <img src="${logoPath}" alt="Logo Finanças" class="h-10 md:h-12 w-auto rounded object-contain" onerror="this.src='https://via.placeholder.com/120x40?text=Finan%C3%A7as'">
                    </a>

                    <nav class="hidden md:flex items-center gap-6 font-medium text-sm text-slate-600">
                        <div class="relative group cursor-pointer py-1">
                            <span class="hover:text-slate-900 transition flex items-center gap-1 select-none ${activePage === 'invoices' ? 'font-bold text-slate-900' : ''}">
                                Cartões
                                <span class="material-symbols-outlined text-base">expand_more</span>
                            </span>
                            <div class="absolute top-full left-0 hidden group-hover:flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 w-52 z-30">
                                <a href="${invoicesPath}" class="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-base text-slate-500">credit_card</span>
                                    Fatura Geral (Todos)
                                </a>
                                <div class="border-t border-slate-100 my-1"></div>
                                <div id="lista-cartoes-dropdown" class="flex flex-col">
                                    <p class="px-4 py-1.5 text-[11px] text-slate-400">Carregando cartões...</p>
                                </div>
                            </div>
                        </div>

                        <a href="${paymentsPath}" class="hover:text-slate-900 transition ${activePage === 'payments' ? 'font-bold text-slate-900' : ''}">
                            Pagamentos
                        </a>
                        <a href="${receivablesPath}" class="hover:text-slate-900 transition ${activePage === 'receivables' ? 'font-bold text-slate-900' : ''}">
                            A Receber
                        </a>
                    </nav>
                </div>

                <div class="flex items-center gap-1.5 md:gap-2">
                    <button onclick="window.abrirDrawer('drawer-sync')" title="Sincronizar" class="p-2 text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center">
                        <span id="sync-icon-topbar" class="material-symbols-outlined text-xl">sync</span>
                    </button>
                    
                    <button onclick="window.abrirDrawer('drawer-notifications')" title="Notificações" class="relative p-2 text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center">
                        <span class="material-symbols-outlined text-xl">notifications</span>
                    </button>

                    <div class="relative group cursor-pointer">
                        <button title="Configurações" class="p-2 text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center">
                            <span class="material-symbols-outlined text-xl">settings</span>
                        </button>
                        <div class="absolute top-full right-0 hidden group-hover:flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 w-48 z-30">
                            <a href="${cardsPath}" class="px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 transition">
                                <span class="material-symbols-outlined text-base text-slate-500">manage_accounts</span>
                                Gerenciar Dados
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Overlay Global -->
        <div id="drawer-overlay" onclick="window.fecharTodosDrawers()" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 hidden transition-opacity"></div>

        <!-- Drawer Lateral de Sincronização -->
        <aside id="drawer-sync" class="fixed top-0 right-0 z-50 w-80 sm:w-96 h-screen bg-white shadow-2xl border-l border-slate-200 transform translate-x-full transition-transform duration-300 ease-in-out flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-slate-700">sync</span>
                    <h3 class="font-semibold text-slate-800">Sincronização</h3>
                </div>
                <button onclick="window.fecharDrawer('drawer-sync')" class="p-1 text-slate-400 hover:text-slate-700 rounded-lg transition">
                    <span class="material-symbols-outlined text-xl">close</span>
                </button>
            </div>

            <div class="p-6 overflow-y-auto flex-1 space-y-5">
                <button id="btn-sync-action" onclick="window.executarSincronizacao()" class="w-full py-3 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium text-sm transition flex items-center justify-center gap-2 shadow-sm">
                    <span id="sync-icon-drawer" class="material-symbols-outlined text-lg">sync</span>
                    <span>Sincronizar Agora</span>
                </button>

                <div id="sync-results" class="hidden space-y-3 pt-3 border-t border-slate-200">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resultado da Consulta</span>
                    <div id="sync-results-content" class="space-y-2 text-xs"></div>
                </div>
            </div>
        </aside>
    `;

    window.toggleMenuMobile = () => {
        const menu = document.getElementById('mobile-menu');
        if (menu) menu.classList.toggle('hidden');
    };

    window.abrirDrawer = (id) => {
        const drawer = document.getElementById(id);
        const overlay = document.getElementById('drawer-overlay');
        if (overlay) overlay.classList.remove('hidden');
        if (drawer) drawer?.classList.remove('translate-x-full');
    };

    window.fecharDrawer = (id) => {
        const drawer = document.getElementById(id);
        const overlay = document.getElementById('drawer-overlay');
        if (drawer) drawer.classList.add('translate-x-full');
        if (overlay) overlay.classList.add('hidden');
    };

    window.fecharTodosDrawers = () => {
        document.querySelectorAll('aside[id^="drawer-"]').forEach(d => d.classList.add('translate-x-full'));
        const overlay = document.getElementById('drawer-overlay');
        if (overlay) overlay.classList.add('hidden');
    };

    window.executarSincronizacao = async () => {
        const iconDrawer = document.getElementById('sync-icon-drawer');
        const iconTopbar = document.getElementById('sync-icon-topbar');
        const button = document.getElementById('btn-sync-action');
        const resultsContainer = document.getElementById('sync-results');
        const resultsContent = document.getElementById('sync-results-content');

        if (iconDrawer) iconDrawer.classList.add('animate-spin');
        if (iconTopbar) iconTopbar.classList.add('animate-spin');
        if (button) button.disabled = true;
        if (resultsContainer) resultsContainer.classList.remove('hidden');

        if (resultsContent) {
            resultsContent.innerHTML = `<p class="text-slate-500 text-center py-2">Consultando e comparando dados na Pluggy...</p>`;
        }

        try {
            const data = await apiRequest('/sync', 'POST');
            const totalNovas = data.resumo?.total_novas || 0;
            const totalAtualizadas = data.resumo?.total_atualizadas || 0;
            const excedente = data.resumo?.excedente_preview || 0;
            const previewList = data.preview_novas_transacoes || [];

            if (!resultsContent) return;
            let html = '';

            if (totalNovas > 0 || totalAtualizadas > 0) {
                let textoResumo = '';
                if (totalNovas > 0 && totalAtualizadas > 0) {
                    textoResumo = `${totalNovas} nova(s) e ${totalAtualizadas} atualizada(s) com sucesso!`;
                } else if (totalNovas > 0) {
                    textoResumo = `${totalNovas} nova(s) transação(ões) encontrada(s)!`;
                } else {
                    textoResumo = `${totalAtualizadas} transação(ões) atualizada(s) no banco!`;
                }

                html += `<p class="font-semibold text-emerald-600 mb-2">${textoResumo}</p>`;

                if (previewList.length > 0) {
                    html += `<div class="space-y-1.5">`;
                    previewList.forEach(tx => {
                        const atualizada = String(tx.tipo || '').toLowerCase() === 'atualizada';
                        const badgeTexto = atualizada ? 'Atualizada' : 'Nova';
                        const badgeStyle = atualizada
                            ? 'background-color:#fef3c7;color:#b45309;'
                            : 'background-color:#d1fae5;color:#047857;';
                        html += `
                            <div class="p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex justify-between items-center">
                                <div class="min-w-0 pr-2">
                                    <p class="font-medium text-slate-800 truncate"><span style="${badgeStyle}display:inline-block;padding:2px 6px;margin-right:6px;border-radius:4px;font-size:9px;line-height:1.2;text-transform:uppercase;letter-spacing:0.04em;vertical-align:middle;">${badgeTexto}</span>${tx.descricao}</p>
                                    <p class="text-[10px] text-slate-400 font-medium">${tx.banco || 'Cartão'} • ${tx.data}</p>
                                </div>
                                <span class="font-semibold text-slate-900 whitespace-nowrap">R$ ${Number(tx.valor).toFixed(2)}</span>
                            </div>
                        `;
                    });
                    html += `</div>`;
                }

                if (excedente > 0) {
                    html += `<p class="text-[11px] text-slate-500 italic mt-2 text-center">...e mais outras ${excedente} encontradas.</p>`;
                }
            } else {
                html = `<div class="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 text-center">Nenhum dado novo ou atualização disponível.</div>`;
            }

            resultsContent.innerHTML = html;
            if (typeof window.carregarDados === 'function') await window.carregarDados();
            if (typeof window.carregarCartoes === 'function') await window.carregarCartoes();
            await carregarCartoesMenu();
        } catch (err) {
            if (resultsContent) {
                resultsContent.innerHTML = `
                    <div class="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs leading-relaxed">
                        <p class="font-semibold">Sincronização Falhou</p>
                        <p class="mt-0.5 text-rose-600">${err.message}</p>
                    </div>
                `;
            }
        } finally {
            setTimeout(() => {
                if (iconDrawer) iconDrawer.classList.remove('animate-spin');
                if (iconTopbar) iconTopbar.classList.remove('animate-spin');
                if (button) button.disabled = false;
            }, 500);
        }
    };
    
    await carregarCartoesMenu();
}

async function carregarCartoesMenu() {
    const containerDesktop = document.getElementById('lista-cartoes-dropdown');
    if (!containerDesktop) return;

    try {
        const cartoes = await apiRequest('/invoices/cards');

        if (!cartoes || cartoes.length === 0) {
            containerDesktop.innerHTML = '<p class="px-4 py-1.5 text-[11px] text-slate-400">Nenhum cartão cadastrado</p>';
            return;
        }

        containerDesktop.innerHTML = cartoes.map(c => {
            const nomeExibicao = c.card_name || c.bank_name;
            const urlCard = `/src/pages/invoices/invoices.html?card_id=${encodeURIComponent(c.id)}&banco=${encodeURIComponent(nomeExibicao)}`;

            return `
                <a href="${urlCard}" class="px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 transition">
                    <span class="w-2 h-2 rounded-full bg-slate-400"></span> ${nomeExibicao}
                </a>
            `;
        }).join('');
    } catch (err) {
        console.error('Erro ao carregar menu de cartões:', err);
    }
}