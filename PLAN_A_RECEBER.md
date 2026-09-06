# Plano de Implementação: Módulo A Receber (Gestão de Terceiros)

Este documento estabelece a especificação técnica para a implementação do módulo **A Receber**, responsável pela gestão de despesas compartilhadas no cartão de crédito e pelo controle de saldos devedores informais entre usuários e terceiros.

## 1. Modelagem do Banco de Dados (Supabase) 

O módulo é composto por três tabelas principais integradas ao isolamento por usuário (`user_id`).

### Tabela `receivable_people`

Armazena o cadastro das pessoas com as quais o usuário compartilha despesas.

```sql
CREATE TABLE public.receivable_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```

### Tabela `card_splits`

Registra a alocação integral ou parcial de transações de cartão de crédito para uma pessoa em uma fatura específica.

```sql
CREATE TABLE public.card_splits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id TEXT NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES public.receivable_people(id) ON DELETE CASCADE,
    reference_month VARCHAR(7) NOT NULL, -- Formato YYYY-MM
    is_integral BOOLEAN DEFAULT FALSE NOT NULL,
    amount_person NUMERIC(10, 2) NOT NULL,
    total_transaction_amount NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_person_transaction_month UNIQUE (transaction_id, person_id, reference_month)
);
```

### Tabela `manual_debts`

Registra cobranças (`charge`) e pagamentos ou abatimentos (`payment`) fora da fatura do cartão.

```sql
CREATE TABLE public.manual_debts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES public.receivable_people(id) ON DELETE CASCADE,
    type VARCHAR(10) CHECK (type IN ('charge', 'payment')) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    description TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```

## 2. Rotas do Backend (`app/modules/receivables/router.py`)

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/api/v1/receivables/summary` | Retorna a lista de pessoas com o total de cartão no mês e o saldo devedor manual. |
| `GET` | `/api/v1/receivables/people/{id}` | Traz os detalhes da pessoa, incluindo os `card_splits` do mês e o histórico de `manual_debts`. |
| `POST` | `/api/v1/receivables/people` | Cadastra uma nova pessoa vinculada ao `user_id`. |
| `GET` | `/api/v1/receivables/people/{id}/card-transactions` | Lista compras da fatura filtrada disponíveis para alocação. |
| `POST` | `/api/v1/receivables/card-splits` | Vincula ou edita a divisão de uma compra de cartão para a pessoa. |
| `DELETE` | `/api/v1/receivables/card-splits/{id}` | Remove o vínculo de uma compra. |
| `POST` | `/api/v1/receivables/manual` | Registra uma nova cobrança (`charge`) ou pagamento (`payment`). |
| `PUT` | `/api/v1/receivables/manual/{id}` | Atualiza o valor ou a descrição de um lançamento manual. |
| `DELETE` | `/api/v1/receivables/manual/{id}` | Exclui um lançamento manual. |

### Regras de Negócio e Validações

#### Cálculo de saldo manual

O valor do saldo devedor informal é computado como:

$$
\sum \text{charge} - \sum \text{payment}
$$

Se o resultado for negativo, o saldo é zerado no resumo.

#### Validação de alocação de cartão

- O valor atribuído (`amount_person`) não pode exceder o valor total da compra.
- A soma de todas as divisões registradas em `card_splits` para uma mesma transação não pode ultrapassar o valor total original da compra.

## 3. Interface do Usuário e Fluxos (Front-end)

### Objetivo da tela

A tela **A Receber** acompanha valores que terceiros devem ao usuário. Ela reúne duas origens de saldo:

- **Cartão:** compras de uma fatura vinculadas a uma pessoa, integralmente ou por uma parcela.
- **Saldo Devedor:** cobranças e pagamentos registrados manualmente.

O fluxo principal é:

1. Exibir uma grade com todas as pessoas cadastradas.
2. Abrir os detalhes de uma pessoa em um drawer lateral.
3. Consultar uma fatura específica e vincular compras à pessoa.
4. Registrar, editar ou remover cobranças e pagamentos manuais.

### Arquivos envolvidos

- `frontend/src/pages/receivables/receivables.html`: estrutura HTML, drawer e modais.
- `frontend/src/pages/receivables/receivables.js`: estado da tela, renderização, eventos e chamadas de API.
- `frontend/src/core/api.js`: funções HTTP usadas pelo frontend.
- `backend/app/modules/receivables/router.py`: endpoints HTTP do módulo.
- `backend/app/modules/receivables/service.py`: regras de negócio e validações.
- `backend/app/modules/receivables/repository.py`: acesso ao Supabase.
- `backend/app/modules/receivables/schemas.py`: contratos Pydantic.
- `frontend/assets/css/global.css`: tokens e componentes CSS compartilhados.

### Composição visual

#### Layout global

- Fundo `bg-slate-100`, texto `text-slate-800` e fonte utilitária `font-sans`.
- Conteúdo em um container `max-w-6xl mx-auto`, com `p-4` no mobile e `p-6` a partir de `sm`.
- Drawer e modais com `position: fixed`.
- Ícones de ação usando Material Symbols Outlined.

#### Cabeçalho

- Texto auxiliar: `Receitas de terceiros`, em caixa alta, pequeno, semibold e cinza.
- Título: `A Receber`, tamanho `text-2xl`, negrito.
- Descrição: `Acompanhe faturas compartilhadas e saldos informais.`
- Botão à direita com ícone `person_add` e texto `Adicionar Pessoa`.
- No mobile, o cabeçalho vira uma coluna e o botão mantém apenas a largura necessária.

#### Grade de pessoas

O elemento `#receivable-grid` usa `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4`.

