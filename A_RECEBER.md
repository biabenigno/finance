# Tela "A Receber"

Documentação funcional e visual da tela de recebíveis do Finanças Pluggy. Este documento descreve o comportamento atual da implementação para que outra pessoa consiga reproduzir a interface e o fluxo sem precisar inferir regras a partir do código.

## Objetivo da tela

A tela acompanha valores que terceiros devem ao usuário. Ela reúne duas origens de saldo:

- **Cartão:** compras de uma fatura que foram vinculadas a uma pessoa, integralmente ou por uma parcela.
- **Saldo Devedor:** cobranças e pagamentos registrados manualmente.

O fluxo principal é:

1. Exibir uma grade com todas as pessoas cadastradas.
2. Abrir os detalhes de uma pessoa em um drawer lateral.
3. Consultar uma fatura específica e vincular compras à pessoa.
4. Registrar, editar ou remover cobranças e pagamentos manuais.

## Arquivos envolvidos

- [ui/templates/aReceber.html](ui/templates/aReceber.html): estrutura HTML, drawer e modais.
- [ui/static/js/receivables_ui.js](ui/static/js/receivables_ui.js): estado da tela, renderização, eventos e chamadas de API.
- [ui/static/js/api.js](ui/static/js/api.js): funções HTTP usadas pelo front end.
- [api/app/routers/receivables.py](api/app/routers/receivables.py): contratos, validações e regras de negócio do backend.
- [ui/static/css/style.css](ui/static/css/style.css): tokens e componentes CSS compartilhados.
- [ui/templates/base.html](ui/templates/base.html): Tailwind via CDN, Material Symbols, fundo e largura geral da aplicação.

## Composição visual

### Layout global

- A página usa fundo `bg-slate-100`, texto `text-slate-800` e fonte utilitária `font-sans`.
- O conteúdo fica em um container `max-w-6xl mx-auto`.
- O espaçamento externo é `p-4` no mobile e `p-6` a partir do breakpoint `sm`.
- O título e os cards ficam dentro do bloco principal da página; o drawer e os modais usam `position: fixed`.
- Ícones de ação usam Material Symbols Outlined carregado no `base.html`.

### Cabeçalho

O cabeçalho da página é uma linha responsiva:

- Texto auxiliar: `Receitas de terceiros`, em caixa alta, pequeno, semibold e cinza.
- Título: `A Receber`, tamanho `text-2xl`, negrito.
- Descrição: `Acompanhe faturas compartilhadas e saldos informais.`
- Botão à direita: ícone `person_add` e texto `Adicionar Pessoa`.

No mobile, o cabeçalho passa a ser uma coluna. O botão ocupa apenas a largura necessária.

### Grade de pessoas

O elemento `#receivable-grid` usa:

```text
grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4
```

Cada pessoa é renderizada como um `<button>` com a classe `card-financeiro`, padding `p-5` e alinhamento de texto à esquerda. O card contém:

- nome da pessoa em `text-slate-800` e semibold;
- coluna **Cartão · Fatura atual**, valor em `text-sky-700`;
- coluna **Saldo Devedor**, valor em `text-amber-700`;
- hover com pequena elevação (`hover:-translate-y-0.5`) e sombra maior.

O componente `.card-financeiro` define fundo branco, borda `#e2e8f0`, raio de 14 px e sombra discreta. Quando não há pessoas, aparece uma mensagem centralizada com borda tracejada. Durante o carregamento, aparece `Carregando pessoas...`. Em erro, a mensagem fica em rose.

Valores monetários devem ser formatados com `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })`.

### Drawer de detalhes

O elemento `#person-drawer` é um painel lateral direito:

- largura total no mobile e `max-w-3xl` em telas maiores;
- fundo branco, `z-50`, sombra `shadow-2xl`;
- inicia fora da tela com `translate-x-full`;
- abre removendo essa classe, com transição de 300 ms;
- cabeçalho fixo visualmente por estar separado do conteúdo rolável;
- conteúdo em `p-5`, com rolagem vertical e duas colunas em `lg`.

O cabeçalho mostra o rótulo `Detalhes`, o nome da pessoa e o botão com ícone `close`. O conteúdo é preenchido dinamicamente em `#person-drawer-content`.

Dentro do drawer há duas seções:

#### Cartão

- título `Cartão`;
- total da pessoa no mês selecionado em azul (`text-2xl text-sky-700`);
- seletor de mês da fatura;
- botão `Vincular compra`;
- lista de compras vinculadas.

Cada compra é um artigo branco com borda, raio `rounded-xl`, padding `p-3` e sombra discreta. A primeira linha mostra o banco e o tipo da divisão:

- Integral: badge verde;
- Parcial: badge âmbar;
- banco Inter: badge laranja;
- banco Santander: badge vermelho;
- demais bancos: badge slate.

A compra mostra o valor devido pela pessoa em azul, o valor total original quando a divisão é parcial, descrição e data/hora. O menu de ações usa o ícone `settings` e oferece `Editar valor` e `Excluir vínculo`.

