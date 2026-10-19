# Reconciliação do gabarito teste_16out

Conjunto: 284 manchetes (`teste_16out.jsonl`). Anotadores: `anotador1_teste_16out.json` (A1) e `anotador2_teste_16out.json` (A2).

## Concordância antes da revisão (A1 x A2, nível de evento)

| medida | valor |
|---|---|
| eventos | A1 220, A2 220 |
| pares de manchetes juntos | A1 150, A2 139, em ambos 137 |
| acordo sobre todos os 40.186 pares | 99,96% (15 pares divergentes) |
| Jaccard dos pares juntos | 0,901 |
| B-cubed (A1 como referência) | precisão 0,988, cobertura 0,993, F 0,990 |
| Rand ajustado (ARI) | 0,948 |

Os dois anotadores concordaram quase sempre sobre o que é o mesmo evento. As diferenças maiores ficaram nos **assuntos**:
881 pares no mesmo assunto em A1, 892 em A2, só 692 em comum. Houve também 3 divergências de **tipo**.

## Divergências de evento: 4 casos (15 pares)

| ids | A1 | A2 | decisão | motivo |
|---|---|---|---|---|
| 23 com 6, 7, 10, 27, 48, 101 | junto do ataque de 16/10 | análise à parte | **A2: separado, `analise`** | 23 fala de ataques no plural ("pogroms escalate"), sem local nem a fotojornalista ferida. É uma peça ampla sobre a onda, não sobre o ataque. 6 fica no evento porque cita Turmus Ayya. |
| 162 com o evento de Bruxelas | junto | assunto Starlink | **A1: junto** | 109 ("Ukraine is dependent on Starlink, Zelensky says in Brussels") mostra que a fala sobre Starlink foi feita em Bruxelas, no mesmo dia. 162 relata essa fala. 132 (Patriot) continua separado, porque nada o liga a Bruxelas. |
| 175 e 195 | separados | juntos | **A2: juntos** | São do mesmo dia, da TASS e sobre o mesmo tema. 195 nomeia o vice-ministro Tavakoli. 175 cita "o funcionário" e trata de gás, a área dele. Os dois anotadores usaram a regra "mesmo falante, mesmo dia, uma declaração" (Novak, Kobyakov, Lavrov). A1 juntou 176 a Tsivilev sem nome, e aqui aplico o mesmo critério. Fica em `duvidas`. |
| 245 e 253 | separados (253 `analise`) | juntos (`fato`) | **A1: separados** | 253 é uma análise de vários ataques com drones no mar Negro e do temor de escalada. Não é a notícia do navio que afundou (245). Os "dois mortos" podem ser os mesmos, mas a análise é ampla. Pela diretriz, juntar errado é pior que deixar separado. |

## Divergências de tipo: 3 casos

- **52 (turismo de Vermont cai com a guerra comercial): `analise` (A2).** É uma reportagem de tendência, sem ato, incidente ou número divulgado. Segue o mesmo critério da reportagem sobre fome em Oleshki (84), que os dois marcaram como análise.
- **85 (mais estrangeiros barrados na Argentina): `analise` (A2).** Também é reportagem de tendência. O caso do jornalista barrado (dia 12) serve só de gancho.
- **117 ("No, this oil tanker didn't carry Russian diesel"): `analise` (A1).** Uma checagem explica e desmente uma alegação, não relata um acontecimento novo.

## Divergências de assunto: decisões de fronteira

Critério: o assunto junta eventos **ligados por uma mesma história**. País ou área em comum não basta para juntar.

- **Ucrânia**: mantive a divisão mais fina de A1. As ligações aparecem no texto: refinarias e retaliação (39/254, 216, 278), navios no mar Negro (245, 253), ajuda militar e interceptadores (132, 184, 160, 283), Starlink e a ida a Bruxelas. A2 juntou tudo em "ataques e combates" e "atrito com Trump". Sachs (127) e o senador russo (213) ficaram no assunto geral da guerra, que passou a se chamar "frente de combate e comentários gerais".
- **Energia**: segui A2. A Semana Russa de Energia ficou separada de "Energia na Europa antes do inverno" (134, 154, 224), porque são histórias diferentes.
- **Rússia–Irã**: segui A2. Lavrov no Irã (135) e Tavakoli (175/195) formam um assunto próprio. A1 os tinha espalhado entre "energia" e "guerra com o Irã".
- **Fora da guerra com o Irã**: 156 (falta de munição antimíssil nos EUA até 2030) e 279 (renúncia do ministro do Petróleo, "no reason given") ficaram em assuntos próprios (A2). O texto não liga nenhum dos dois à guerra.
- **Gaza**: 226 ("From Iraq to Gaza: A Long Trail of Damage", sem resumo) ficou em assunto próprio (A2). É uma peça ampla que não trata da situação humanitária atual.
- **EUA**: o assunto das eleições de meio de mandato ficou com 86, 92, 107, 120 e 256. As cartas suspeitas (43) ficaram de fora (A1), porque são um incidente de segurança que só tangencia a eleição. O super PAC (232) também ficou de fora (A2), porque trata de propaganda oficial, não da eleição.
- **Canadá**: nenhum dos dois anotadores fez assim. Juntei o turismo de Vermont (52) a Carney e Alberta (74/263), porque as duas notícias tratam da tensão entre Canadá e EUA. UE–Canadá (108) ficou à parte.
- **Separados por não terem ligação (A2)**: 11/223 (Guterres e a candidata à sucessão), 51/62 (China) e 207/209 (ciência no Ártico). Nesses três pares, só país ou área eram comuns.

## Resultado

- `gabarito_teste_16out.json`: 125 assuntos e 220 eventos, dos quais 30 têm duas ou mais manchetes. Tipos: 176 `fato`, 42 `analise`, 2 `resenha`. 29 dúvidas anotadas.
- Checagem por script: os 284 ids aparecem exatamente uma vez cada, sem id faltando ou sobrando, com ids de evento e assunto únicos.
- Concordância de cada anotador com o gabarito final, no nível de evento: A1 B-cubed F 0,995 (7 pares divergentes); A2 B-cubed F 0,995 (8 pares divergentes).