Cada pessoa é renderizada como um botão com a classe `card-financeiro`, `p-5` e alinhamento à esquerda. O card contém:

- nome da pessoa em `text-slate-800` e semibold;
- **Cartão · Fatura atual**, em `text-sky-700`;
- **Saldo Devedor**, em `text-amber-700`;
- hover com pequena elevação e sombra maior.

Quando não há pessoas, aparece uma mensagem centralizada com borda tracejada. Durante o carregamento, aparece `Carregando pessoas...`; em erro, a mensagem usa rose. Valores monetários devem usar `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })`.

#### Drawer de detalhes

O elemento `#person-drawer` é um painel lateral direito, com largura total no mobile e `max-w-3xl` em telas maiores. Ele usa fundo branco, `z-50`, `shadow-2xl`, começa com `translate-x-full` e entra com transição de 300 ms.

O cabeçalho mostra o rótulo `Detalhes`, o nome da pessoa e o botão `close`. O conteúdo fica em `#person-drawer-content`, com rolagem vertical e duas colunas a partir de `lg`.

##### Seção Cartão

- título `Cartão`;
- total da pessoa no mês selecionado em azul (`text-2xl text-sky-700`);
- seletor de mês da fatura;
- botão `Vincular compra`;
- lista de compras vinculadas.

Cada compra usa um artigo branco com borda, `rounded-xl`, `p-3` e sombra discreta. A primeira linha mostra banco e tipo da divisão:

- Integral: badge verde;
- Parcial: badge âmbar;
- Inter: badge laranja;
- Santander: badge vermelho;
- demais bancos: badge slate.

A compra mostra o valor devido pela pessoa em azul, o total original quando a divisão é parcial, descrição e data/hora. O menu `settings` oferece `Editar valor` e `Excluir vínculo`.

##### Seção Saldo Devedor

- título `Saldo Devedor`;
- total em azul;
- botão `add` para adicionar cobrança;
- botão `remove` para registrar pagamento;
- lista de lançamentos manuais.

Cobranças usam o prefixo `+` e pagamentos usam `-`. Cada item mostra descrição, data/hora e o menu com `Editar informações` e `Excluir lançamento`.

### Modais

