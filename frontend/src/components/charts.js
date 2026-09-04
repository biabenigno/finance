let chartInstance = null;

export function renderChart(canvasId, categorias) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    // Destrói o gráfico anterior para evitar sobreposição ao recarregar os dados
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }

    if (!categorias || categorias.length === 0) return;

    chartInstance = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: categorias.map(c => c.category_name),
            datasets: [{
                label: 'Gastos por Categoria (R$)',
                data: categorias.map(c => c.total_amount),
                backgroundColor: categorias.map(c => c.category_color || '#0284c7'),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

let paymentHistoryChartInstance = null;

export function renderPaymentHistoryChart(canvasId, dados) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    if (paymentHistoryChartInstance) {
        paymentHistoryChartInstance.destroy();
        paymentHistoryChartInstance = null;
    }

    const primeiroMesComDados = dados.findIndex(d => Number(d.previsto || 0) !== 0 || Number(d.realizado || 0) !== 0);
    const dadosVisiveis = primeiroMesComDados >= 0 ? dados.slice(primeiroMesComDados) : dados;

    paymentHistoryChartInstance = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: dadosVisiveis.map(d => d.mes),
            datasets: [
                {
                    label: 'Previsto',
                    data: dadosVisiveis.map(d => d.previsto),
                    backgroundColor: 'rgba(56, 114, 238, 0.75)',
                    borderRadius: 5,
                    borderSkipped: false,
                    order: 2
                },
                {
                    label: 'Realizado',
                    type: 'line',
                    data: dadosVisiveis.map(d => d.realizado),
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.12)',
                    borderWidth: 2.5,
                    pointBackgroundColor: '#f97316',
                    pointRadius: 4,
                    tension: 0.35,
                    fill: false,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: true, position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true }
            }
        }
    });
}