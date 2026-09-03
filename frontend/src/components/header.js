import { apiRequest } from '../core/api.js';

const USER_ID = 'd262bc6c-d58b-4f4e-99b4-505202b646ba';

export async function renderHeader(activePage = 'invoices') {
    const container = document.getElementById('header-container');
    if (!container) return;

    const logoPath = '/assets/logo.gif';

    container.innerHTML = `
        <header class="bg-white border-b border-slate-200 px-4 md:px-6 py-2.5 md:py-3 sticky top-0 z-20 shadow-sm">
            <div class="flex items-center justify-between max-w-6xl mx-auto">
                <div class="flex items-center gap-3 md:gap-8">
                    <button onclick="window.toggleMenuMobile()" class="p-1.5 text-slate-600 hover:bg-slate-100 rounded-lg md:hidden">
                        <span class="material-symbols-outlined text-2xl">menu</span>
                    </button>

                    <a href="/src/pages/invoices/invoices.html" class="flex items-center">
                        <img src="${logoPath}" alt="Logo Finanças" class="h-10 md:h-12 w-auto rounded object-contain" onerror="this.src='https://via.placeholder.com/120x40?text=Finan%C3%A7as'">
                    </a>

                    <nav class="hidden md:flex items-center gap-6 font-medium text-sm text-slate-600">
                        <div class="relative group cursor-pointer py-1">
                            <span class="hover:text-slate-900 transition flex items-center gap-1 select-none ${activePage === 'invoices' ? 'font-bold text-slate-900' : ''}">
                                Cartões
                                <span class="material-symbols-outlined text-base">expand_more</span>
                            </span>
                            <div class="absolute top-full left-0 hidden group-hover:flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 w-52 z-30">
                                <a href="/src/pages/invoices/invoices.html" class="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-base text-slate-500">credit_card</span>
                                    Fatura Geral (Todos)
                                </a>
                                <div class="border-t border-slate-100 my-1"></div>
                                <div id="lista-cartoes-dropdown" class="flex flex-col">
                                    <p class="px-4 py-1.5 text-[11px] text-slate-400">Carregando cartões...</p>
                                </div>
                            </div>
                        </div>

                        <a href="/src/pages/payments/payments.html" class="hover:text-slate-900 transition ${activePage === 'payments' ? 'font-bold text-slate-900' : ''}">
                            Pagamentos
                        </a>
                        <a href="/src/pages/receivables/receivables.html" class="hover:text-slate-900 transition ${activePage === 'receivables' ? 'font-bold text-slate-900' : ''}">
                            A Receber
                        </a>
                    </nav>
                </div>

                <!-- Botões de Ação na Direita -->
                <div class="flex items-center gap-1.5 md:gap-2">
                    <button onclick="window.abrirDrawer('drawer-sync')" title="Sincronizar" class="p-2 text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200">
                        <span class="material-symbols-outlined text-xl">sync</span>
                    </button>
                    
                    <button onclick="window.abrirDrawer('drawer-notifications')" title="Notificações" class="relative p-2 text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200">
                        <span class="material-symbols-outlined text-xl">notifications</span>
                    </button>

                    <!-- Botão de Engrenagem com Dropdown -->
                    <div class="relative group cursor-pointer">
                        <button title="Configurações" class="p-2 text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200 flex items-center justify-center">
                            <span class="material-symbols-outlined text-xl">settings</span>
                        </button>
                        <div class="absolute top-full right-0 hidden group-hover:flex flex-col bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 w-48 z-30">
                            <a href="/src/pages/cards/cards.html" class="px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 transition">
                                <span class="material-symbols-outlined text-base text-slate-500">manage_accounts</span>
                                Gerenciar Dados
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Menu Mobile -->
            <div id="mobile-menu" class="hidden md:hidden pt-3 pb-1 border-t border-slate-100 mt-2 space-y-1">
                <a href="/src/pages/invoices/invoices.html" class="block px-2 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50 rounded">Fatura Geral (Todos)</a>
                <div id="lista-cartoes-mobile" class="pl-2 border-l-2 border-slate-200 space-y-1 my-1"></div>
                <a href="/src/pages/payments/payments.html" class="block px-2 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded">Pagamentos</a>
                <a href="/src/pages/receivables/receivables.html" class="block px-2 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded">A Receber</a>
                <div class="border-t border-slate-100 pt-1">
                    <a href="/src/pages/cards/cards.html" class="block px-2 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded">Gerenciar Dados</a>
                </div>
            </div>
        </header>
    `;

    window.toggleMenuMobile = () => {
        const menu = document.getElementById('mobile-menu');
        if (menu) menu.classList.toggle('hidden');
    };

    await carregarCartoesMenu();
}

async function carregarCartoesMenu() {
    const containerDesktop = document.getElementById('lista-cartoes-dropdown');
    const containerMobile = document.getElementById('lista-cartoes-mobile');
    if (!containerDesktop) return;

    try {
        const faturas = await apiRequest(`/invoices/bills?user_id=${USER_ID}`);
        const bancosUnicos = Array.from(
            new Set(faturas.map(f => f.card_name).filter(Boolean))
        ).sort();

        if (bancosUnicos.length === 0) {
            containerDesktop.innerHTML = '<p class="px-4 py-1.5 text-[11px] text-slate-400">Nenhum cartão cadastrado</p>';
            return;
        }

        let htmlDesktop = '';
        let htmlMobile = '';

        bancosUnicos.forEach(nomeBanco => {
            const isInter = nomeBanco.toLowerCase().includes('inter');
            const isSantander = nomeBanco.toLowerCase().includes('santander');
            const corDot = isInter ? 'bg-orange-500' : isSantander ? 'bg-red-500' : 'bg-slate-400';

            htmlDesktop += `
                <a href="/src/pages/invoices/invoices.html?banco=${encodeURIComponent(nomeBanco)}" class="px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 transition">
                    <span class="w-2 h-2 rounded-full ${corDot}"></span> ${nomeBanco}
                </a>
            `;

            htmlMobile += `
                <a href="/src/pages/invoices/invoices.html?banco=${encodeURIComponent(nomeBanco)}" class="block py-1 px-2 text-xs font-medium text-slate-600 hover:bg-slate-50 rounded">
                    ${nomeBanco}
                </a>
            `;
        });

        containerDesktop.innerHTML = htmlDesktop;
        if (containerMobile) containerMobile.innerHTML = htmlMobile;

    } catch (err) {
        console.error('Erro ao carregar menu de cartões:', err);
    }
}