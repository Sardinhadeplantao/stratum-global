# Ideias para depois

Ideia nova entra aqui e espera a fase dela. Nada daqui entra no código antes de ir para `docs/plano.md`.

- Lente Brasil: Comex Stat, empresas da B3 (dados abertos da CVM), câmbio pelo Banco Central.
- Perguntas sobre o arquivo com citação (fase 5).
- Pistas de rede social: Bluesky (API aberta) e canais públicos do Telegram via RSSHub. X só se a API ficar acessível.
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
- Guardar o texto de atos oficiais de domínio público, se a fase 3 precisar da frase de prova.
- Estética de atlas (serifa nos títulos, textura discreta), sem significado de cor.
- Amostra semanal de 20 eventos conferida pelo dono, com a taxa de acerto publicada.
- Exportação dos eventos em CSV, respeitando as licenças.
- Ao abrir ao público: bloqueio automático do que o termo de uso de uma fonte não deixa publicar.