Todos os modais usam `bg-slate-900/40`, `backdrop-blur-sm`, centralização com `flex`, `p-4`, card branco, `rounded-xl` e `shadow-xl`. Fechados, permanecem com `hidden`; abertos, removem `hidden` e adicionam `flex`.

#### Nova pessoa: `#person-modal`

- largura máxima `max-w-sm`;
- campo obrigatório `Nome`;
- botões `Cancelar` e `Cadastrar`;
- foco em `#new-person-name` ao abrir.

#### Lançamento manual: `#manual-modal`

- largura máxima `max-w-md`;
- título variável: `Adicionar cobrança`, `Registrar pagamento` ou `Editar informações`;
- campo numérico `Valor`, mínimo `0.01`, passo `0.01`;
- campo opcional `Descrição`;
- campo oculto `#manual-type`, com `charge` ou `payment`.

#### Vínculo de compra: `#card-modal`

- largura máxima `max-w-lg`;
- título inicial `Compras da fatura`;
- busca por descrição em `#card-purchase-search`;
- lista rolável de compras;
- após selecionar uma compra, exibe o formulário de divisão;
- seletor `Integral` ou `Parcial`;
- no modo parcial, mostra `Valor da pessoa`;
- o valor parcial não pode exceder o total da compra.

### Estado do frontend

O módulo mantém estas variáveis:

| Variável | Função |
| --- | --- |
| `pessoaAtual` | Pessoa aberta no drawer, inicialmente com `id` e depois com os dados completos. |
| `lancamentoManualEmEdicao` | ID do lançamento manual em edição; `null` significa criação. |
| `mesesFatura` | Meses retornados para a pessoa atual. |
| `mesFaturaSelecionado` | Mês atualmente selecionado. |

O mês corrente é obtido no formato `YYYY-MM`.

### Fluxos de interação

#### Carregamento inicial

`carregarPessoas()` chama `GET /api/v1/receivables/summary?mes=YYYY-MM`, atualiza o grid, cria um botão por pessoa e associa o clique a `abrirPessoa(id)`. Após qualquer mutação bem-sucedida, o grid é carregado novamente.

#### Abrir uma pessoa

`abrirPessoa(id)` salva a pessoa em `pessoaAtual`, abre o drawer, busca os meses disponíveis e prefere o mês atual. Caso ele não exista, usa o primeiro mês retornado ou o mês atual como fallback. Enquanto os detalhes carregam, mostra `Carregando extratos...`.

#### Trocar a fatura

O seletor `#person-month` chama `renderizarPessoa` no evento `change`, buscando novamente os detalhes do mês e mantendo os lançamentos manuais retornados pelo backend.

#### Vincular uma compra

1. `abrirCompras()` abre o modal e consulta as compras da pessoa e do mês.
2. A busca por descrição é enviada no parâmetro `busca` a cada evento `input`.
3. Compras já vinculadas ficam desabilitadas, opacas e exibem `Já vinculada`.
4. Uma compra disponível mostra descrição, valor, data e banco.
5. `selecionarCompra` troca a lista pelo formulário e seleciona `Integral`.
6. Ao escolher `Parcial`, o campo de valor fica visível.
7. Ao salvar, envia a divisão, fecha o modal e atualiza detalhes e grid.

#### Criar ou editar lançamento manual

`abrirManual('charge')` abre o formulário de cobrança e `abrirManual('payment')` abre o de pagamento. A edição preenche os campos existentes e guarda o ID em `lancamentoManualEmEdicao`.

- criação envia `person_id`, `type`, `amount` e `description`;
- edição envia `type`, `amount` e `description` ao endpoint do ID;
- sucesso fecha o modal, limpa o formulário, atualiza o drawer e recarrega o grid.

Antes de excluir uma divisão ou lançamento manual, a interface pede confirmação. Erros de escrita são mostrados ao usuário.

#### Fechar superfícies

