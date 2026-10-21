# 0011. A régua única das séries e as primeiras moedas

Data: 2026-10-20

Atualização de 21/10: as moedas contra o dólar passaram do FRED para o Yahoo Finance, conferidas com o BCE
(decisão 0012). A régua não mudou.

## Contexto

A fase 2 traz os mercados. A regra 6 pede uma régua só para todas as séries: dizer "fora do normal" comparando cada
série com o próprio passado, com os mesmos parâmetros para todas. Se os parâmetros fossem escolhidos depois de ver os
dados, seria fácil ajustá-los até "achar" o que se queria. Por isso eles ficam fixados aqui, antes do primeiro dado
(proposta em `docs/ideias.md`, decisão 0006).

## Decisão: a régua (`regua-1.0`, em `jobs/stratum/domain/regua.py`)

1. **O que se mede em cada série** (a medida), conforme o tipo:
   - preço (moeda, bolsa, commodity, cripto): a variação em % desde a observação anterior;
   - taxa (juros): a diferença em pontos percentuais desde a observação anterior;
   - série mensal: a variação em 12 meses (contra o mesmo mês do ano anterior), que tira a sazonalidade sem modelo.

   Hoje só existe o primeiro tipo, em séries diárias. Fim de semana e feriado não contam: a variação é de um dia de
   cotação para o seguinte.
2. **Histórico de referência**: as medidas dos **5 anos** anteriores ao ponto, sem o próprio ponto e sem nada depois
   dele. A mesma janela para todas as séries, para que "fora do normal" queira dizer a mesma coisa em todas. Dez anos
   misturariam épocas muito diferentes (antes e depois de 2020) e deixariam séries novas incomparáveis.
3. **Percentil**: a posição da medida dentro do histórico, de 0 a 100 (empates contam metade). Percentil 97 quer dizer
   que 97% das medidas dos 5 anos anteriores foram menores.
4. **Fora do normal**: percentil até 5 (queda) ou a partir de 95 (alta).
5. **Faixa normal** mostrada: a medida no percentil 5 e no 95 do histórico.
6. **Pontuação**, só para ordenar: a distância até a mediana do histórico, medida em desvios absolutos medianos (DAM,
   vezes 1,4826, que equivale a um desvio-padrão numa curva normal). O percentil para em 100; a pontuação diz qual de
   duas altas fora do normal foi maior. A lista é ordenada só pela pontuação, nunca pelo preço ou pelo nome.
7. **Mínimo**: 250 medidas no histórico em série diária (um ano de cotações) e 24 em série mensal. Abaixo disso,
   "histórico curto", sem leitura.
8. **Validade**: cada fonte diz em quantos dias o dado fica velho (o ritmo dela mais o atraso de publicação, escrito em
   `fontes.py` e na tela Método). Passou disso, a série fica "parada" e cinza.
9. **Revisão**: quando a fonte muda um valor já publicado, o valor novo entra como registro novo, com a data em que o
   sistema soube; o antigo fica. A leitura de qualquer momento usa só o que o sistema sabia naquele momento.

## Decisão: o detector de mudança

- **Extremo que persiste**: dois períodos seguidos fora do normal, do mesmo lado (duas altas ou duas quedas).
- **Quebra de ritmo**: a agitação (o DAM das últimas 20 medidas) no percentil 95 ou mais da agitação dos 5 anos
  anteriores, com a mesma régua.
- **Taxa-base**: cada mudança vem com quantas vezes a mesma mudança começou nos 5 anos anteriores (com a régua aplicada
  a cada dia, só com o passado daquele dia). Se a série tem menos de 5 anos de leituras, diz em quantos anos contou.
- O detector descreve; não prevê e não manda aviso. Preço é contexto (regra 8).

Mudar qualquer parâmetro desta página pede uma decisão nova e uma versão nova da régua. Cada leitura leva a versão.

## Decisão: as primeiras séries

Moedas, de duas fontes oficiais gratuitas e sem chave (arquivo público antes de API com chave):

- **BCE** (taxas de referência do euro, publicadas a cada dia útil): as moedas do G20 que o BCE cota. São 13: dólar,
  iene, libra, yuan, real, rupia indiana, rupia indonésia, won, peso mexicano, lira turca, rand, dólar australiano e
  dólar canadense. Ficam de fora Argentina e Arábia Saudita (o BCE não cota) e Rússia (o BCE parou em março de 2022).
- **FRED** (Banco Central de St. Louis, que republica a tabela H.10 do Fed): as mesmas moedas do G20 que o Fed cota
  contra o dólar (10: real, yuan, iene, libra, rupia indiana, won, peso mexicano, dólar canadense, dólar australiano e
  rand) e o índice amplo do dólar. O euro contra o dólar já vem do BCE e não se repete.

Cada série aparece como a fonte publica, sem conta: "Euro em reais" (R$ por €), "Dólar em reais" (R$ por US$).
Subiu quer dizer que a primeira moeda ficou mais cara. O robô baixa desde 2015 (5 anos de janela e mais 5 para a
taxa-base) e depois lê o último mês a cada vez, para pegar revisões: o BCE a cada 3 horas, o FRED a cada 12 (a H.10 sai
uma vez por semana). Validade: 5 dias para o BCE (cobre a Páscoa) e 12 para o FRED.

## Consequências

- As leituras aparecem na tela Método, com os parâmetros. A tela Mercados e a ligação com os eventos vêm depois.
- Tabelas novas `serie` (a lista, copiada do código a cada rodada, como as fontes) e `observacao` (só inserção).
  São dados públicos e entram na cópia semanal. Cerca de 70 mil linhas no começo, uns 6 mil por ano depois.
- O BCE e o Fed não publicam no fim de semana: no sábado e no domingo, a última leitura é a de sexta.
- A H.10 sai às segundas, com a semana anterior: a leitura do FRED chega com até uma semana de atraso. Para a reação a
  um evento no mesmo dia, vale a do BCE.
