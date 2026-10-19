# Reconciliação do gabarito dev_19out

Conjunto: 236 manchetes (`dev_19out.jsonl`). Anotadores: `anotador1_dev_19out.json` e `anotador2_dev_19out.json`.
Gabarito final: `gabarito_dev_19out.json`, com 99 assuntos, 177 eventos (33 com 2 ou mais manchetes) e 32 dúvidas anotadas.
Todo id aparece exatamente uma vez. Isso foi conferido por script; nenhum id falta, se repete ou sobra.

## Concordância antes da reconciliação

| medida | valor |
|---|---|
| pares de manchetes (236 × 235 / 2) | 27.730 |
| pares com a mesma decisão (juntos nos dois ou separados nos dois) | 27.717 (99,95%) |
| pares divergentes | **13**, em 5 grupos, com 18 manchetes envolvidas |
| pares juntos nos dois / só no anotador 1 / só no anotador 2 | 100 / 10 / 3 |
| Jaccard dos pares juntos (medida mais exigente, ignora os pares separados por obviedade) | 0,885 |
| B-cubed (anotador 1 como referência) | P 0,987 · R 0,981 · F 0,984 |
| eventos / assuntos | 177 / 100 nos dois |

Os 99,95% saem altos porque quase todos os pares são obviamente separados. As medidas que contam são o Jaccard (0,885) e o B-cubed (0,984).
Além dos eventos, houve 2 divergências de **assunto**: a Itália (assunto à parte ou dentro da onda europeia) e a Ucrânia (um assunto só ou combates e diplomacia separados).

Depois da reconciliação, o gabarito tem B-cubed F 0,990 contra o anotador 1 (6 pares diferentes) e 0,994 contra o anotador 2 (7 pares diferentes). Cada divergência foi decidida caso a caso, sem média.

## Decisões, uma por divergência

| # | manchetes | anotador 1 | anotador 2 | decisão | motivo |
|---|---|---|---|---|---|
| 1 | 74 (France 24, "Papers react to polarising riots") | dentro dos distúrbios do fim de semana | evento próprio, `resenha` | **anotador 1** | É uma revista de imprensa de tema único sobre um evento específico, então entra nesse evento. `resenha` é só para revista com vários temas. |
| 2 | 31 (Meloni convoca reunião de emergência) × 141 (150 detidos em Milão) | separados | juntos | **anotador 1** | A manchete decide: a reunião de Meloni é resposta do governo, outro evento, como "Macron recusa a demissão" na França. O resumo de 31 cita as detenções, mas isso não muda o assunto da manchete. |
| 3 | 188 (Comissão Europeia condena a violência; 7º dia) × 76, 216 (6º dia, domingo) | juntos | separados | **anotador 2** | A manchete de 188 abre com outro ato (a condenação da Comissão Europeia) e o protesto é de outro dia. Na dúvida, não juntar. |
| 4 | 29, 140, 142, 144 (falas de Trump) | {29, 140, 144} + {142} | {29, 140} + {142, 144} | **anotador 2** | Seguimos o critério que os dois usaram para as falas de Rubio da mesma entrevista: separar por tema. Sanções ficam com sanções (29, 140, como 125 e 218) e o processo de paz com o processo de paz (144 "grande progresso" e 142 "Zelensky nunca quis encerrar", como 102, 110 e 126). O resumo de 198 mostra que "grande progresso" e a crítica a Zelensky foram ditos juntos. |
| 5 | 116 × 121 (Grupo Norte, mesmo dia) | separados | juntos | **anotador 2** | São dois números do mesmo boletim diário do porta-voz do Grupo Norte, ou seja, um só ato. Os dois anotadores já tinham juntado os dois números do balanço semanal de Marochko (96, 98). As duas manchetes são da TASS, então a junção não infla a contagem de fontes. |
| A | assunto da Itália | assunto próprio | dentro de "onda de protestos na França e na Europa" | **anotador 2** | É o mesmo fim de semana, e o assunto já tinha manchetes sobre a Europa toda: 99 e 131 (Kremlin sobre "distúrbios na Europa"), 61 (geração Z) e 92 (TASS). Na Itália, 80% dos detidos eram menores, o que combina com a onda liderada por jovens. Os eventos italianos continuam separados dos franceses. |
| B | assunto da Ucrânia | um assunto (guerra e negociações) | dois (combates; diplomacia) | **anotador 1** | Assunto é a história maior. 83 (ataque a Kiev e fala de Rubio na mesma manchete), 184 (falta de alerta: ataque ou polêmica da inteligência?) e 112 (atrito Trump-Zelensky e a operação militar) ligam os dois lados. Na França, os dois anotadores também puseram os distúrbios e a reação política num assunto só. |

## Fronteiras difíceis: regras que ficam para o anotador e para o algoritmo

1. **Manchete com dois fatos**: vale o fato que abre a manchete; o resumo só desempata. Exemplos: 188, 31, 83 e 58.
2. **Várias falas da mesma pessoa na mesma ocasião**: um evento por tema, não um por entrevista. Exemplos: Rubio (11/115/190; 64/113/125/218; 102/110/126) e Trump (29/140; 142/144).
3. **Mesmo tema, pessoas diferentes**: eventos separados. Exemplos: Trump × Rubio sobre as sanções; Nuñez × Macron.
4. **Resposta do governo × o próprio distúrbio**: eventos separados no mesmo assunto. Exemplos: Meloni × Milão; Macron × fim de semana na França.
5. **Boletim com vários números do mesmo autor e período**: um evento. Exemplos: Grupo Norte (116/121) e Marochko (96/98). Comunicados diferentes do Ministério da Defesa russo continuam separados (101 × 156).
6. **Protesto que se repete em dias seguidos**: separar quando o outro dia traz um ato novo na manchete. Exemplo: Albânia, 6º × 7º dia.
7. **Revista de imprensa de tema único**: entra no evento de que trata. Exemplo: 74.

As dúvidas que ficaram estão em `duvidas` no `gabarito_dev_19out.json`. Entre elas: limpeza × distúrbios (70, 73), Bolsa de Paris × euro (94, 118), e se 184 se refere ao ataque a Kiev ou à polêmica da inteligência.