#### Saldo Devedor

- título `Saldo Devedor`;
- total em azul;
- botão quadrado com ícone `add` para adicionar cobrança;
- botão quadrado com ícone `remove` para registrar pagamento;
- lista de lançamentos manuais.

O valor de uma cobrança aparece com prefixo `+`; o valor de um pagamento aparece com prefixo `-`. Cada item mostra descrição, data/hora e menu com `Editar informações` e `Excluir lançamento`.

### Modais

Todos os modais usam fundo `bg-slate-900/40`, `backdrop-blur-sm`, centralização com `flex`, padding `p-4`, card branco, `rounded-xl` e sombra `shadow-xl`. O estado fechado é representado por `hidden`; para abrir, remover `hidden` e adicionar `flex`.

#### Nova pessoa: `#person-modal`

- largura máxima `max-w-sm`;
- campo obrigatório `Nome`;
- botões `Cancelar` e `Cadastrar`;
- ao abrir, o foco vai para `#new-person-name`.

#### Lançamento manual: `#manual-modal`

- largura máxima `max-w-md`;
- título variável: `Adicionar cobrança`, `Registrar pagamento` ou `Editar informações`;
- campo numérico `Valor`, mínimo `0.01`, passo `0.01`;
- campo opcional `Descrição`;
- campo oculto `#manual-type` com `charge` ou `payment`.

#### Vínculo de compra: `#card-modal`

- largura máxima `max-w-lg`;
- título inicial `Compras da fatura`;
- busca por descrição em `#card-purchase-search`;
- lista rolável de compras;
- após selecionar uma compra, troca a lista pelo formulário de divisão;
- seletor `Integral` ou `Parcial`;
- no modo parcial, exibe o campo `Valor da pessoa`;
- o valor parcial não pode exceder o total da compra.

## Estado do front end

O módulo mantém estas variáveis:

| Variável | Função |
| --- | --- |
| `pessoaAtual` | Pessoa aberta no drawer. Guarda pelo menos o `id` e depois recebe os dados completos. |
| `lancamentoManualEmEdicao` | ID do lançamento manual em edição; `null` significa criação. |
| `mesesFatura` | Meses retornados para a pessoa atual. |
| `mesFaturaSelecionado` | Mês inicial selecionado, preferindo o mês atual. |

O mês corrente é obtido como `YYYY-MM` a partir de `new Date().toISOString().slice(0, 7)`.

## Fluxos de interação

### Carregamento inicial

Ao importar o módulo, `carregarPessoas()` é executada automaticamente. Ela:

1. chama `GET /api/receivables/summary?mes=YYYY-MM`;
2. substitui o conteúdo do grid;
3. cria um botão por pessoa;
4. associa o clique a `abrirPessoa(id)`.

Depois de qualquer criação, edição ou exclusão bem-sucedida, o grid é carregado novamente para atualizar os totais.

### Abrir uma pessoa

`abrirPessoa(id)` salva a pessoa mínima em `pessoaAtual`, abre o drawer, busca os meses disponíveis e escolhe o mês atual quando ele existe. Caso contrário, escolhe o primeiro mês retornado ou o mês atual como fallback. Em seguida chama `renderizarPessoa()`.

O título do drawer usa o nome retornado. Enquanto os detalhes carregam, o conteúdo exibe `Carregando extratos...`.

### Trocar a fatura

O seletor `#person-month` chama `renderizarPessoa` no evento `change`. A nova consulta busca novamente os detalhes do mês, atualiza a seção Cartão e mantém os lançamentos manuais retornados pelo backend.

### Vincular uma compra

1. `abrirCompras()` abre o modal e consulta as compras da pessoa e do mês selecionado.
2. A busca textual é enviada no parâmetro `busca` a cada evento `input`.
3. Compras já vinculadas à pessoa ficam desabilitadas, opacas e exibem `Já vinculada`.
4. Uma compra disponível mostra descrição, valor, data e banco.
5. `selecionarCompra` troca a lista pelo formulário, preenche o valor total e seleciona `Integral`.
6. Ao escolher `Parcial`, o campo de valor fica visível; no modo integral ele fica oculto.
7. Ao salvar, envia a divisão e fecha o modal, atualizando detalhes e grid.

O backend transforma o modo integral no valor total da transação. Também impede que a divisão individual ou a soma das divisões ultrapasse o valor da compra.

### Criar ou editar lançamento manual

`abrirManual('charge')` abre o formulário para cobrança. `abrirManual('payment')` abre para pagamento. A edição preenche os campos existentes e guarda o ID em `lancamentoManualEmEdicao`.

No envio:

- criação envia `person_id`, `type`, `amount` e `description`;
- edição envia `type`, `amount` e `description` para o endpoint do ID;
- sucesso fecha o modal, limpa o formulário, atualiza o drawer e recarrega os cards.