- `fecharPessoa()` move o drawer para `translate-x-full` e limpa `pessoaAtual`;
- os três modais voltam a `hidden` e removem `flex`;
- fechar o modal de compra restaura a lista para que o próximo uso comece no estado inicial.

### Contrato da API

Todas as chamadas passam por `apiRequest`, que executa `fetch`, interpreta JSON e lança `Error` usando `data.detail` em respostas malsucedidas.

| Método | Endpoint | Uso |
| --- | --- | --- |
| `GET` | `/api/v1/receivables/summary?mes=YYYY-MM` | Cards da grade. |
| `GET` | `/api/v1/receivables/people/{id}?mes=YYYY-MM` | Detalhes, divisões e lançamentos. |
| `GET` | `/api/v1/receivables/people/{id}/card-transactions?mes=YYYY-MM&busca=...` | Compras disponíveis para vínculo. |
| `GET` | `/api/v1/receivables/people/{id}/card-months` | Meses com compras de fatura. |
| `POST` | `/api/v1/receivables/people` | Cria pessoa. |
| `POST` | `/api/v1/receivables/manual` | Cria cobrança ou pagamento. |
| `PUT` | `/api/v1/receivables/manual/{id}` | Edita lançamento manual. |
| `DELETE` | `/api/v1/receivables/manual/{id}` | Exclui lançamento manual. |
| `POST` | `/api/v1/receivables/card-splits` | Cria ou atualiza divisão de compra. |
| `DELETE` | `/api/v1/receivables/card-splits/{id}` | Exclui vínculo de compra. |

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

`reference_month` deve seguir `YYYY-MM`. Uma divisão existente para a mesma transação, pessoa e mês deve ser atualizada em vez de duplicada.

### Regras de cálculo e segurança

- `card_total` é a soma de `amount_person` das divisões no mês consultado.
- `manual_total` é a soma das cobranças menos a soma dos pagamentos.
- O saldo manual nunca fica abaixo de zero no resumo.
- No resumo dos cards, lançamentos manuais representam o acumulado geral.
- Nos detalhes, compras são filtradas pelo mês, mas lançamentos manuais retornam o histórico da pessoa.
- Uma compra pode ser dividida entre pessoas, desde que a soma não exceda o valor original.
- O frontend exibe valores em reais, mas envia números JSON sem símbolo de moeda.
- Valores recebidos da API devem ser escapados antes de entrar em HTML.
- O backend valida valores positivos, mês no formato `YYYY-MM`, existência de pessoa/transação e limite das divisões.

### Checklist visual

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

### Grade Principal de Pessoas

- Exibe cards com o nome de cada pessoa.
- Apresenta dois totais: **Cartão (Fatura Atual)** e **Saldo Devedor**.
- Possui botão para acionar o modal de Nova Pessoa.

### Drawer de Detalhes da Pessoa

#### Seção Cartão

- Seletor de mês de fatura.
- Exibição das compras vinculadas.
- Ação para abrir o modal de seleção e alocação de compras da fatura.

#### Seção Saldo Devedor

- Botões de ação rápida para **Adicionar Cobrança (+)** ou **Debitar Pagamento (-)**.
- Lista histórica de movimentações manuais com opção de edição e exclusão.

### Modais de Vínculo de Compras

- Permite pesquisar lançamentos do cartão na fatura selecionada.
- Ao escolher a compra, o usuário define a modalidade:
  - **Integral:** 100% do valor.
  - **Parcial:** informa o valor desejado.

## 4. Roteiro Recomendado de Execução

1. Executar os scripts SQL para criação das tabelas `receivable_people`, `card_splits` e `manual_debts` no Supabase.
2. Criar os schemas Pydantic e o repositório no backend em `app/modules/receivables`.
3. Implementar a camada de serviço com as validações de limite de alocação de compras.
4. Criar a página `src/pages/receivables/receivables.html` e a lógica do front-end em `receivables.js`.
5. Validar o fluxo completo de vinculação de compras, cálculo de saldo manual e filtro por mês de fatura.
