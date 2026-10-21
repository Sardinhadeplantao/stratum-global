# 0013. Juros, bolsas, commodities e cripto

Data: 2026-10-21

## Contexto

A fase 2 pede as séries por lista, cada uma com critério, todas na mesma régua (decisão 0011). Antes de escolher, a
sonda de 21/10 (`jobs/scripts/sondar_series.py`) testou 34 candidatas com dados reais: se respondem, quantos anos de
histórico têm e o formato da resposta.

## Decisão

Cada grupo é uma fonte na lista, com critério e ficha próprios. Todas as séries passam pela mesma régua.

- **Juros de 10 anos**, de fonte oficial, lidos a cada 6 horas; medida: diferença em pontos percentuais (decisão 0011).
  São os títulos de referência que o plano já listava:
  - EUA: Tesouro dos EUA (curva de juros diária, coluna "10 Yr"). Em 20/10: 5,12%;
  - Alemanha: Bundesbank (rendimento dos títulos federais, 10 anos). Em 20/10: 3,45%;
  - Reino Unido: Banco da Inglaterra (título nominal de 10 anos, série IUDMNPY);
  - Japão: Ministério das Finanças (curva de juros diária, coluna "10Y"). Em 19/10: 2,935%.

  O Brasil fica para depois: não há série oficial diária e gratuita do título de 10 anos num arquivo simples.
- **Bolsas**: o índice principal de cada membro do G20 com histórico no Yahoo, mais o da zona do euro (EURO STOXX 50).
  São 18. Ficam de fora a Arábia Saudita (o Yahoo só tem 1 dia de histórico) e a Rússia (sem dados da bolsa de Moscou
  desde as sanções de 2022). O índice da Argentina está em pesos, com inflação alta: a régua compara cada série com o
  próprio passado, então a inflação já faz parte do "normal" dele.
- **Commodities**: os contratos de referência mundial de três famílias que pesam em conflitos e sanções. São 11:
  - energia: petróleo Brent e WTI, gás natural nos EUA (Henry Hub) e na Europa (TTF);
  - metais: ouro, prata, cobre e alumínio;
  - grãos: trigo, milho e soja.
- **Cripto**: as duas maiores por valor de mercado, bitcoin e ether.

Bolsas, commodities e cripto vêm do Yahoo Finance (mercado, não oficial; decisão 0012), lidas a cada hora, com o dia em
andamento marcado. Não há fonte oficial para conferir a cotação delas: aparecem sem conferência.

## O que a sonda mostrou e mudou no código

- O petróleo WTI fechou **negativo** em 20/04/2020 (−37,63 dólares). Foi real, então o robô passa a aceitar valor
  negativo; só número inválido é recusado. A variação em % a partir de um preço negativo ou zero não existe, e esse
  dia fica sem medida.
- Commodities são o contrato futuro mais próximo. Na troca de contrato, o preço pode saltar sem que o mercado tenha
  mudado. A régua ainda não separa isso, e a tela Método avisa.
  - Visto na primeira rodada (21/10): o WTI apareceu "fora do normal: queda de 5,0%" com o Brent parado. A sonda dos
    contratos confirmou a troca: o contrato de novembro (CLX26) foi de 103,66 a 101,09 em 20/10 (−2,5%), e a série do
    Yahoo passou de 103,66 (novembro) para 98,47 (dezembro, CLZ26). Metade da queda era a troca.
  - Correção (próxima etapa): o Yahoo diz o mês do contrato no nome em 9 das 11 commodities ("Crude Oil Dec 26",
    "Gold Dec 26"); Brent e TTF não dizem. O robô vai guardar o contrato de cada dia e tirar da régua o dia da troca.

## Consequências

- 61 séries ativas: 26 moedas, 4 juros, 18 bolsas, 11 commodities e 2 cripto. A tela Método passa a separar por grupo.
- O Yahoo vira um ponto único de falha para bolsas, commodities e cripto. Se ele parar, essas séries ficam paradas
  (cinza), e a falha aparece na tela Método e no resumo.
- Mais linhas no banco: cerca de 270 mil por ano, a maior parte da leitura a cada hora do dia em andamento. Entra na
  decisão de retenção da fase 1, que precisa sair antes da imprensa nova.
- A tabela `serie` ganha a coluna `grupo` (migração 0007).
- Saída do banco (achado da revisão de 21/10): a régua lê o histórico inteiro de cada série a cada rodada. Lido do
  Supabase, seriam uns 6 MB por rodada, cerca de 17 GB por mês, e o plano gratuito dá 5 GB de saída. O robô guarda uma
  cópia local das cotações no cache do GitHub e pede ao banco só as linhas novas; o resultado é idêntico (testado).
  Se o banco for recriado, a cópia é descartada e tudo é lido de novo uma vez.
