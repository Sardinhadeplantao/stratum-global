# 0016. Mercados a cada 15 minutos, página que se atualiza sozinha e nomes no padrão do mercado

Data: 2026-10-21

## Contexto

O dono pediu os mercados "ao vivo", oscilando sem recarregar a página, os nomes no padrão do mercado (USD/CAD, DXY) e
o painel organizado como o do OSIRIS: por categoria, uma linha por ativo, colunas claras.

Ao vivo segundo a segundo, de graça e num site estático, só existe para cripto: bolsas, câmbio e commodities pedem
servidor próprio ou fonte paga com chave, e chave não pode ficar no site (regra 12). O OSIRIS também atualiza de
tempos em tempos ("UPD 00:35Z"). A rodada do robô é de 15 minutos; mais curta, o tráfego do Supabase gratuito
passaria do limite.

As cópias de hora em hora do dia em andamento eram o que mais fazia as cotações crescerem no banco (cerca de 270 mil
linhas por ano), e o valor do dia em andamento é provisório: o que vale é o fechamento.

## Decisão

1. **O Yahoo (câmbio, bolsas, commodities e cripto) é lido em toda rodada**, a cada 15 minutos, em vez de a cada hora.
2. **O dia em andamento não vai para o banco.** Só o dia que já fechou (data anterior ao dia da leitura, em UTC) é
   gravado; revisão do fechamento continua virando registro novo (regra 2). O valor do dia em andamento da rodada vai
   direto para o status.json, com a data do dia e a hora em que o robô leu (as duas datas, regra 1). Se a leitura
   falhar numa rodada, o site mostra o último fechamento, com a data dele.
3. **A página inicial se atualiza sozinha**: a cada minuto pergunta se o robô publicou dados novos e, se sim, troca os
   números sem recarregar e sem mexer no mapa. Mostra a hora da última atualização.
4. **Nomes no padrão do mercado** (`simbolo`, em `fontes.py`): moedas como BASE/COTADA, em que USD/CAD é quantos
   dólares canadenses vale um dólar americano (EUR/USD, GBP/USD, USD/BRL, EUR/BRL, DXY); juros como US10Y, DE10Y,
   UK10Y, JP10Y; cripto como BTC/USD; bolsas e commodities pelo nome curto (S&P 500, Ibovespa, Brent). A descrição em
   português continua ao lado, menor.
5. **O painel de mercados** tem categorias (Todos, Bolsas, Juros, Moedas, Commodities, Cripto), uma linha por ativo
   com colunas Ativo, Último, Dia e 1 mês, e ao clicar abre a leitura da régua daquele ativo. Moedas separadas em
   "contra o dólar (mercado, conferido com o BCE)" e "contra o euro (oficial, BCE)".

## Consequências

- As cotações passam de cerca de 270 mil para cerca de 16 mil linhas novas por ano.
- O Yahoo recebe 4 vezes mais pedidos (44 por rodada). Se começar a recusar, a fonte aparece como falha na tela
  Método e o ritmo volta a ser revisto.
- O que o site mostra do dia em andamento não fica no banco: não dá para rever depois qual era a cotação às 14h de um
  dia passado. O fechamento de cada dia fica.
