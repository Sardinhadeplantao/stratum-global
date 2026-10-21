# Plano

O caminho do usuário: **aconteceu → é verdade? → importa? → quem é afetado? → o que vem por aí?**
Cada fase entrega algo usável e termina num "pronto quando" verificável.

Regra de ouro: não prever o futuro, e sim mapear as forças que podem produzi-lo. O Stratum Global não prevê guerra,
eleição ou preço, não recomenda compra ou venda e não apresenta opinião como dado (decisão 0006).

## Fase 0. Fundação ✅

- [x] Robô no GitHub Actions a cada 15 minutos, com testes antes de cada rodada
- [x] Banco com migrações automáticas; banco temporário quando o Supabase não está configurado
- [x] Primeiras fontes (oficiais e imprensa de vários blocos), sem duplicatas, com registro de cada coleta
- [x] Site com o globo (países do Natural Earth, cinza = sem medição), painel do país e tela Método
- [x] Resumo no Telegram às 7:30, 12:00 e 19:00 de Brasília (decisão 0005)
- [x] Agendador pelo Supabase: o robô roda a cada 15 minutos, sem depender do horário do GitHub (decisão 0004)
- [x] Supabase, Telegram e GitHub Pages ligados pelo dono (passo a passo em `docs/configurar.md`)

**Pronto quando:** o site está no ar, a tela Método diz "Banco: Permanente" e a mensagem de teste chega no Telegram.

## Fase 1. Monitor (4 a 6 semanas)

Já entregue:

- nome Stratum Global e página inicial no formato do esboço (globo, últimas atualizações, indicadores, cartões);
- regra de citação de países: dicionário com nomes, gentílicos, capitais e siglas; versão atual em
  `docs/decisoes/0003-regra-paises-0.2.md`;
- gabarito de eventos: 520 manchetes de dois dias agrupadas em eventos pelo Claude, em duas anotações independentes
  e reconciliadas, em `jobs/tests/gabarito/`;
- cópia semanal do banco, com a restauração testada e a data da última cópia na tela Método (decisão 0007);
- ficha de cada fonte (nível e quem controla, com a fonte da informação), na tela Método (decisão 0008);
- fontes oficiais de 3 blocos, além da ONU: EUA (sanções e controles de exportação), Europa (Relações Exteriores do
  Reino Unido, Conselho e Comissão da UE) e Rússia (Relações Exteriores). China, Índia, Japão, Brasil e OTAN não têm
  feed que o robô consiga ler (sonda de 20/10, `jobs/scripts/sondar_fontes.py`);
- histórias: notícias da mesma história juntas por regra (`historias-0.2`), com quantas vozes independentes (donos
  diferentes) cobrem cada uma, na página Histórias, no painel de cada país do globo e no resumo do Telegram
  (decisão 0009);
- títulos em português por tradução automática gratuita, marcada como tal, com o original sempre à vista (decisão 0010);
- página inicial em torno das histórias do dia: a coluna ao lado do globo mostra as histórias com mais vozes; as
  notícias uma a uma ficam num cartão embaixo;
- Método com a regra de ouro, o que o sistema não faz, a versão de cada regra em vigor, a fila da tradução e um
  glossário curto.

Também entregue: a retenção (decisão 0015, arquivo conferido). Banco medido em 21/10: 45,6 MB de 500 MB.
Mercados a cada 15 minutos, com a página que se atualiza sozinha, nomes no padrão do mercado e só o fechamento do dia
no banco (decisão 0016).

Falta:

- Completar a ficha das fontes: termos de uso e volume esperado por dia. Fonte nova entra com a ficha, uma amostra
  real guardada e um teste. Fonte que se cala além do esperado entra no resumo.
- Lista de fontes: a China oficial, se aparecer um feed que funcione; GDELT para volume. A imprensa das regiões que
  faltam (África, América hispânica, Japão e Coreia, Turquia, Irã, Israel): a retenção já está decidida (decisão
  0015, arquivo conferido), então podem entrar.
- Um dia novo anotado para medir a regra `historias-0.2` num dia que ela nunca viu (meta: pelo menos 90% dos pares
  juntados são da mesma história).
- Opcional: o dono confere 30 pares do gabarito (`jobs/tests/gabarito/conferencia_dono.md`). Sem isso, o Método diz
  que o gabarito foi feito só pelo Claude.

Depois das histórias (o selo por fato, decisão 0009):

- Juntar por fato, não só por história. A regra de entidades não separa fatos vizinhos da mesma história (72% a 79%
  de acerto num dia novo, `jobs/estudos/eventos/LEIAME.md`). Caminhos: mais dias anotados e uma regra nova, ou uma IA
  gratuita que leia os pares, o que pede mudar a regra 7 por escrito.
- Com isso, o grau de confirmação de cada fato:
  - pista: só rede social (regra 4);
  - relatado: uma fonte de imprensa, ou várias do mesmo controlador;
  - corroborado: veículos de controladores diferentes; texto que credita a mesma agência (AFP, Reuters, AP) conta
    como uma fonte só;
  - oficial: documento do próprio órgão (governo ou organismo multilateral) sobre o próprio ato;
  - contestado: a regra do que conta como contradição é escrita nos casos de referência.

  Mudança de grau vira registro novo e aparece no resumo. Proposta já escrita em `jobs/estudos/eventos/grau/`.
