# Melhoria: Ordenação dos Lançamentos dos Cartões

## Objetivo

Melhorar a listagem de lançamentos da tela de cartões para:

- Exibir a data e a hora da compra.
- Permitir que o usuário escolha o tipo de ordenação.
- Manter a ordenação selecionada enquanto a fatura atual for exibida.

## Escopo

A melhoria deve ser implementada na tela de faturas/cartões:

- `frontend/src/pages/invoices/invoices.html`
- `frontend/src/pages/invoices/invoices.js`

Não é necessário alterar o backend neste primeiro momento, pois a API já retorna a data da transação como `datetime` no campo `date`.

## Opções de ordenação

Adicionar um seletor de ordenação próximo ao seletor de fatura com as seguintes opções:

| Valor | Texto exibido | Critério |
| --- | --- | --- |
| `date_desc` | Mais recente | Data e hora decrescentes |
| `date_asc` | Mais antigo | Data e hora crescentes |
| `amount_desc` | Maior valor | Valor decrescente |
| `amount_asc` | Menor valor | Valor crescente |

A opção padrão deve ser `date_desc`.

## Exibição da data e hora

Cada lançamento deve exibir o campo `tx.date` no formato local brasileiro:

```text
DD/MM/AAAA HH:MM
```

Exemplo:

```text
28/08/2026 05:25
```

A conversão deve ser feita com `new Date(tx.date)` e `toLocaleString('pt-BR')`, respeitando o fuso horário do navegador.

Exemplo de implementação:

```js
function formatarDataCompra(data) {
    if (!data) return 'Data não informada';

    return new Date(data).toLocaleString('pt-BR', {
        dateStyle: 'short',
        timeStyle: 'short'
    });
}
```

## Implementação no frontend

### 1. Adicionar o seletor no HTML

Em `invoices.html`, inserir um segundo `select` próximo de `#filtro-fatura`:

```html
<select id="filtro-ordenacao">
    <option value="date_desc">Mais recente</option>
    <option value="date_asc">Mais antigo</option>
    <option value="amount_desc">Maior valor</option>
    <option value="amount_asc">Menor valor</option>
</select>
```

O seletor deve manter o mesmo padrão visual do filtro de fatura.

### 2. Armazenar as transações carregadas

Em `invoices.js`, criar uma variável para manter as transações da fatura selecionada:

```js
let transacoesAtuais = [];
```

Depois que a API retornar os lançamentos, atualizar essa variável antes de renderizar:

```js
transacoesAtuais = transacoes;
renderTransacoes(transacoesAtuais);
```

### 3. Registrar a mudança de ordenação

No `init()`, adicionar um listener para o novo seletor:

```js
document
    .getElementById('filtro-ordenacao')
    ?.addEventListener('change', () => renderTransacoes(transacoesAtuais));
```

A troca da ordenação deve ocorrer sem nova chamada à API.

### 4. Criar a função de ordenação

Ordenar uma cópia do array para não alterar os dados originais:

```js
function ordenarTransacoes(transacoes) {
    const ordenacao = document.getElementById('filtro-ordenacao')?.value || 'date_desc';

    return [...transacoes].sort((a, b) => {
        if (ordenacao === 'date_asc') {
            return new Date(a.date) - new Date(b.date);
        }

        if (ordenacao === 'amount_desc') {
            return Number(b.amount) - Number(a.amount);
        }

        if (ordenacao === 'amount_asc') {
            return Number(a.amount) - Number(b.amount);
        }

        return new Date(b.date) - new Date(a.date);
    });
}
```

### 5. Aplicar a ordenação na renderização

A função `renderTransacoes()` deve ordenar os dados antes de gerar o HTML:

```js
const transacoesOrdenadas = ordenarTransacoes(transacoes || []);
```

O contador deve continuar refletindo a quantidade total de lançamentos, e a lista deve ser gerada usando `transacoesOrdenadas`.

### 6. Exibir a data e a hora

Adicionar a data formatada junto das informações secundárias do lançamento:

```js
const dataCompra = formatarDataCompra(tx.date);
```

Exemplo de apresentação:

```html
<p class="text-[10px] text-slate-400">
    ${dataCompra} • ${banco}
</p>
```

A data deve aparecer tanto para transações normais quanto para transações ignoradas.

## Comportamento esperado

- Ao abrir a tela, os lançamentos aparecem do mais recente para o mais antigo.
- Ao selecionar outra opção, a lista é reordenada imediatamente.
- Ao trocar de fatura, os novos lançamentos são carregados e a ordenação escolhida continua aplicada.
- O total da fatura e o gráfico de categorias não devem ser alterados pela ordenação.
- A ordenação não deve modificar o array original retornado pela API.
- Lançamentos sem data devem permanecer na lista sem causar erro.
- Valores negativos devem ser ordenados corretamente nas opções de maior e menor valor.

## Critérios de aceite

- [ ] O seletor de ordenação aparece ao lado do seletor de fatura.
- [ ] A opção padrão é "Mais recente".
- [ ] A data e a hora aparecem em cada lançamento.
- [ ] "Mais recente" ordena pela data/hora decrescente.
- [ ] "Mais antigo" ordena pela data/hora crescente.
- [ ] "Maior valor" ordena pelo valor decrescente.
- [ ] "Menor valor" ordena pelo valor crescente.
- [ ] A troca de ordenação não faz nova requisição ao backend.
- [ ] A seleção permanece aplicada ao trocar de fatura.
- [ ] A ordenação não altera o total nem o gráfico.
- [ ] Faturas sem lançamentos continuam exibindo a mensagem adequada.

## Validação manual

1. Abrir a tela de faturas/cartões.
2. Confirmar que os lançamentos aparecem com data e hora.
3. Confirmar que a ordem inicial é da compra mais recente para a mais antiga.
4. Selecionar "Mais antigo" e conferir a inversão da lista.
5. Selecionar "Maior valor" e conferir o primeiro lançamento.
6. Selecionar "Menor valor" e conferir o primeiro lançamento.
7. Trocar a fatura e confirmar que a ordenação continua selecionada.
8. Testar uma fatura sem lançamentos.
9. Verificar no DevTools que a troca de ordenação não gera novas requisições.

## Possível evolução

Se a quantidade de transações crescer a ponto de exigir paginação, a ordenação poderá ser movida para o backend com parâmetros no endpoint, por exemplo:

```text
GET /api/v1/invoices/transactions?sort_by=date&sort_order=desc
```

Essa evolução não faz parte desta implementação inicial.
