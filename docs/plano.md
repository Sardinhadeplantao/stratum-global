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
- ficha de cada fonte (nível e quem controla, com a fonte da informação), na tela Método (decisão 0008).

Falta, em duas voltas. A primeira entrega o monitor usável; a segunda refina.

Primeira volta:

- Retenção: medir o tamanho do banco e quanto ele cresce por semana (o manifesto da cópia semanal traz os dois). A decisão 0001 previa apagar o detalhe das
  notícias depois de uns 90 dias, o que a regra 2 proíbe: a decisão nova mantém tudo ou muda a regra 2 por escrito.
- O dono confere uma amostra de 30 pares do gabarito, para o acerto medido não depender só do Claude.
- Completar a ficha das fontes: termos de uso e volume esperado por dia. Fonte nova entra com a ficha, uma amostra
  real guardada e um teste. Fonte que se cala além do esperado entra no resumo.
- Lista de fontes completa: oficiais de pelo menos 3 blocos (diários oficiais, sanções, chancelarias, ONU, UE),
  com os feeds do governo britânico (GOV.UK) de reserva e a China só se a coleta funcionar; GDELT para volume.
  A imprensa das regiões que faltam (África, América hispânica, Japão e Coreia, Turquia, Irã, Israel) entra depois
  da decisão de retenção.
- Antes das tabelas novas, uma decisão curta com o modelo dos objetos da fase 1: campos, de onde vêm e que regra os muda.
- Caminho do documento até o evento:
  - idioma e tradução (Argos/Opus-MT), com o original a um clique;
  - quase-duplicatas (MinHash);
  - nomes com código (GLiNER + Wikidata): órgãos do Estado, como PLA e IDF, contam o país;
  - lugar (GeoNames);
  - agrupamento em eventos.

  Cada registro derivado guarda a versão da regra que o produziu. Os documentos já guardados passam pelo caminho
  novo, com a data em que a regra rodou.
- Grau de confirmação, por regra escrita e com casos de referência antes do código:
  - pista: só rede social (regra 4);
  - relatado: uma fonte de imprensa, ou várias do mesmo controlador;
  - corroborado: veículos de controladores diferentes. Texto quase igual, ou que credita a mesma agência
    (AFP, Reuters, AP), conta como uma fonte só;
  - oficial: documento do próprio órgão (governo ou organismo multilateral) sobre o próprio ato;
  - contestado: a regra do que conta como contradição é escrita nos casos de referência.

  Mudança de grau vira registro novo e aparece no resumo. O Método diz o limite: não detectamos dois veículos que
  reescrevem a mesma agência sem dar o crédito.
- Fato × declaração: "Trump diz X", confirmado, quer dizer que ele disse, não que X é verdade. Primeiro esse rótulo
  entra no gabarito; depois vem a regra.
- Telas (uma tela, uma pergunta; cada coisa num lugar só):
  - lista "Hoje" com os eventos das últimas 24 horas;
  - globo com eventos;
  - página do evento: duas datas, fontes por bloco, grau e a regra que o deu;
  - página do país, com a linha do tempo dos eventos.

  Contagens prontas no status.json (regra 9). Uma página só, que lê um arquivo por evento, para a montagem do site
  não crescer sem fim.
- Resumo do Telegram com eventos no lugar de notícias soltas, só nos 3 horários (decisão 0005). Briefing extrativo.
- Método: a regra de ouro, o que o sistema não faz, a versão de cada regra em vigor e um glossário curto.

Segunda volta:

- Importância (alta, média, baixa) por fórmula publicada no Método: grau, ato oficial novo, países envolvidos e
  novidade. Nunca preço (regra 8), nunca IA (regra 7). Antes, 5 ou 6 casos de referência.
- Acerto do agrupamento publicado no Método, ao lado do "nada juntado", dizendo que o gabarito foi feito pelo Claude
  e quantos pares o dono conferiu.
- Tipo de evento (lista curta, com "outro"), depois de anotado no gabarito.
- Reações: quem mais se manifestou sobre o mesmo assunto.
- Todo número da tela leva aos documentos que o produziram.
- Cobertura por bloco e o funil do dia no Método (notícias → eventos → importância alta).

**Pronto quando:**

- você acompanha o mundo por uma semana só pelo Stratum Global;
- no gabarito de teste (284 manchetes de 16/10, que não é usado para ajustar a regra), contando pares (par = duas
  manchetes do mesmo evento):
  - pelo menos 90% dos pares que o agrupamento junta estão certos;
  - ele encontra pelo menos 60% dos pares certos;
  - em pelo menos metade dos 30 eventos que têm 2 ou mais manchetes, ele junta ao menos duas delas
    (sem isso, acertar só os 5 maiores eventos já bateria a meta);
- a rodada inteira (testes, coleta e montagem do site) termina em até 10 minutos no log do GitHub, abaixo do limite
  de 14 do workflow.

## Fase 2. Mercados (3 a 4 semanas)

- Séries por lista: moedas (BCE, FRED), juros de 10 anos, bolsa por país, commodities (Banco Mundial, EIA), cripto.
- A régua única (percentil contra o próprio histórico) e a reação medida a cada evento.
  Os parâmetros da régua e do detector de mudança são fixados antes do primeiro dado (proposta em `docs/ideias.md`).
- Tela Mercados: o que se mexeu fora do normal e os eventos no mesmo período ("coincidência no tempo, não causa").

**Pronto quando:** todo evento importante mostra se algum ativo ligado se mexeu fora do normal.

## Fase 3. IA como redatora (2 a 3 semanas)

- Tarefa agendada do Claude: briefing da manhã com citação de cada fonte; zelador semanal que propõe consertos.
- API gratuita (Groq, com Gemini de reserva) para títulos e resumos dos eventos importantes.
- Conjunto de ~100 documentos anotados para medir se a IA melhora sem inventar fonte.
  Troca de modelo só passa se a precisão não cair. Cada campo que a IA extrair traz a frase do documento, conferida
  por programa no título e no trecho guardados, ou no documento baixado na hora, sem guardá-lo.

**Pronto quando:** o briefing é melhor que o extrativo no conjunto anotado e toda citação confere.

## Fase 4. Medição física (4 a 6 semanas)

PortWatch (navios nos estreitos), comércio (BACI, UN Comtrade), sanções e conflito (UCDP, ACLED) como séries,
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