Antes de excluir uma divisão ou lançamento, a interface pede confirmação com `confirm()`. Erros das operações de escrita são mostrados com `alert(error.message)`.

### Fechar superfícies

- `fecharPessoa()` move o drawer de volta com `translate-x-full` e limpa `pessoaAtual`.
- Os três modais voltam a `hidden` e removem `flex`.
- Fechar o modal de compra também restaura a lista de compras para que o próximo uso comece no estado inicial.

## Contrato da API

Todas as chamadas passam por `requisicaoJson`. Ela executa `fetch`, interpreta JSON e lança `Error` usando `data.detail` quando a resposta não é bem-sucedida.

| Método | Endpoint | Uso |
| --- | --- | --- |
| GET | `/api/receivables/summary?mes=YYYY-MM` | Cards da grade. |
| GET | `/api/receivables/people/{id}?mes=YYYY-MM` | Detalhes, divisões e lançamentos. |
| GET | `/api/receivables/people/{id}/card-transactions?mes=YYYY-MM&busca=...` | Compras disponíveis para vínculo. |
| GET | `/api/receivables/people/{id}/card-months` | Meses com compras de fatura nos últimos 12 meses. |
| POST | `/api/receivables/people` | Cria pessoa. |
| POST | `/api/receivables/manual` | Cria cobrança ou pagamento. |
| PUT | `/api/receivables/manual/{id}` | Edita lançamento manual. |
| DELETE | `/api/receivables/manual/{id}` | Exclui lançamento manual. |
| POST | `/api/receivables/card-splits` | Cria ou atualiza divisão de compra. |
| DELETE | `/api/receivables/card-splits/{id}` | Exclui vínculo de compra. |

Payload de pessoa:

```json
{ "name": "Nome da pessoa" }
```

Payload de lançamento manual:

```json
{
  "person_id": "uuid-da-pessoa",
  "type": "charge",
  "amount": 100.5,
  "description": "Descrição opcional"
}
```

`type` deve ser `charge` ou `payment`, e `amount` deve ser maior que zero. O backend registra a data atual quando `occurred_at` não é enviado.

Payload de divisão de cartão:

```json
{
  "transaction_id": "uuid-da-transacao",
  "person_id": "uuid-da-pessoa",
  "is_integral": false,
  "amount_person": 50.25,
  "reference_month": "2026-09"
}
```

`reference_month` deve seguir `YYYY-MM`. Uma divisão existente para a mesma transação, pessoa e mês é atualizada em vez de duplicada.

## Regras de cálculo

- `card_total` é a soma de `amount_person` das divisões da pessoa no mês consultado.
- `manual_total` é a soma das cobranças menos a soma dos pagamentos.
- O valor apresentado para `manual_total` nunca fica abaixo de zero: o backend aplica `max(0, total)`.
- No resumo dos cards, os lançamentos manuais são consultados sem filtro de mês; portanto, o saldo manual representa o acumulado geral.
- Nos detalhes, a lista de compras é filtrada pelo mês selecionado, mas os lançamentos manuais retornam todos os registros da pessoa.
- Uma compra pode ser dividida entre pessoas, desde que a soma das parcelas não exceda o valor original.
- O front end exibe valores monetários em reais, mas deve enviar números JSON, sem símbolo de moeda.

## Requisitos para uma réplica

1. Reproduzir os IDs dos elementos ou atualizar todos os seletores usados pelo módulo.
2. Manter a separação entre o grid, o drawer e os três modais.
3. Implementar os estados de carregamento, lista vazia e erro em cada consulta.
4. Usar um drawer direito com transição horizontal e conteúdo interno rolável.
5. Manter layout responsivo: uma coluna no mobile, duas colunas no `sm` para os cards, três no `xl` e duas seções no drawer a partir de `lg`.
6. Formatar BRL com locale `pt-BR` e preservar os sinais de cobrança e pagamento.
7. Desabilitar compras já vinculadas e filtrar a busca no servidor.
8. Atualizar detalhes e resumo depois de toda mutação.
9. Escapar valores vindos da API antes de inseri-los em HTML. A implementação atual usa a função `seguro` para escapar `&`, `<`, `>`, aspas simples e aspas duplas.
10. Validar no backend valores positivos, mês no formato `YYYY-MM`, existência de pessoa/transação e limite das divisões.

## Checklist visual

- [ ] Fundo geral slate claro e cards brancos.
- [ ] Azul sky para valores de cartão e ações principais.
- [ ] Âmbar para saldo devedor no resumo.
- [ ] Verde para divisão integral e âmbar para parcial.
- [ ] Bordas finas slate, raios entre 8 e 14 px e sombras discretas.
- [ ] Material Symbols Outlined nos botões de ícone.
- [ ] Drawer com animação de entrada pela direita.
- [ ] Modais centralizados com backdrop escuro e blur.
- [ ] Controles de formulário com foco azul e largura responsiva.
- [ ] Listas longas com rolagem interna, sem alterar a largura do layout.
