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

Os dois juntam quase sempre certo, mas encontram poucos pares.

`vetores/`: vetores de frase de três modelos multilíngues gratuitos (sentence-transformers), medidos no GitHub
Actions em 20/10. Com precisão de pelo menos 0,93, o melhor encontrou só 14% dos pares (paraphrase-multilingual-mpnet,
só o título). Descartado: pior que `entidades/` e pesado (instala o torch, mais de 1 minuto por rodada).

## Medida única no conjunto de teste (20/10)

A regra de `entidades/` foi congelada (`entidades/CONGELADO.txt`) e medida uma vez no conjunto de teste
(`entidades/teste.json`):

| Ordem de chegada | Precisão dos pares | Cobertura dos pares | Eventos com par (de 30) |
|---|---|---|---|
| crescente | 0,72 | 0,18 | 14 |
| decrescente | 0,73 | 0,19 | 13 |
| embaralhada | 0,79 | 0,16 | 14 |

**Não atinge a meta** (0,90, 0,60 e 15). A regra estava ajustada demais ao dia de desenvolvimento (19/10). A primeira
medida deu ainda pior, porque 139 das 284 manchetes do teste tinham acentos escritos como código (`n\u00e3o`); só os
textos foram corrigidos, sem tocar na regra nem nos rótulos. O conjunto de teste agora está gasto: pode virar
desenvolvimento, e a próxima medida precisa de um dia novo, anotado e guardado.

`grau/proposta.md`: proposta da regra de grau de confirmação (`grau-0.1`), da ficha das 11 fontes (nível e dono),
do modelo das tabelas novas e de 20 casos de referência (`test_casos.py`, rodam com `python -m pytest` dentro de
`grau/`). Ainda não revisada; vira decisão (0008) e código depois de conferida.

## Segunda tentativa (20/10)

- Com os textos do teste corrigidos, os erros da regra de `entidades/` no dia 16/10 são quase todos acontecimentos
  vizinhos da mesma história ("Trump aprova o fuzilamento" × "Trump cancela a transmissão do fuzilamento").
- Subir o limiar não resolve: no dia 16/10 a precisão por evento fica entre 0,67 e 0,82 em qualquer limiar.
- Contra o gabarito de **assunto** (a história maior), os pares que a regra junta estão certos em 94% a 100% das vezes,
  nos dois dias. A regra é confiável para "mesma história", não para "mesmo fato".
- `segunda/`: regra da fala atribuída ("... — Novak", mesma fonte). Descartada: os dois dias do gabarito tratam
  entrevistas de jeitos diferentes (19/10 separa por tema, 16/10 junta tudo), e para confirmar o que importa é cada
  afirmação, não a entrevista inteira.

