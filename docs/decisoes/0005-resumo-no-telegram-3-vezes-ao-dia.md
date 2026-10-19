# 0005. Resumo no Telegram 3 vezes ao dia

Data: 2026-10-19

## Contexto

O dono quer que o robô colete o tempo todo, mas que o Telegram não mande mensagem toda hora: um resumo às 7:30,
ao meio-dia e às 19:00, no horário de Brasília. Até agora, o Telegram só avisava quando a coleta parava ou voltava.

## Decisão

- **Três resumos por dia**, às 7:30, 12:00 e 19:00 (America/Sao_Paulo). Fora desses horários, o Telegram não manda
  nada, nem aviso de falha: problemas entram no resumo seguinte. O aviso imediato "a coleta parou/voltou" deixa de
  existir; o caso de referência dele sai de `test_referencia.py` por esta decisão.
- **Quem manda**: a primeira rodada do robô depois do horário. Se ela atrasar mais de 3 horas, aquele resumo é
  pulado. O seguinte cobre o período inteiro desde o último resumo enviado, então nada se perde.
- **Nunca em dobro**: cada resumo enviado fica gravado no banco (tabela `resumo`, só inserção), com o horário a
  que se refere e o texto enviado. Sem banco permanente, nenhum resumo sai: o banco temporário não lembraria do
  anterior e mandaria um a cada rodada.
- **Período**: as notícias de que o robô soube (`conhecido_em`) desde o último resumo enviado. Assim, cada notícia
  entra em um resumo só, mesmo a de uma fonte que caiu e voltou. Notícia cuja data da fonte é de mais de 24 horas
  antes do período fica de fora, para uma fonte que volta depois de dias não despejar notícia velha.
- **Conteúdo**, montado por regra, sem IA (a fase 3 troca por um briefing redigido):
  - quantas notícias e de quantas fontes desde o último resumo;
  - os países mais citados, com o número do período anterior para comparar;
  - um destaque para cada um dos 3 países mais citados: a notícia mais recente com o país no título (sem repetir
    notícia entre países), com link. Na fase 1, o destaque passa a ser o maior evento do país;
  - fontes que falharam em alguma coleta desde o último resumo (quantas vezes e o motivo), e não só na rodada que
    manda o resumo; e a situação do agendador, se houver algo errado;
  - o link do site.
- Rede social não entra nas contagens (regra 4). Preço não entra no resumo (regra 8).

## Consequências

- O resumo das 7:30 chega por volta das 7:35, se o agendador do Supabase (decisão 0004) estiver ligado. Sem ele,
  chega quando o GitHub rodar o robô, o que pode levar horas, ou é pulado.
- Se o robô parar de vez, o resumo não chega. A falta do resumo é o sinal, e o site mostra o aviso de dados parados.
- Na fase 1, o resumo passa a listar eventos ("novos desde o último resumo, com grau de confirmação")
  em vez de notícias soltas.
