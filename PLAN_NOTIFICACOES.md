# Notificações

Documentação funcional e visual do sistema de notificações do Finanças Pluggy. A notificação é uma mensagem persistida no banco que informa eventos de sincronização ou de integração e pode ser consultada pelo drawer global da aplicação.

## Visão geral

As notificações ficam disponíveis em todas as páginas porque o drawer é incluído pelo template base. O usuário acessa o recurso pelo botão de sino na topbar.

O comportamento principal é:

1. Consultar as notificações ao carregar a aplicação.
2. Mostrar uma bolinha vermelha quando existe pelo menos uma notificação não lida.
3. Atualizar essa bolinha a cada 5 segundos por polling.
4. Abrir um drawer lateral com a lista ordenada da mais recente para a mais antiga.
5. Permitir marcar uma notificação como lida ou excluí-la.
6. Permitir marcar todas as notificações não lidas como lidas.

## Arquivos envolvidos

- [ui/templates/components/drawerNotifications.html](ui/templates/components/drawerNotifications.html): estrutura do drawer.
- [ui/templates/components/topbar.html](ui/templates/components/topbar.html): botão do sino e badge.
- [ui/templates/base.html](ui/templates/base.html): inclusão global do drawer e overlay.
- [ui/static/js/main.js](ui/static/js/main.js): carregamento, polling, ações e exposição dos handlers globais.
- [ui/static/js/ui.js](ui/static/js/ui.js): abertura do drawer, formatação de data, badge e renderização dos cards.
- [ui/static/js/api.js](ui/static/js/api.js): funções HTTP.
- [api/app/routers/notifications.py](api/app/routers/notifications.py): endpoints consumidos pela interface.
- [api/app/routers/transactions.py](api/app/routers/transactions.py): cria notificação após sincronização de cartões.
- [api/app/routers/webhooks.py](api/app/routers/webhooks.py): cria notificação ao processar evento externo.

## Aparência e layout

### Botão na topbar

O botão fica no lado direito da barra superior, junto do botão de sincronização:

- ícone Material Symbols `notifications`;
- padding `p-2`;
- texto slate;
- borda `border-slate-200`;
- raio `rounded-lg`;
- hover com fundo slate claro e texto mais escuro;
- `title="Notificações"` para tooltip nativo.

O elemento tem `position: relative` para posicionar o badge.

### Badge de não lidas

O badge é o elemento `#notif-badge`:

- círculo de 8 px (`w-2 h-2`);
- fundo `bg-rose-500`;
- posição absoluta no canto superior direito;
- fica oculto com `hidden` quando não há item com `read === false`.

O badge não mostra quantidade. Ele é apenas um indicador visual de que existe algo novo.

### Drawer

O drawer é o `<aside id="drawer-notifications">` e possui:

- posição fixa no topo e à direita;
- altura total da viewport (`h-screen`);
- largura `w-80` no mobile e `w-96` a partir de `sm`;
- fundo branco, sombra `shadow-2xl` e borda esquerda slate;
- `z-50`;
- início fora da tela com `translate-x-full`;
- transição horizontal de 300 ms com `ease-in-out`.

O drawer tem três regiões:

1. **Cabeçalho:** ícone de sino, título `Notificações` e botão de fechar.
2. **Barra de ação:** botão `Ler todas` alinhado à direita.
3. **Lista:** área flexível e rolável, com padding `p-6` e espaçamento vertical `space-y-3`.

O overlay global `#drawer-overlay`, definido no [base.html](ui/templates/base.html), escurece e desfoca o restante da aplicação. Ao clicar nele, todos os drawers são fechados.

### Card de notificação

Cada item é renderizado como:

- `<div>` com ID `notif-{id}`;
- padding `p-3.5`;
- borda e raio `rounded-xl`;
- texto pequeno `text-xs`;
- espaçamento vertical `space-y-2`;
- transição de aparência.

O conteúdo do card é dividido em:

- primeira linha: título em semibold à esquerda e data relativa à direita;
- mensagem com texto slate e `leading-relaxed`;
- rodapé separado por uma borda superior clara;
- ações alinhadas à direita.