- Fato × declaração ("Trump diz X", confirmado, quer dizer que ele disse); importância por fórmula publicada; tipo
  de evento; reações; todo número leva aos documentos; cobertura por bloco no Método.

**Pronto quando:**

- você acompanha o mundo por uma semana só pelo Stratum Global;
- num dia novo anotado, pelo menos 90% dos pares que a regra de histórias junta são da mesma história;
- a rodada inteira (testes, coleta e montagem do site) termina em até 10 minutos no log do GitHub, abaixo do limite
  de 14 do workflow.

A meta por fato da decisão 0006 (90% de precisão e 60% de cobertura por evento) passa para a etapa do selo por fato.

## Fase 2. Mercados (3 a 4 semanas)

Já entregue:

- a régua única (`regua-1.0`) e o detector de mudança, com os parâmetros fixados antes do primeiro dado
  (decisão 0011): percentil da variação contra os 5 anos anteriores, fora do normal até 5 ou a partir de 95, mínimo
  de 250 cotações, extremo que persiste por 2 dias, quebra de ritmo e taxa-base;
- moedas do G20 contra o euro (BCE, 13, oficial) e contra o dólar (Yahoo Finance, 12, e o DXY), lidas no ritmo de cada
  fonte, com revisão gravada como registro novo e o dia em andamento marcado. O FRED saiu (uma semana de atraso) e o
  Yahoo, que é de mercado e não oficial, é conferido com a conta pelo BCE (decisão 0012). A leitura de cada uma aparece
  na tela Método;
- conferência no fim de cada rodada: o log do GitHub mostra fontes com falha, notícias e a leitura de cada série
  (`jobs/scripts/conferir_status.py`);
- juros de 10 anos de fonte oficial (Tesouro dos EUA, Bundesbank, Banco da Inglaterra, Ministério das Finanças do
  Japão), em pontos percentuais; bolsas de 18 membros do G20 e da zona do euro, 11 commodities e 2 cripto pelo Yahoo
  (decisão 0013). São 61 séries na mesma régua, separadas por grupo na tela Método;
- a página inicial em torno do mapa (decisão 0014): pontos críticos que acendem por regra (`pontos-0.1`), contexto de
  cada ponto com fonte, rotas esquemáticas, terremotos do USGS, o painel de cada país com os mercados dele, a aba
  Mercados (destaques, quantas sobem e caem, último mês, bolsas por região) ao lado das notícias, e a troca de contrato
  das commodities fora da régua (`regua-1.1`);
- a reação do mercado a cada evento (`reacao-0.1`, decisão 0017): em cada história e em cada ponto crítico em pauta, os
  ativos ligados (dos pontos e dos países citados), o dia do evento e o pregão seguinte pela régua, a variação desde
  o evento e a taxa-base de pelo menos um deles sair do normal por acaso.

Falta:

- Juros do Brasil: não há série oficial diária e gratuita do título de 10 anos num arquivo simples.
- Atores e incentivos de cada ponto crítico, com decisão própria (é análise, não dado).

**Pronto quando:** todo evento importante mostra se algum ativo ligado se mexeu fora do normal.

## Fase 3. IA como redatora (2 a 3 semanas)

- Tarefa agendada do Claude: briefing da manhã com citação de cada fonte; zelador semanal que propõe consertos.
- API gratuita (Groq, com Gemini de reserva) para títulos e resumos dos eventos importantes.
- Conjunto de ~100 documentos anotados para medir se a IA melhora sem inventar fonte.
  Troca de modelo só passa se a precisão não cair. Cada campo que a IA extrair traz a frase do documento, conferida
  por programa no título e no trecho guardados, ou no documento baixado na hora, sem guardá-lo.

**Pronto quando:** o briefing é melhor que o extrativo no conjunto anotado e toda citação confere.

## Fase 4. Medição física (4 a 6 semanas)

Já entregue, adiantado a pedido do dono: navios nos estreitos (PortWatch do FMI, decisão 0018), navios e petroleiros
por dia em cada ponto crítico, pela média de 7 dias na régua, com a comparação com um ano antes.

Falta: comércio (BACI, UN Comtrade), sanções e conflito (UCDP, ACLED) como séries,
calendário geopolítico, picos de cobertura, comparação entre imprensas de blocos diferentes.
Os atos oficiais, que já são eventos na fase 1, viram série. Conflito tem estado por limiar escrito, sem "potencial".

**Pronto quando:** eventos aparecem ligados a fluxos físicos, além do mercado.

## Fase 5. Grafo, hipóteses e arquivo (4 a 6 semanas)

Ligações país–commodity–ativo com fonte e peso, simulação de choque, hipóteses com placar,
perguntas sobre o arquivo com citação, rever o passado como o sistema o via.
Começa por um piloto, EUA × China em chips e terras raras. As hipóteses têm sinais contra obrigatórios e um placar
que mostra as erradas; nada de carteira (decisão 0006).

**Pronto quando:** o teste retroativo não usa dado do futuro e o placar mostra as hipóteses erradas.

## Para quando abrir ao público

Login, aviso legal ("não é recomendação de investimento"), licenças de dados (mercado não oficial, ACLED e
OpenSanctions são só para uso não comercial), briefing por API própria em vez do plano pessoal do Claude.
Abrir só depois de 30 dias de coleta com toda falha no resumo e de uma pessoa de fora usar o site sem explicação.
Até lá, o site pede aos buscadores que não o indexem (já faz isso).
