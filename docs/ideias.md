# Ideias para depois

Ideia nova entra aqui e espera a fase dela. Nada daqui entra no código antes de ir para `docs/plano.md`.

## Pedido do dono em 21/10: a página inicial em torno do mapa (próxima etapa, antes da tela Mercados)

O dono achou a página inicial redundante, com dados soltos, sem ligação com o contexto geopolítico e com apresentação
confusa. Pedido:

- página inicial com o globo 3D interativo em destaque, com rotas marítimas, países e pontos críticos (estreitos);
- notícia crítica acende a região no mapa (ex.: Ormuz, Bab el-Mandeb), sempre com o contexto geopolítico do lugar:
  o que acontece, quem são os atores, seus objetivos e incentivos ("como uma teoria dos jogos"), não só notícias;
- referência citada pelo dono: o OSIRIS (https://osirisai.live, código em https://github.com/simplifaisoul/osiris,
  licença MIT). O link do X de antes não abre no ambiente do Claude.

O que o OSIRIS ensina (análise de 21/10, pelo README e pelas capturas de tela do dono):

- Mesma base técnica do nosso site (Next.js 16 e MapLibre). A licença MIT permite reaproveitar código com o aviso
  de autoria. Diferença: o OSIRIS é um servidor que busca os dados ao vivo; o nosso é estático (o robô grava o
  status.json a cada 15 minutos), o que mantém o custo zero.
- Estrutura de tela que funciona: mapa em tela cheia; barra de ícones à esquerda com as camadas por categoria e a
  contagem de cada uma; painel à direita com abas (alertas, notícias, mercados por grupo, com minigráfico);
  barra de cima com hora e estado; faixa de baixo que passa as últimas informações; 3D/2D e mapa/satélite.
- Camadas gratuitas e sem chave que cabem nas nossas regras: terremotos (USGS), desastres (NASA EONET, GDACS),
  portos e pontos de passagem marítima (lista fixa), eventos com local (GDELT). Aviões (OpenSky) e navios ao vivo (AIS)
  pedem servidor ou chave: só como contexto, se couberem. Câmeras de trânsito e ferramentas de invasão (RECON) ficam
  fora: não servem ao propósito e têm risco de privacidade e de abuso.
- O que fazemos diferente, e é o que dá valor: cada número tem fonte e duas datas; vozes independentes; a régua que
  diz o que está fora do normal; conferência com a fonte oficial; contexto com fonte; IA só resume (regra 7). O
  próprio OSIRIS mostrava o WTI a −4,93% em 21/10, o mesmo falso alarme de troca de contrato que a nossa
  conferência pegou.

- Lente Brasil: Comex Stat, empresas da B3 (dados abertos da CVM), câmbio pelo Banco Central.
- Perguntas sobre o arquivo com citação (fase 5).
- Pistas de rede social: Bluesky (API aberta) e canais públicos do Telegram via RSSHub. X só se houver caminho
  gratuito: desde fevereiro de 2026 a API cobra por post lido (cerca de US$ 0,005), e as ferramentas gratuitas
  (twscrape, RSSHub) exigem o login de uma conta do X. Contas que o dono quer seguir, como pista (regra 4):
  @neilsethinew, @MoloWarMonitor, @Barchart, @GlobalMktObserv, @KobeissiLetter, @insiderwave. Antes, procurar as
  mesmas contas em canal gratuito (site com RSS, newsletter, Telegram, Bluesky) com `jobs/scripts/sondar_fontes.py`.
- Camadas de contexto no globo (voos, navios ao vivo): só como contexto, nunca como fato, e só se forem gratuitas.
- Aplicativo instalável no celular (PWA) como alternativa ao Telegram.

## Dos PDFs do STRATUM antigo (decisão 0006)

Fase 2 (mercados):

- Régua com parâmetros fixos:
  - janela de 5 anos (10 quando houver);
  - mediana e desvio absoluto mediano;
  - ajuste sazonal nas séries mensais;
  - mínimo de 24 pontos ("histórico curto" não gera leitura);
  - validade por frequência;
  - revisão da fonte guardada como registro novo.
- Detector de mudança: nível extremo que persiste (percentil ≥ 95 ou ≤ 5 por dois períodos) ou quebra de ritmo.
  Cada mudança vem com a taxa-base ("quantas vezes algo parecido já aconteceu"). A lista é ordenada só pela pontuação.
- Juros: para a reação a um evento, série diária oficial numa lista curta (Tesouro dos EUA, Bundesbank, Banco da
  Inglaterra, Japão). A média mensal da OCDE serve só de contexto.
- Contexto do país: população e PIB (Banco Mundial), gasto militar (SIPRI, termos a conferir).
- Cada fonte lida no ritmo dela, com o formato conferido na entrada. Arquivo público sem chave antes de API com chave.
- Preço em coluna à parte: variação desde o evento.

