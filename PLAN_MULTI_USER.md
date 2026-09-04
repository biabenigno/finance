# Plano de Implementação: Arquitetura Multi-Usuários

Este documento detalha o roteiro técnico para expandir a aplicação e permitir a gestão e alternância de múltiplos perfis de usuários com isolamento completo de dados.

## 1. Banco de Dados (Supabase)

### Tabela `users`

Criar a tabela mestre de usuários para identificação dos perfis no sistema:

```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```

### Integridade Relacional

Vincular a coluna `user_id` da tabela `items` como chave estrangeira da tabela de usuários:

```sql
ALTER TABLE public.items
ADD CONSTRAINT fk_items_user
FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
```

## 2. Backend (FastAPI)

### Novo módulo: `app/modules/users`

Implementar endpoints para consumo do front-end:

- `GET /api/v1/users`: Consulta a lista de perfis cadastrados para o modal de troca.
- `POST /api/v1/users`: Registra novos usuários na plataforma.

### Parametrização dos endpoints existentes

- **Remoção de padrões hardcoded:** Remover o valor default estático do parâmetro `user_id` em todos os arquivos `router.py`.
- **Injeção de contexto:** Exigir obrigatoriamente a passagem do `user_id` via parâmetro de busca (`Query`) ou através do cabeçalho customizado `X-User-Id`.

## 3. Front-end (Header e Gestão de Estado)

### Gerenciador de estado: `frontend/src/core/state.js`

- `getUsuarioAtivo()`: Obtém o `user_id` ativo salvo no `localStorage`.
- `setUsuarioAtivo(usuario)`: Atualiza o `user_id` no `localStorage` e recarrega os componentes da tela.

### Menu de perfil: `frontend/src/components/header.js`

Substituir o botão de configurações por um menu de usuário:

- **Avatar/ícone de perfil:** Exibe o avatar ou as iniciais do usuário logado.

#### Dropdown

- Nome do usuário (apenas leitura).
- Botão **Trocar Usuário**: Dispara o modal de seleção de perfis.
- Botão **Gerenciar Dados**: Navega para a página `/src/pages/cards/cards.html`.

### Modal de seleção de usuários

- Faz a chamada à rota `GET /api/v1/users`.
- Renderiza os perfis disponíveis em lista/cards.

Ao selecionar um novo usuário:

- Salva a nova preferência via `setUsuarioAtivo()`.
- Fecha o modal.
- Atualiza os dados das faturas, extratos e cartões em tela chamando `carregarDados()`.

## 4. Roteiro Recomendado de Execução

1. Rodar o script SQL de criação da tabela `users` no Supabase.
2. Desenvolver o módulo `users` no backend FastAPI.
3. Implementar a persistência do `user_id` no `localStorage` do front-end.
4. Atualizar o `header.js` para incluir o menu de perfil e o modal de alternância.
5. Validar a alternância entre contas confirmando o isolamento de cartões e transações.