Estado visual:

| Estado | Classes principais | Aparência |
| --- | --- | --- |
| Não lida | `bg-white border-slate-200` | Card branco, com destaque normal. |
| Lida | `bg-slate-50 opacity-60` | Card esmaecido, indicando que já foi visto. |

O botão de leitura usa `check_circle`. Em item não lido, o ícone é slate e fica verde no hover. Em item lido, permanece verde. O botão de exclusão usa `delete`, fica slate e muda para rose no hover. Ambos devem ter `title` para identificar a ação sem adicionar texto ao layout.

## Estado e ciclo de vida

O sistema não mantém uma store dedicada para notificações. O estado exibido vem diretamente do resultado mais recente da API.

### Inicialização

No evento `DOMContentLoaded`, [main.js](ui/static/js/main.js) executa:

```text
carregarNotificacoes()
verificarNotificacoes()
setInterval(verificarNotificacoes, 5000)
```

`carregarNotificacoes()` busca a lista, atualiza o badge e renderiza o drawer. `verificarNotificacoes()` busca apenas para recalcular o badge, sem alterar a lista aberta.

### Ao abrir

O botão chama `abrirDrawer('drawer-notifications')`. A função compartilhada:

1. localiza o drawer;
2. mostra o overlay;
3. remove `translate-x-full`;
4. chama `carregarNotificacoes()` novamente quando o drawer é o de notificações.

Esse reload garante que a lista esteja atualizada no momento em que o usuário a consulta.

### Ao fechar

`fecharDrawer('drawer-notifications')` adiciona novamente `translate-x-full` e esconde o overlay. O mesmo resultado ocorre ao clicar no overlay global, que chama `fecharTodosDrawers()`.

## Formatação de datas

`formatarDataNotificacao` recebe `created_at` e aplica estas regras:

- sem data: `Agora`;
- criada hoje: exibe somente hora e minuto, por exemplo `14:32`;
- criada ontem: exibe `Ontem`;
- demais datas: exibe `dd/mm/aaaa`.

A comparação é feita no horário local do navegador. A data é interpretada pelo construtor `new Date(dateString)`.

## Ações disponíveis

### Marcar uma como lida

O botão de check chama `marcarComoVista(id)`:

1. envia `PATCH /api/notifications/{id}/read`;
2. adiciona `bg-slate-50` e `opacity-60` ao card atual;
3. consulta novamente as notificações para recalcular o badge.

O texto do card não é reconstruído nesse fluxo; a alteração visual é aplicada diretamente no elemento existente.

### Marcar todas como lidas

O botão `Ler todas` chama `marcarTodasComoVistas()`:

1. busca a lista atual;
2. filtra somente itens em que `read` é falso;
3. envia um `PATCH` para cada item em paralelo com `Promise.all`;
4. recarrega lista e badge ao final.

Se não houver itens não lidos, nenhuma chamada de atualização é feita, mas a lista ainda é recarregada.

### Excluir uma

O botão de lixeira chama `deletarNotificacao(id)`:

1. envia `DELETE /api/notifications/{id}`;
2. remove o card `#notif-{id}` do DOM;
3. consulta novamente a API para atualizar o badge.

Não há confirmação antes da exclusão individual na implementação atual.

### Erros

Falhas no carregamento, leitura ou exclusão são registradas com `console.error`. A lista existente não é substituída por uma mensagem de erro e o usuário não recebe `alert` nessas ações.

Uma réplica pode manter esse comportamento para ser fiel ao sistema atual, mas deve considerar uma mensagem visual de erro se o objetivo for melhorar a acessibilidade e a percepção de falha.

## Contrato da API

As funções de [api.js](ui/static/js/api.js) usam `fetch`, esperam JSON e lançam um `Error` com `data.detail` quando `response.ok` é falso.

| Método | Endpoint | Uso |
| --- | --- | --- |
| GET | `/api/notifications` | Lista notificações em ordem decrescente de `created_at`. |
| PATCH | `/api/notifications/{id}/read` | Define `read` como `true`. |
| DELETE | `/api/notifications/{id}` | Remove a notificação. |

Resposta esperada do GET:

