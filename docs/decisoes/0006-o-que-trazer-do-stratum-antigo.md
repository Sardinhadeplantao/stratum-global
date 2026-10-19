# 0006. O que trazer do STRATUM antigo

Data: 2026-10-19

## Contexto

O dono enviou dois PDFs do sistema anterior, "só como possibilidades":

- o texto de visão (STRATUM ORIGINAL, 92 páginas);
- o manual da versão seguinte (Stratum Manual, 41 páginas).

Seis leituras independentes tiraram cerca de 400 itens, que viraram 146 ideias únicas. Uma crítica conferiu cada
recomendação contra as regras do CLAUDE.md, contra o custo zero e contra o gabarito da fase 1.
Os PDFs não entram no repositório.

Os dois começam por outro lugar:

- o manual começa pelos fluxos medidos (dinheiro público, comércio, capacidade, quase tudo dos EUA) e só aceita
  notícia ligada a um fluxo;
- o original começa por estudo e teses de investimento, e termina em carteira e assinatura.

## Decisão

- **A ordem do plano continua**: primeiro notícias viram eventos, no mundo todo; mercados na fase 2, fluxos na 4,
  grafo e hipóteses na 5. Motivos:
  - o projeto quer saber o que acontece hoje, e os fluxos saem por mês ou por trimestre;
  - os fluxos do manual são quase todos dos EUA; começar por eles faria um monitor de Washington, não do mundo;
  - a régua dos fluxos é a parte mais pesada: pelo próprio manual, o uso diário só viria em uns 3 meses;
  - a coleta e o gabarito dos eventos já existem.
- **Do manual vem o rigor**:
  - "corroborado" exige fontes independentes de verdade;
  - volume de notícia mede atenção, não importância;
  - o sistema mede o próprio acerto, com meta escrita antes de medir;
  - cada número guarda a versão da regra que o produziu.
- **Nada de carteira, nota de empresa ou recomendação.** Vale a regra de ouro do texto original: não prever o futuro,
  e sim mapear as forças que podem produzi-lo. Do manual vem a lista do que isso exclui: guerra, eleição ou preço;
  compra ou venda. Na fase 5, as "teses" viram hipóteses verificáveis com placar, e o placar mostra também as
  erradas. Motivos:
  - regras 7 e 8;
  - ACLED, OpenSanctions e dados de mercado não oficiais são só para uso não comercial;
  - o próprio original avisa que começar pela carteira vira máquina de confirmar o que já se acha.

  A regra de ouro fica no plano e na tela Método, e não vira regra do CLAUDE.md. As hipóteses da fase 5 têm prazo e
  probabilidade, ou seja, são previsões verificáveis; uma regra "não prever" brigaria com elas.
- **Largo no monitor, estreito na profundidade**: os eventos são do mundo todo. As camadas caras da fase 5
  começam por um piloto, EUA × China em chips e terras raras.
- **Ficam como estão**:
  - só os 3 resumos do Telegram (decisão 0005);
  - só título, link e trecho de cada notícia (decisão 0001);
  - IA opcional e gratuita (regras 7 e 11);
  - robô no GitHub Actions, com banco no Supabase (decisões 0001 e 0004).
- A fase 1 ganha os itens dos PDFs que cabem nela, em duas voltas, e um "pronto quando" com número.
  O detalhe das fases 2 a 5 vai para `docs/ideias.md`, como manda o CLAUDE.md.
- O gabarito de eventos sai da pasta temporária da sessão e entra no repositório (`jobs/tests/gabarito/`).
  Ele foi feito pelo Claude, em duas anotações independentes e reconciliadas. O dono confere uma amostra de 30 pares,
  e o Método diz isso.
- **Regra 12**: segredo que aparecer em código, log, mensagem de erro, conversa ou captura de tela é trocado no mesmo
  dia, como já pedia o manual antigo.

## Consequências

- O "pronto quando" da fase 1 passa a ter uma meta medida, fixada antes de o agrupamento existir. No gabarito de
  teste:
  - pelo menos 90% dos pares que o sistema junta estão certos;
  - ele encontra pelo menos 60% dos pares certos;
  - em pelo menos metade dos 30 eventos com 2 ou mais manchetes, ele junta ao menos duas delas.

  A meta é sobre os pares porque quase todo evento tem uma manchete só: não juntar nada já tira 0,87 de 1 na medida
  usual (B-cubed). A terceira condição existe porque os pares se concentram nos eventos grandes: no teste, os 5
  maiores somam 65% dos pares.
- Com as 11 fontes de hoje, a maioria dos eventos vai sair "relatado" (uma fonte só). Além disso, 36% das manchetes
  do gabarito são da TASS. Isso é honesto, e o que faz "corroborado" aparecer é ampliar as fontes.
- A decisão 0001 previa guardar o detalhe das notícias por uns 90 dias, o que conflita com a regra 2.
  A fase 1 mede o banco e decide a retenção.
- O Supabase gratuito não faz cópia de segurança, e o banco só recebe inserções. Por isso, a cópia semanal vem
  antes do resto da fase 1.
- Ficam descartados:
  - carteira e assinatura;
  - cor por julgamento ("tensão alta");
  - previsões e conflitos "potenciais";
  - ficha de ator escrita à mão;
  - o vocabulário do Senhor dos Anéis;
  - fontes pagas (Reuters, Bloomberg, Financial Times) e IA paga;
  - servidor ligado o tempo todo;
  - aviso na hora;
  - guardar o documento inteiro.
