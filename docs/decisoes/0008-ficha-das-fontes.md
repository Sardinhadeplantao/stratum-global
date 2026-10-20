# 0008. Ficha das fontes

Data: 2026-10-20

## Contexto

O grau "corroborado" (fase 1) exige vozes independentes (decisão 0006). Para saber se duas notícias são vozes
independentes, o sistema precisa saber quem controla cada fonte. A lista de fontes não dizia isso.

## Decisão

Cada fonte em `fontes.py` ganha uma ficha, gravada no banco e mostrada na tela Método:

- **nível**: 1 governo, 2 organismo multilateral, 3 empresa, 4 imprensa, 5 rede social;
- **controle**: privado; público (dinheiro do Estado, com independência editorial escrita em lei ou carta, como BBC,
  DW e France 24); estatal (dirigido pelo governo ou partido, sem essa garantia, como TASS e CGTN; a Al Jazeera
  entra aqui por ser financiada e dirigida pelo Estado do Catar); multilateral;
- **controlador**: a chave que decide a independência. Duas fontes com o mesmo controlador são uma voz só.
  Público e estatal do mesmo país têm o mesmo controlador (`estado:<país>`), o que é conservador: France 24 e uma
  futura RFI contariam como uma voz;
- **quem controla e onde está escrito**: nome e endereço público da informação. Fonte sem isso não entra.

## Consequências

- A regra do grau de confirmação pode ser escrita sobre a ficha, sem lista à mão em outro lugar.
- Algumas fichas citam a Wikipédia ao lado da fonte primária; trocar por fonte primária quando houver.
- Termos de uso e volume esperado por dia ainda faltam; entram aos poucos, sem travar a fase 1.
