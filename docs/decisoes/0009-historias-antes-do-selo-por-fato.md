# 0009. Histórias antes do selo por fato

Data: 2026-10-20

## Contexto

A fase 1 previa juntar notícias em eventos (o mesmo fato) e dar a cada evento um grau de confirmação. Medida no
gabarito (`jobs/estudos/eventos/LEIAME.md`), a melhor regra gratuita, que compara países, nomes próprios, números e
palavras de ação:

- acerta a **mesma história**: dos pares que ela junta, 88% a 100% são da mesma história, nos dois dias anotados;
- não separa **fatos vizinhos** da mesma história: num dia que ela não tinha visto, só 72% a 79% dos pares juntados
  eram o mesmo fato ("Trump aprova a execução" × "Trump cancela a transmissão da execução").

Vetores de frase de modelos gratuitos foram piores. Um selo de "corroborado" em cima de um agrupamento que erra um
em quatro diria que algo foi confirmado quando não foi. O dono escolheu, em 20/10, começar pelas histórias.

## Decisão

- **Histórias**: cada notícia nova entra na história da notícia mais parecida das últimas 48 horas, ou abre uma
  história nova (regra `historias-0.1`, limiar 1,6, em `domain/historias.py`). Sem IA (regra 7).
  - `historias-0.2` (20/10, no mesmo dia): em produção apareceram correntes, como uma história de chuva em Istambul
    que puxou 18 notícias de 9 países (A parece com B, B com C, e C não tem nada com A). A notícia nova passa a
    precisar também de nota 1,2 com a primeira notícia da história, e a primeira tem de estar na janela. No dia
    19/10 o acerto sobe de 95% para 97%; no dia 16/10 fica em 88%. As ligações feitas pela 0.1 ficam como estão.
- **Gravação**: tabela `historia_documento`, só de inserção. Cada notícia ganha uma ligação, que nunca muda
  (regra 2), com a data em que o robô a fez e a versão da regra. A história recebe o id da primeira notícia dela.
  Rede social não entra (regra 4).
- **O que se mostra**: quantas notícias, quantas fontes e quantas **vozes independentes** (donos diferentes, pela
  ficha da decisão 0008) cobrem cada história. É cobertura, não confirmação, e o site e o resumo dizem isso.
- **Onde**: página Histórias no site e, no resumo do Telegram, as 3 histórias do período com mais vozes.
- **Sem selo por fato por enquanto.** Ele volta quando houver um jeito de juntar por fato com pelo menos 90% de
  acerto num dia novo: uma regra nova, com mais dias anotados, ou uma IA gratuita lendo os pares, o que pediria mudar
  a regra 7 por escrito.

## Consequências

- A meta por fato da decisão 0006 passa para a etapa do selo. A fase 1 mede a regra de histórias num dia novo
  anotado (meta: 90% dos pares juntados são da mesma história).
- A regra junta pouco: prefere deixar separado a juntar errado, então uma história grande pode aparecer em pedaços.
- A primeira rodada liga todas as notícias já guardadas, em ordem de chegada, com a janela de 48 horas.
