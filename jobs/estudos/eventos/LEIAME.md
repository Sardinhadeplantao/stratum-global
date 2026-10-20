# Estudo: notícias em eventos e grau de confirmação (fase 1)

Rascunhos de 20/10/2026, guardados para a próxima etapa da fase 1. Não são código do robô: nada daqui roda em
produção, e os testes do robô não passam por esta pasta. Medidas feitas só no conjunto de desenvolvimento
(`jobs/tests/gabarito/dev_19out`); o conjunto de teste ainda não foi usado.

`avaliar.py` mede um agrupamento contra o gabarito: precisão e cobertura dos pares, e quantos eventos com 2 ou mais
manchetes tiveram ao menos duas juntadas (a meta da fase 1 está em `docs/plano.md`).

| Jeito de agrupar | Precisão dos pares | Cobertura dos pares | Eventos com par (meta: 17 de 33) |
|---|---|---|---|
| `lexico/`: palavras em comum | 0,96 a 0,97 | 0,22 a 0,29 | 10 |
| `entidades/`: países, nomes próprios e números em comum | 0,98 | 0,39 a 0,40 | 14 a 15 |
| meta | 0,90 | 0,60 | metade |

Os dois juntam quase sempre certo, mas encontram poucos pares. O terceiro jeito planejado, vetores de frase de um
modelo multilíngue gratuito, não pôde ser medido nesta máquina (o site dos modelos é bloqueado aqui) e fica para
um teste no GitHub Actions.

`grau/proposta.md`: proposta da regra de grau de confirmação (`grau-0.1`), da ficha das 11 fontes (nível e dono),
do modelo das tabelas novas e de 20 casos de referência (`test_casos.py`, rodam com `python -m pytest` dentro de
`grau/`). Ainda não revisada; vira decisão (0008) e código depois de conferida.
