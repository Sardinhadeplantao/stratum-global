# 0014. A página inicial em torno do mapa: pontos críticos, contexto e mercados

Data: 2026-10-21

## Contexto

O dono achou a página inicial redundante, com dados soltos, sem ligação com o contexto geopolítico e com a apresentação
confusa ("Mais citados" repete o globo; "Quem está falando" fala das fontes, não do mundo; o menu lista oito fases
futuras). Ele pediu o mapa em destaque, com rotas marítimas e pontos críticos que acendem quando uma notícia crítica
os toca, sempre com o contexto do lugar, e citou o OSIRIS como referência de estrutura (`docs/ideias.md`).

## Decisão

1. **A página inicial é o mapa.** O globo ocupa a tela, com botão para o mapa plano. À esquerda, as camadas, cada uma
   com a sua contagem. À direita, um painel com abas: Agora (os alertas contados, o que acendeu e as histórias com mais
   vozes), Mercados e Notícias. Embaixo, uma faixa com os pontos críticos, os mercados fora do normal, os terremotos
   fortes e as últimas notícias. Os cartões de contagem saem; "Mais citados" e "Quem está falando" vão para o fim da aba
   Notícias; a saúde do robô fica numa linha da aba Agora e, inteira, na tela Método.
2. **Pontos críticos** (`pontos-0.1`, em `jobs/stratum/domain/pontos.py`):
   - critério da lista: os estreitos e canais da análise de pontos de passagem de petróleo do EIA (agência de energia
     dos EUA): Ormuz, Malaca, Suez e o oleoduto SUMED, Bab el-Mandeb (com o Mar Vermelho), estreitos turcos, estreitos
     dinamarqueses, Panamá e Cabo da Boa Esperança;
   - uma notícia cita o ponto quando o título ou o resumo traz um dos nomes dele (inglês ou português), como palavra
     inteira ("Suezmax" não é Suez);
   - estado, nas últimas 24 horas e sem rede social: **em pauta** com uma notícia ou mais; **crítico** quando, além
     disso, alguma notícia traz palavra de ação (ataque, míssil, mina, apreensão, bloqueio, explosão, incêndio...) e as
     notícias vêm de pelo menos duas vozes independentes (donos diferentes, decisão 0009); sem notícia, **sem pauta**.
     É regra, sem IA (regra 7), e mede atenção das fontes, não gravidade.
3. **Contexto de cada ponto, com fonte**: o que passa por ali (número do EIA, com o período e o link), os países das
   margens, as séries de mercado ligadas (com a oscilação do dia) e as notícias que o citam. Ponto sem número conferido
   diz isso. Atores, objetivos declarados e incentivos ficam para uma decisão própria: é análise, e precisa de regra
   para não virar opinião apresentada como dado.
4. **Rotas marítimas**: traçado esquemático entre os pontos críticos, desenhado à mão e marcado como tal; não é a rota
   de nenhum navio.
5. **Terremotos**: o feed público do Serviço Geológico dos EUA (USGS), magnitude 4,5 ou mais nas últimas 24 horas, sem
   chave. Cada terremoto entra uma vez; revisão da magnitude vira registro novo (regra 2).
6. **Troca de contrato das commodities** (decisão 0013): o robô guarda o contrato de cada dia quando o Yahoo diz o mês
   no nome. No dia em que o contrato muda, a variação não mede o mercado: a série aparece como "troca de contrato", sem
   cor, e esse dia fica fora da régua. Brent e TTF não dizem o mês; neles o aviso geral continua.

7. **Aba Mercados** (o que o OSIRIS faz bem, com a nossa régua):
   - oito quadros de destaque, lista fixa escrita no robô (`mercados.DESTAQUES`): bolsa e juro de 10 anos dos EUA,
     índice do dólar, ouro, Brent, bitcoin, dólar em reais e Ibovespa. Critério: um número por grande mercado, para quem
     lê do Brasil. A lista não muda com o dia; o que se mexeu fora do normal aparece pela régua;
   - quantas séries sobem, caem ou ficam iguais no último dia, no total e por grupo, contadas pelo robô só entre as de
     leitura "ok" (troca de contrato, dado parado e cotação que não confere ficam de fora);
   - o último mês de cada série (30 dias corridos, como o sistema os conhecia), num minigráfico;
   - as bolsas agrupadas por região (Américas; Europa, Oriente Médio e África; Ásia e Pacífico), a do país do índice;
   - sem verde para alta e vermelho para queda: subir não é bom nem ruim. O dourado marca só o fora do normal.
8. **Aba Notícias**: as 100 últimas manchetes, cada uma com quem fala (a ficha da fonte: imprensa estatal, pública ou
   privada, oficial, e o país), filtro por tipo de fonte e busca. Busca e filtro só escondem itens da lista que o robô
   mandou; não contam nem ordenam.

## Consequências

- Tabelas novas `contrato_futuro` e `evento_local` (migração 0008), dados públicos, na cópia semanal.
- O painel de cada país mostra a moeda, os juros e a bolsa dele, quando existem.
- A tela Mercados deixa de ser uma página à parte: vira a aba Mercados do painel da direita.
- O mapa mostra a regra, não a verdade: um ponto "crítico" quer dizer que fontes independentes noticiam ação ali.
  O número de navios que passa de fato (PortWatch do FMI) fica para a fase 4.
