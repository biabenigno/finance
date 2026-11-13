# Guia de Refatoração Visual: Implementação do Material Design (Google)

## 1. Instruções Críticas para a I.A. (Leia com Atenção)
- **NÃO QUEBRE NENHUMA FUNCIONALIDADE:** O objetivo desta atualização é **estritamente visual**. Nenhuma regra de negócio, chamada de API, fluxo de dados, lógica de estado ou funcionalidade interna do sistema deve ser alterada.
- **Preservação de Dados e Informações:** Todos os dados, textos e informações que atualmente aparecem na tela devem ser mantidos intactos. O trabalho consiste apenas em melhorar o posicionamento (layout), alinhamento, hierarquia visual, fontes, espaçamentos e cores.
- **Separação de Preocupações:** Se houver necessidade de reorganizar a estrutura HTML/DOM para aplicar o novo design (por exemplo, adicionar uma `div` extra para criar um Card), garanta que os atributos essenciais para o funcionamento do sistema (como `id`, `name`, `data-attributes` e classes usadas pelo JavaScript) continuem intactos e nos locais corretos.

## 2. O que é o Modelo de Design do Google (Material Design)?
A aplicação deve ser modernizada utilizando os princípios do **Material Design 3 (Material You)**, a linguagem visual do Google. Para garantir que a interface fique com a "cara do Google", as seguintes diretrizes devem ser aplicadas:

- **Uso do Espaço (Whitespace e Grids):** Utilize um sistema de espaçamento consistente, geralmente baseado em múltiplos de 8px (8px, 16px, 24px). A interface deve "respirar", sem elementos colados uns nos outros.
- **Tipografia Limpa:** O padrão Google utiliza a fonte `Roboto` ou `Google Sans` (a fonte open-source `Inter` é um excelente substituto). Crie uma hierarquia clara entre Títulos (grandes e expressivos), subtítulos e o corpo do texto.
- **Superfícies e Elevação (Sombras):** O Material Design não abusa de bordas duras; em vez disso, utiliza diferentes tons de fundo e sombras sutis (`box-shadow`) para separar elementos. Elementos interativos como botões, modais e cards flutuantes devem ter uma sensação tátil de profundidade.
- **Bordas Arredondadas (Border-Radius):** Os componentes devem adotar bordas suaves. Cards geralmente usam bordas de 12px a 24px. Botões de ação costumam ser no formato "pílula" (totalmente arredondados) ou levemente arredondados, dependendo da importância.
- **Feedback Visual:** Componentes interativos devem reagir ao usuário (mudança sutil de cor no hover, efeito *ripple* ao clicar).

## 3. Comportamento de Temas (Claro e Escuro)
A interface deve ser totalmente responsiva quanto ao tema e deve suportar **Modo Claro** e **Modo Escuro**.

- **Regra Principal:** O tema deve ser definido por padrão de acordo com a preferência do sistema operacional/navegador do usuário (utilizando `@media (prefers-color-scheme: dark)` no CSS).
- **Fallback Estrito:** Caso o sistema não consiga detectar a preferência ou a funcionalidade de detecção não esteja disponível, **a aplicação deve obrigatoriamente iniciar no Modo Escuro**.
- Recomenda-se adicionar um gatilho manual (toggle/switch) para que o usuário possa sobrescrever o tema, se desejar.

## 4. Paleta de Cores (Design Tokens)
Todas as cores **DEVEM ser configuradas utilizando Variáveis Nativas do CSS** (`:root` e seletores de tema escuro). Isso é obrigatório para garantir que as cores de destaque possam ser facilmente substituídas posteriormente sem refatorar o código inteiro.

Abaixo está a paleta dividida em tons neutros (estruturais) e tons de destaque (coloridos, que podem ser mudados depois).

### 4.1. Cores Neutras (Estrutura, Fundo e Texto)
Estas cores formam o esqueleto da interface.