Fase 3 (IA):

- Extração por formulário fechado: cada campo traz a frase literal do documento, e um programa confere se ela existe
  e se valor e data batem. Campo sem prova é descartado; código só vale se existir na tabela oficial.
- Cada resultado guarda o modelo e a versão da instrução.

Fase 4 (medição física):

- Atos oficiais como série: sanções e controles de exportação por país e por semana, com quem sanciona e quem é alvo
  (Federal Register, lista consolidada dos EUA, UE; China se houver coleta estável).
- Comércio por código HS: fatia do maior país de origem, mudança em 12 meses e dependência de importação.
  BACI (sem chave, anual) primeiro; o UN Comtrade pede chave.
- Conflito: estado por limiar escrito (ativo, em alta, parado). O ACLED gratuito só dá dado agregado por semana;
  a API do UCDP pede token desde fevereiro de 2026.
- Finanças soberanas: reservas por moeda (FMI, COFER), ouro dos bancos centrais, títulos dos EUA com estrangeiros (TIC).
- Armas: transferências (SIPRI) e vendas militares notificadas (DSCA).
- Focos de calor por satélite (NASA FIRMS, pede chave) como contexto físico, nunca como confirmação sozinho.
- Os mesmos fluxos de EUA, UE e China lado a lado, com a mesma régua.

Fase 5 (grafo e hipóteses):

- Piloto EUA × China em chips e terras raras, com os nós tirados de listas oficiais (minerais críticos do USGS e da UE).
- Ligação sem fonte não existe. Cada ligação tem tipo (fornece, controla, produz, membro de), peso e validade.
- Gargalo é medida: fatia do maior produtor, concentração e dependência de importação, com limite publicado.
- Ficha da hipótese:
  - afirmação verificável;
  - mecanismo (o caminho no grafo);
  - prazo de 6 a 36 meses;
  - sinais a favor e sinais contra (obrigatórios);
  - critério de resultado e probabilidade declarada.

  A hipótese fica travada no registro: mudar cria uma versão nova. No prazo, é julgada sozinha (acertou, errou ou
  indeterminada). O placar é permanente, com as erradas e a pontuação de Brier, separado para o dono e para o sistema.
- Evento que toca o mecanismo marca a hipótese como "revisar" e aparece no resumo. A nota do dono fica ao lado, com
  data, e nunca entra em conta.

Sem fase ainda:

- Resumo da semana dentro do resumo de domingo às 19:00 (eventos de importância alta), sem mensagem extra.
- Busca no arquivo, com índice estático gerado pelo robô.
- Página de bloco (UE, OTAN, Oriente Médio) e seções por região no resumo, a partir de listas oficiais.
- Imprensa especializada (defesa, energia, mineração, transporte marítimo, chips). Think tanks só marcados como
  análise, fora de toda contagem.
- Cabos submarinos, dutos e corredores como camada de contexto (licença a conferir).
- Dinheiro público de defesa dos EUA (contratos diários, USAspending), separando anúncio, teto e valor obrigado.
  É só dos EUA e puxa para investimento.
- Empresas expostas, só depois do placar de hipóteses: universo por regra, exposição medida em documento, sem nota
  e sem ranking.
- Guardar o texto de atos oficiais de domínio público, se a fase 3 precisar da frase de prova (exceção à decisão
  0001; pede decisão própria).
- Estética de atlas (serifa nos títulos, textura discreta), sem significado de cor.
- Amostra semanal de 20 eventos conferida pelo dono, com a taxa de acerto publicada.
- Exportação dos eventos em CSV, respeitando as licenças.
- Ao abrir ao público: bloqueio automático do que o termo de uso de uma fonte não deixa publicar; seguir países ou
  entidades (só faz sentido com mais de um usuário); slogans, sem os que falam de capital.
- Tabela de vieses no Método, cada um com a regra que o evita.
- Poucos conceitos (evento, série, mudança, hipótese): tela que precise de um conceito novo está errada.
- Fase 5: descida em camadas (país → recurso → cadeia → exposição), com a fonte em cada passo; a IA pode redigir o
  "por que importa", mas só a partir de um caminho que já está no grafo. Hipóteses geradas pelo sistema por modelo
  fixo, só depois do placar do dono.
- Candidatos do piloto da fase 5: Ásia dos chips (METI, comércio de Coreia e Taiwan), medidas comerciais da OMC,
  insumo-produto da OCDE, dados gratuitos da IEA sobre minerais e petróleo (licença a conferir).
- Só se dinheiro público e empresas entrarem: avisos de compra pública (SAM.gov) e lei anual de defesa, política
  industrial dos EUA (DOE, CHIPS), mudança de texto nos balanços anuais (10-K), comunicados de empresas por RSS.
- Indicadores da indústria (encomendas, uso da capacidade, emprego, usinas, Eurostat), só se a economia de guerra
  virar tema.
