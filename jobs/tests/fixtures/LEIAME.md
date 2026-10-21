# Amostras dos testes

Trechos reais do que cada fonte devolveu, copiados do log da sonda (`jobs/scripts/sondar_series.py`, workflow
`sondar.yml`) ou do robô. Servem só para os testes conferirem que o robô lê o formato de verdade; o site nunca usa
estes arquivos.

- `bce_exr.csv`: BCE, taxas de referência do iene e do dólar, sonda de 20/10/2026.
- `fred_dtwexbgs.csv`: FRED, índice amplo do dólar, sonda de 20/10/2026.
- `feed_rss.xml` e `feed_atom.xml`: feeds de exemplo, montados para testar casos difíceis (artigo repetido, âncora,
  link perigoso); não são notícias reais.