**No Modo Escuro (Padrão/Preferencial):**
- `--bg-base`: `#121212` *(Fundo principal da aplicação, áreas vazias)*
- `--surface-1`: `#1E1E1E` *(Cards principal, barras de navegação superior/lateral)*
- `--surface-2`: `#2C2C2C` *(Elementos em destaque secundário, fundo de inputs, hover de cards)*
- `--text-primary`: `#E3E3E3` *(Textos principais, alta legibilidade)*
- `--text-secondary`: `#A0A0A0` *(Subtítulos, ícones neutros, textos auxiliares)*
- `--border`: `#333333` *(Linhas divisórias, apenas quando sombra não for aplicável)*

**No Modo Claro:**
- `--bg-base`: `#F8F9FA` *(Fundo principal, tom muito leve e frio)*
- `--surface-1`: `#FFFFFF` *(Cards principais, áreas de conteúdo brilhante)*
- `--surface-2`: `#F1F3F4` *(Fundos de input, áreas secundárias)*
- `--text-primary`: `#202124` *(Texto de alta ênfase)*
- `--text-secondary`: `#5F6368` *(Textos secundários, placeholders)*
- `--border`: `#DADCE0` *(Linhas divisórias sutis)*

### 4.2. Cores de Destaque / Ação (Modificáveis)
Estas variáveis devem ser aplicadas em botões, links, ícones ativos, botões flutuantes (FABs), alertas e focos de input. Por serem variáveis CSS, poderão ser alteradas pelo usuário ou dev num único arquivo central depois.

- **Cor Primária (Ações principais, botões "Call to Action", links):**
  - `--color-primary-dark`: `#8AB4F8` *(Azul claro no modo escuro)*
  - `--color-primary-light`: `#1A73E8` *(Azul vibrante no modo claro)*
- **Cor Primária Variante (Para estado Hover/Active do botão primário):**
  - `--color-primary-variant-dark`: `#AECBFA`
  - `--color-primary-variant-light`: `#174EA6`
- **Cor Secundária (Ações alternativas, ou indicações de sucesso):**
  - `--color-secondary-dark`: `#81C995` *(Verde suave)*
  - `--color-secondary-light`: `#1E8E3E` *(Verde sólido)*
- **Cor de Erro / Alerta Destrutivo (Apagar, Excluir, Alertas críticos):**
  - `--color-error-dark`: `#F28B82` *(Vermelho pálido)*
  - `--color-error-light`: `#D93025` *(Vermelho intenso)*

## 5. Estados de Carregamento (Loading States) e Feedback Visual
Para evitar que o usuário pense que a aplicação travou enquanto aguarda o processamento ou carregamento de dados, é **obrigatório** implementar estados de carregamento claros. O Material Design sugere as seguintes abordagens:

- **Skeleton Screens (Esqueletos de Carregamento):** Em vez de apresentar telas em branco durante o carregamento de dados, utilize componentes do tipo *Skeleton* (blocos ou formas geométricas em tons neutros, como `--surface-2`, com uma leve animação de pulso ou brilho contínuo da esquerda para a direita). Eles devem imitar a estrutura do conteúdo que será exibido (como textos, imagens e cards).
- **Indicadores de Progresso (Spinners/Barras):**
  - Utilize *Spinners Circulares* (com a `--color-primary-light` / `--color-primary-dark`) para ações específicas e menores, como botões de envio de formulário, onde o ícone ou texto do botão é temporariamente substituído pelo spinner.
  - Utilize *Barras Lineares* de progresso (indeterminadas) no topo da tela ou no topo de containers de dados ao buscar informações ou navegar de rota.
- **Transições Suaves:** Os elementos devem entrar e sair do estado de carregamento com transições suaves (fade-in), evitando mudanças bruscas e engasgos visuais na estrutura da página ("layout shifts").

## 6. Resumo para a Ação de Implementação
Ao codificar, estruture o CSS primeiramente com as variáveis. Mantenha os eventos e IDs do JS. Aplique classes que tragam os conceitos de `Superfícies` e `Elevações` do Material Design. Inclua a lógica visual de "carregando" onde dados assíncronos forem esperados. Transforme a aplicação em uma interface limpa, elegante e funcional baseada nas regras acima.