```json
[
  {
    "id": "uuid",
    "title": "Sincronização de Cartões",
    "message": "Sincronização concluída: 12 transações processadas.",
    "type": "sucesso",
    "read": false,
    "created_at": "2026-09-06T14:32:00+00:00"
  }
]
```

O front end utiliza diretamente `id`, `title`, `message`, `read` e `created_at`. O campo `type` é persistido, mas atualmente não altera a cor, o ícone ou o layout do card.

## Origem das notificações

### Sincronização de cartões

Depois de processar uma sincronização, o endpoint de transações cria uma notificação com:

- título `Sincronização de Cartões`;
- mensagem informando total processado, novas transações e atualizações;
- `type` `sucesso` quando há novas transações ou `info` quando não há novas;
- `read: false`;
- `created_at` em UTC.

O drawer de sincronização também chama `carregarNotificacoes()` quando encontra novas transações, fazendo a nova notificação aparecer imediatamente.

### Webhook

Ao processar um evento externo, o webhook salva uma notificação com dados da transação, como:

- `transaction_id`;
- `bank_name`;
- `description`;
- `amount`.

Esse caminho precisa estar alinhado ao schema da tabela `notifications`. Como o renderer do drawer espera `title`, `message`, `read` e `created_at`, a tabela deve fornecer defaults ou o backend deve normalizar o registro antes de retorná-lo. Sem isso, uma notificação criada pelo webhook pode aparecer sem título, mensagem ou estado visual correto.

## Modelo de dados mínimo

Para o drawer atual funcionar de forma previsível, a tabela `notifications` deve possuir pelo menos:

| Campo | Tipo sugerido | Obrigatório | Função |
| --- | --- | --- | --- |
| `id` | UUID | Sim | Identificador usado nos botões e endpoints. |
| `title` | Texto | Sim | Cabeçalho do card. |
| `message` | Texto | Sim | Corpo da notificação. |
| `type` | Texto | Não | Classificação persistida, ainda sem efeito visual. |
| `read` | Booleano | Sim | Controla badge e estado esmaecido. Default recomendado: `false`. |
| `created_at` | Timestamp | Sim | Ordenação e data relativa. Default recomendado: agora em UTC. |

Campos específicos da origem, como `transaction_id`, `bank_name`, `description` e `amount`, podem ser mantidos para auditoria ou para uma futura ação ao clicar na notificação.

## Segurança e robustez da réplica

- Escapar `title` e `message` antes de interpolar valores em `innerHTML`. A implementação atual insere esses campos diretamente; uma réplica deve aplicar escape HTML ou construir nós DOM com `textContent`.
- Codificar o ID com `encodeURIComponent` nas URLs.
- Ordenar no backend por `created_at DESC` para manter a ordem consistente.
- Tratar `read` explicitamente como booleano; não usar apenas a existência do campo.
- Evitar sobreposição de polling: se a consulta a cada 5 segundos puder demorar, usar um lock ou agendamento que aguarde a requisição anterior.
- Considerar feedback visual para erro de rede, pois o comportamento atual apenas registra a falha no console.
- Manter o drawer acessível, com foco inicial no título ou botão de fechar, fechamento por `Escape` e atributos `aria-label` nos botões de ícone.

## Checklist para replicação

- [ ] Botão de sino na topbar com badge vermelho ocultável.
- [ ] Drawer direito responsivo, com overlay e animação de 300 ms.
- [ ] Cabeçalho com sino, título e botão de fechar.
- [ ] Botão `Ler todas` no separador abaixo do cabeçalho.
- [ ] Lista rolável com estados carregando, vazia e preenchida.
- [ ] Card com título, data relativa, mensagem e ações de leitura/exclusão.
- [ ] Card lido com fundo slate claro e opacidade reduzida.
- [ ] Polling do badge a cada 5 segundos.
- [ ] Reload completo ao abrir o drawer.
- [ ] PATCH individual e em lote para leitura.
- [ ] DELETE individual com remoção imediata do DOM.
- [ ] Integração com notificações criadas por sincronização e webhook.
- [ ] Defaults ou normalização para todos os campos usados pelo renderer.
