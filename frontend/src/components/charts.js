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