# 0010. Títulos em português

Data: 2026-10-20

## Contexto

Quase todas as fontes publicam em inglês, e o dono lê em português. O site e o resumo mostravam os títulos
originais, o que deixava o sistema com cara de lista crua. O plano já previa tradução gratuita (Argos/Opus-MT).

## Decisão

- **Tradução automática gratuita**, sem API e sem chave (regra 11): Argos, modelo inglês → português do Brasil
  (`argos-en_pb-1.9`), rodando no próprio GitHub Actions por CTranslate2 e SentencePiece. O modelo é baixado uma vez
  e fica no cache do workflow.
- **Só o título**, só de fonte que não é em português, até 800 por rodada (o acervo entra em partes).
- **Gravação**: tabela `traducao`, só de inserção, com o modelo que traduziu. O título original nunca muda (regra 2).
- **A tradução só lê** (regra 7): a regra de países e as histórias usam o título original.
- **Na tela**: o título em português, marcado como "(tradução automática)", com o original ao passar o mouse; o link
  leva à notícia original. Se a tradução falhar, aparece o original e o sistema segue (o sistema funciona sem IA).

## Consequências

- Tradução automática erra: nome próprio, ironia e manchete curta podem sair estranhos. Por isso o original fica a um
  gesto de distância e a marca de tradução fica visível.
- Cada rodada instala o CTranslate2 (uns 40 MB, guardado no cache do pip) e traduz poucas dezenas de títulos.

## Medido na sonda de 20/10 (`jobs/scripts/sondar_traducao.py`)

- O modelo baixa em 1 a 2 segundos e traduz 143 manchetes em 2 a 3 segundos: 800 por rodada cabem com folga.
- Os mesmos parâmetros do Argos (beam 4). Cada parte da manchete (separada por dois-pontos ou travessão) é traduzida
  sozinha: inteira, o modelo largava a última parte, que costuma dizer quem afirma ("...: Iran's Guards").
- A maioria sai legível. Erros vistos: "mine" virou "meu" (era mina), "Russian stocks up" perdeu o sentido. Por isso
  a marca "(tradução automática)" e o original continuam sempre à vista; na página Histórias o original aparece escrito
  embaixo do título (no celular não há "passar o mouse").
