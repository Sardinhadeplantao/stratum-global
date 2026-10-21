# Amostras dos testes

Trechos reais do que cada fonte devolveu, copiados do log da sonda (`jobs/scripts/sondar_series.py`, workflow
`sondar.yml`) ou do robô. Servem só para os testes conferirem que o robô lê o formato de verdade; o site nunca usa
estes arquivos.

- `bce_exr.csv`: BCE, taxas de referência do iene e do dólar, sonda de 20/10/2026.
- `fred_dtwexbgs.csv`: FRED, índice amplo do dólar, sonda de 20/10/2026.
- `yahoo_brl.json`: Yahoo Finance, dólar em reais, sonda de 21/10/2026 às 00:10 UTC (resposta inteira, sem cortes).
- Juros, sonda de 21/10/2026 (linhas reais; os trechos do meio que o log não mostrou ficaram de fora):
  `tesouro_2026.csv` (Tesouro dos EUA), `bundesbank_10a.csv`, `boe_iudmnpy.csv` (Banco da Inglaterra),
  `japao_mes.csv` e `japao_historico.csv` (Ministério das Finanças do Japão; a nota do fim do arquivo do mês perdeu dois
  caracteres japoneses na cópia do log).
- `feed_rss.xml` e `feed_atom.xml`: feeds de exemplo, montados para testar casos difíceis (artigo repetido, âncora,
  link perigoso); não são notícias reais.
