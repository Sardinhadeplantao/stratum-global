# 0012. Moedas contra o dólar todo dia, pelo Yahoo Finance, conferidas com o BCE

Data: 2026-10-21

## Contexto

A decisão 0011 trouxe as moedas contra o dólar do FRED (tabela H.10 do Fed). A primeira rodada real confirmou o
problema: em 20/10, o FRED tinha dados só até 16/10. O Fed publica uma vez por semana, então a reação a um fato chega
com até uma semana de atraso. O dono quer a cotação do dia, inclusive a oscilação do dia em andamento.

Não há fonte oficial, gratuita e diária para as moedas do G20 contra o dólar. O BCE é diário, mas cota contra o euro.

## Decisão

- **Yahoo Finance** (arquivo de cotações por moeda, sem chave) passa a dar as moedas do G20 contra o dólar e o índice
  do dólar (DXY). Ficha: nível 3 (empresa), privado. É **fonte de mercado, não oficial**, e o site diz isso.
  - 12 moedas: real, yuan, iene, libra, rupia indiana, rupia indonésia, won, peso mexicano, lira turca, rand, dólar
    australiano e dólar canadense (rupia indonésia e lira turca não existiam no FRED). O euro contra o dólar continua
    vindo do BCE: uma fonte por par.
  - Lido a cada hora. O dia em andamento aparece como **"dia em andamento"**, com a hora da leitura: é a oscilação do
    dia, ainda não fechada. Ele passa pela mesma régua; como o dia está pela metade, a variação tende a ser menor.
  - Valores guardados com 6 algarismos significativos, para que diferenças de arredondamento da fonte não virem
    "revisão".
  - O valor de cada dia é o último preço negociado nele, e não a barra diária do Yahoo, que demora a ser atualizada.
    Medido na sonda de 21/10: em 20/10, a barra fechava o dólar em 5,0370 reais; o último preço era 5,0238; a conta
    pelo BCE dava 5,0236.
  - O Yahoo às vezes devolve o par com o dólar na frente (CAD=X volta como USDCAD=X). Só essas duas formas são aceitas.
  - Termos de uso: o Yahoo permite uso pessoal, não comercial. Ao abrir ao público, a fonte é trocada ou licenciada
    (já previsto no plano).
- **Conferência com o BCE** (é verdade?): para cada moeda do Yahoo com par no BCE, o robô faz a conta pelo BCE no mesmo
  dia (por exemplo, dólar em reais = euro em reais ÷ euro em dólares) e compara com o Yahoo no último dia completo dos
  dois. Até 2% de diferença, confere (os horários são diferentes: o BCE fixa às 16h de Frankfurt). Acima de 2%, a moeda
  aparece como **"não confere"**, sem cor de leitura, até a diferença sumir. O DXY não tem par no BCE e aparece como
  "sem conferência".
- **O FRED sai da lista**: a fonte e as 11 séries ficam inativas, e o que já foi gravado fica guardado (regra 2).

## Consequências

- As moedas contra o dólar chegam no mesmo dia, e a tela Mercados (próxima etapa) pode mostrar a oscilação do dia ao
  lado dos eventos.
- O Yahoo não tem contrato nem garantia: pode mudar de formato ou bloquear o robô. Se isso acontecer, a fonte aparece
  com falha na tela Método e no resumo do Telegram, e as moedas ficam paradas (cinza). Não há número inventado.
- A leitura a cada hora grava até 24 valores por moeda em dia útil (cada mudança é um registro novo): cerca de 80 mil
  linhas por ano, uns 10 MB. Fica para a decisão de retenção.
- O índice amplo do Fed (oficial, semanal) deixa de ser lido. O DXY é o índice do dólar citado no noticiário, mas pesa
  muito o euro.
