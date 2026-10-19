# Gabarito de eventos (fase 1)

Manchetes reais coletadas pelo robô, agrupadas em eventos e assuntos. Servem para medir o agrupamento da fase 1
(meta no "pronto quando" de `docs/plano.md`).

| Conjunto | Manchetes | Eventos | Eventos com 2 ou mais | Pares juntos | Uso |
|---|---|---|---|---|---|
| `dev_19out` | 236 | 177 | 33 | 108 | desenvolver e ajustar a regra |
| `teste_16out` | 284 | 220 | 30 | 145 | só medir; nunca ajustar a regra olhando este conjunto |

## Arquivos

- `<conjunto>.jsonl`: uma manchete por linha (`id`, `fonte`, `titulo`, `resumo`, `paises`). `paises` saiu da regra
  de países da época e não faz parte do gabarito. As manchetes vieram do log do robô: não têm link nem data. Cada
  conjunto é de um dia, então o gabarito não testa a janela de tempo do agrupamento.
- `gabarito_<conjunto>.json`: o resultado final. Cada assunto tem eventos; cada evento tem `tipo` (`fato`, `analise`
  ou `resenha`) e os `ids` das manchetes. Toda manchete está em exatamente um evento. `duvidas` lista os casos de
  fronteira.
- `anotador1_<conjunto>.json` e `anotador2_<conjunto>.json`: as duas anotações independentes.
- `reconciliacao_<conjunto>.md`: a concordância entre as duas e a decisão de cada divergência.

## Como foi feito

Duas anotações independentes, feitas pelo Claude em sessões separadas, seguindo as diretrizes abaixo. Depois, uma
reconciliação decidiu cada divergência, caso a caso. Os dois anotadores concordaram quase sempre sobre o que é o mesmo
evento (B-cubed F de 0,98 a 0,99). Sobre o assunto, concordaram bem menos (cerca de 64% dos pares no teste).
Por isso, a meta da fase 1 mede só os eventos. O dono confere uma amostra de 30 pares (item da fase 1).

O gabarito não marca grau de confirmação, tipo de evento nem fato × declaração. Esses rótulos, quando forem medidos,
entram aqui antes da regra.

## Diretrizes usadas

- **Evento**: um acontecimento específico (ação, incidente, decisão, declaração, ato oficial ou número divulgado),
  num lugar e num período curto (até uns 2 dias). Notícias que relatam o mesmo acontecimento são o mesmo evento,
  mesmo com ângulos, números ou idiomas diferentes. "Polícia prende 2.400 após protestos na França" e "Mais de mil
  policiais feridos nos protestos" são o mesmo evento; "Macron recusa a demissão do ministro do Interior" é outro,
  do mesmo assunto.
- **Assunto**: a história maior que junta eventos ligados. Um assunto pode ter um evento só.
- **Análise, entrevista, ao vivo, explicação ou revista de imprensa**: se trata de um evento específico, entra nele;
  se é ampla, vira um evento próprio com `tipo` `analise`. Revista de imprensa com vários temas é `resenha`.
- **Ato oficial**: cada ato é um evento. A notícia da imprensa sobre o mesmo ato entra no mesmo evento.
- **Na dúvida, não juntar**: juntar errado é pior que deixar separado.
