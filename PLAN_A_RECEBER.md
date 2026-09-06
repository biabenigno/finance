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
