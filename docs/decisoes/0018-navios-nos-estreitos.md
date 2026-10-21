# 0018. Navios nos estreitos (PortWatch)

Data: 2026-10-21

## Contexto

O dono pediu para ver quantos navios passam por Ormuz e pelos outros pontos críticos, comparado com o normal. O plano
deixava isso para a fase 4; o dono adiantou.

A sonda de 21/10 (`jobs/scripts/sondar_navios.py`, no GitHub Actions) mostrou:
- o PortWatch, do FMI com a Universidade de Oxford, publica navios por dia em 28 estreitos;
- cobre todos os nossos 8 pontos, com dados diários desde 1º de janeiro de 2019;
- é público e sem chave (ArcGIS);
- o último dia era 18/10, 3 dias antes da sonda: a base é atualizada uma vez por semana;
- os termos do FMI permitem reusar os dados citando a fonte e marcando o que foi transformado.

Em Ormuz, de 29/9 a 18/10 de 2026, passaram de 0 a 8 navios por dia. O PortWatch conta navios pelo sinal AIS, que o
navio transmite. Navio com o sinal desligado não entra na conta. O EIA avisa que esses sinais ficaram pouco confiáveis
na região desde o fim de fevereiro de 2026.

## Decisão

1. **Fonte nova**, `portwatch`. É lida uma vez por dia, pedindo de novo o último mês para pegar revisões (regra 2).
   Fica parada (cinza) se o último dia tiver mais de 12 dias (a base sai uma vez por semana, com uns 3 dias de
   atraso; sobra folga para um atraso do FMI).
2. **Duas séries por ponto**: navios por dia (todos os tipos) e petroleiros por dia. Ponto e estreito do PortWatch:
   - Ormuz: Strait of Hormuz;
   - Bab el-Mandeb: Bab el-Mandeb Strait;
   - Suez: Suez Canal;
   - Malaca: Malacca Strait;
   - estreitos turcos: só o Bósforo;
   - estreitos dinamarqueses: só o Øresund (o Grande Belt não é coberto);
   - Panamá: Panama Canal;
   - Cabo da Boa Esperança: Cape of Good Hope.
3. **A mesma régua (`regua-1.2`)**, com uma medida nova para contagens: a média dos últimos 7 dias. O percentil compara
   essa média com as médias de 7 dias dos 5 anos anteriores, com os mesmos parâmetros das outras séries (fora do normal
   até 5 ou a partir de 95). Variação de um dia para o outro não serve para contagem: de 0 para 4 navios não é
   "+400%". Ao lado vai a média dos mesmos 7 dias um ano antes, para comparação simples.
4. **Onde aparece**:
   - no painel de cada ponto crítico;
   - uma marca na lista de pontos;
   - na faixa de baixo, quando sai do normal;
   - na tela Método.
   Não entra no painel de mercados, porque não é mercado, nem na reação a cada evento.
5. **Fonte citada como o FMI pede**: "FMI, PortWatch", com link. A média de 7 dias é marcada como conta do Stratum.

## Consequências

- O site mostra a data do último dia medido; o dado chega com alguns dias de atraso.
- O site diz ao lado do número que é contagem pelo sinal AIS. Navio com o sinal desligado não aparece. Perto de Ormuz,
  a queda mede navios com o sinal ligado, não necessariamente todo o tráfego.
- Um nível baixo que dura meses entra aos poucos no histórico de 5 anos e deixa de ser "fora do normal". A comparação
  com um ano antes continua mostrando a diferença.
- São cerca de 46 mil linhas de histórico (8 pontos, 2 séries, desde 2019) e mais 16 por dia, uns 4 MB no banco.
