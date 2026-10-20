# Grau de confirmação, ficha das fontes e modelo dos objetos (fase 1)

Data: 20/10/2026 (segunda passada; a primeira, de 19/10, foi conferida e corrigida). Proposta; nada foi alterado no
repositório.

O que a segunda passada conferiu e mudou:

- os 20 casos de referência rodam e passam; a regra dá o mesmo resultado nas 3 ordens de chegada;
- **o rascunho da decisão passou a ser 0008**: a 0007 já existe no repositório (cópia semanal do banco);
- as tabelas novas entram sozinhas na cópia semanal (ela copia tudo o que está em `db.md`), e nenhuma tem dado
  pessoal, como a decisão 0007 exige;
- a relação entre o `tipo` de hoje da fonte e o `nivel` novo ficou escrita (seção 1.1);
- entrou o tamanho de cada feed numa leitura real (seção 1.3), a divisão por tipo de evento no dev e o tempo
  medido (seção 6);
- a busca na web foi refeita: a leitura direta das páginas continua bloqueada (o endereço nem resolve), e a busca
  não achou os termos de uso dos feeds de BBC, DW, France 24 e Folha. Continuam pendentes.

Arquivos desta pasta:

- `fichas.py`: a ficha das 11 fontes e das 3 agências, pronta para ir para o `fontes.py`;
- `regra_grau.py`: a regra `grau-0.1`, uma função pura;
- `online.py`: esqueleto do caminho manchete → evento → grau, só com inserções;
- `test_casos.py`: 20 casos de referência, todos passando;
- `aplicar_dev.py`: aplica a regra aos eventos do gabarito dev e grava o resultado em `graus_dev.json`.

## Em poucas linhas

- **Pista**: o evento só tem rede social (nível 5).
- **Relatado**: há pelo menos um documento de nível 1 a 4, mas não há duas vozes independentes.
- **Corroborado**: há pelo menos 2 vozes independentes e pelo menos 2 donos diferentes entre os veículos que
  publicaram.
  - A voz de um documento é o dono da fonte (ficha). Se o texto credita AFP, Reuters ou AP, a voz é a agência.
  - Texto quase igual a outro já presente no evento não acrescenta voz.
- **Oficial**: algum documento é ato do próprio órgão.
  - Federal Register da BIS e da OFAC: todo documento conta.
  - ONU News: só quando o título diz que um órgão da ONU decidiu ou fez algo. Fala não conta.
- **Contestado**: adiar para a versão 0.2. Os motivos estão na seção 2.5.
- **Mudança de grau** vira uma linha nova em `evento_grau`. A linha antiga fica. A mudança aparece no resumo seguinte.
- **No gabarito dev**, a regra dá:
  - 177 eventos: 155 relatados, 22 corroborados, 0 oficiais, 0 pistas;
  - dos relatados, 144 têm uma manchete só e 11 têm várias manchetes do mesmo dono (TASS ou France 24);
  - 57 eventos só têm a TASS.

## 1. Ficha das fontes

### 1.1 O que cada campo quer dizer

**Nível** segue a escala de O 63-65: 1 governo, 2 organismo multilateral, 3 empresa, 4 imprensa, 5 rede social.

**Tipo de controle**:

- **privado**: um grupo privado é o dono.
- **público**: o Estado paga, e a independência editorial está escrita em lei ou carta (BBC, DW, France 24).
- **estatal**: o governo ou o partido controla, sem essa garantia (TASS, CGTN). Também entra aqui quem o Estado
  financia e dirige: a Al Jazeera, pela lei do Catar de 2011.

**Controlador (a chave)** decide se duas fontes são independentes. A mesma chave quer dizer uma voz só.

- Para veículo público ou estatal, a chave é o Estado: `estado:FRA`. É de propósito.
  - France 24 e uma futura RFI, do mesmo Estado, nunca se corroboram.
  - BBC e um futuro Channel 4 também não.
  - Isso é conservador. Na dúvida, não contar duas vezes, como na regra "na dúvida, não juntar" do gabarito.
- Para grupo privado, a chave é o grupo: `grupo:folha`.
- Para organismo, a chave é a sigla: `org:ONU`.

**Nível e o `tipo` de hoje.** A tabela `fonte` já tem `tipo` (oficial, imprensa, dados, social), e o `export.py`
usa `tipo == "social"` para deixar rede social fora das contas. O `tipo` fica, porque é o que a tela mostra, mas
passa a sair do nível: 1 e 2 = oficial, 3 e 4 = imprensa (ou dados, para fonte de série), 5 = social. Um teste
confere que os dois nunca discordam. A regra do grau olha só o nível.

**Atos próprios** diz se um documento da fonte pode ser ato do próprio órgão:

- `todos`: cada documento é ato do órgão (diário oficial filtrado por órgão);
- `por_titulo`: depende do título (veja a seção 2.3);
- `nenhum`.

### 1.2 As 11 fontes

| Fonte | Nível | Tipo de controle | Controlador (chave) | Quem é | Onde está escrito |
|---|---|---|---|---|---|
| onu_noticias | 2 | multilateral | `org:ONU` | ONU, Departamento de Comunicação Global | unic.un.org/aroundworld/unics/en/whoWeAre/aboutDPI/index.asp ✔ |
| fr_bis | 1 | estatal | `estado:USA` | Governo federal dos EUA: BIS (Comércio). Publicado pelo Office of the Federal Register (NARA) | federalregister.gov/agencies/industry-and-security-bureau ✱ |
| fr_ofac | 1 | estatal | `estado:USA` | Governo federal dos EUA: OFAC (Tesouro). Mesmo diário oficial | federalregister.gov/agencies/foreign-assets-control-office ✱ |
| bbc_mundo | 4 | público | `estado:GBR` | BBC: corporação pública por Carta Real, paga pela taxa de licença | wikipedia.com/wiki/Bbc ✔ · bbc.com/aboutthebbc/governance/charter ✱ |
| dw_mundo | 4 | público | `estado:DEU` | Deutsche Welle: emissora internacional da Alemanha, criada pela Lei da DW (1997), paga pelo orçamento federal | baj.media/wp-content/uploads/2024/08/dw_gesetz_en-2.pdf ✔ · mtrlegal.com/en/wiki/deutsche-welle ✔ |
| france24 | 4 | público | `estado:FRA` | France Médias Monde, 100% do Estado francês (via APE) | en.wikipedia.org/wiki/France_24 ✔ · statemediamonitor.com/?p=1854 ✔ |
| aljazeera | 4 | estatal | `estado:QAT` | Al Jazeera Media Network: "fundação privada de utilidade pública" pela lei de 2011, financiada pelo governo do Catar | en.wikipedia.org/wiki/Al_Jazeera_Media_Network ✔ · statemediamonitor.com/2024/07/al-jazeera-media-network-ajmn/ ✔ |
| tass | 4 | estatal | `estado:RUS` | TASS: empresa unitária federal do Estado russo, agência central do governo | en.wikipedia.org/wiki/TASS ✔ |
| cgtn_mundo | 4 | estatal | `estado:CHN` | CGTN: do China Media Group, sob o Departamento Central de Propaganda do PCCh e o Conselho de Estado | en.wikipedia.org/wiki/CGTN_(TV_channel) ✔ · safeguarddefenders.com/en/blog/ownership-and-control-chinese-media ✔ |
| the_hindu | 4 | privado | `grupo:the_hindu` | THG Publishing (The Hindu Group): 52% da Kasturi & Sons, família Kasturi | india.mom-rsf.org/en/owners/companies/detail/company/company/show/the-hindu-group/ ✔ |
| folha_mundo | 4 | privado | `grupo:folha` | Empresa Folha da Manhã S.A. (Grupo Folha): 100% da família Frias de Oliveira | poder360.com.br/brasil/post-engana-ao-dizer-que-lula-e-acionista-da-folha-de-s-paulo/ ✔ · aosfatos.org/noticias/lula-nao-e-o-dono-do-jornal-folha-de-spaulo/ ✔ |

Agências. Não são lidas pelo robô, mas o documento que as credita conta como elas:

| Agência | Controlador (chave) | Quem é | Onde está escrito |
|---|---|---|---|
| AFP | `agencia:afp` | Agence France-Presse: ente autônomo pela lei de 10/01/1957. A lei proíbe que fique sob controle de grupo político ou econômico | culture.gouv.fr/thematiques/presse-ecrite/l-agence-france-presse ✔ |
| Reuters | `grupo:thomson_reuters` | Thomson Reuters, com maioria da Woodbridge, a holding da família Thomson | fullfact.org/online/associated-press-reuters-rothschilds/ ✔ |
| AP | `grupo:ap` | Associated Press: cooperativa sem fins lucrativos dos associados (EUA) | idem ✔ |

Legenda das fontes:

- ✔ apareceu nos resultados da busca na web nesta sessão.
- ✱ endereço oficial que conheço, mas que não deu para abrir. A busca funcionou; a leitura direta das páginas (WebFetch e curl)
  foi bloqueada pelo proxy para bbc.com, dw.com, thehindu.com, tass.com e os feeds. Esses endereços ficam "a conferir".
- Wikipedia e State Media Monitor são fontes secundárias. Para o controle, as primárias são:
  - a lei da DW;
  - o Ministério da Cultura francês, para a AFP;
  - a Carta Real da BBC;
  - para a Folha, a declaração do próprio jornal, citada pelo Poder360.

Os cadastros oficiais da TASS (registro de empresa unitária federal) e da CGTN não apareceram na busca.

Duas escolhas que o dono pode querer rever:

1. **AFP separada do Estado francês.** A AFP tem estatuto próprio e não pertence ao Estado (lei de 1957), embora
   o Estado seja seu maior cliente e historiadores apontem influência. Se o dono preferir o lado conservador,
   basta trocar a chave da AFP para `estado:FRA`. No dev, isso não muda nenhum grau.
2. **Al Jazeera como estatal.** A rede diz que não é controlada pelo Catar. O que está documentado é o
   financiamento e a nomeação da diretoria pelo governo. A chave `estado:QAT` vale do mesmo jeito se ela for
   classificada como "pública"; só muda o rótulo da tela.

### 1.3 Termos de uso e volume

| Fonte | Termos de uso | Volume por dia | Manchetes no gabarito de 19/10 (piso) |
|---|---|---|---|
| onu_noticias | un.org/en/about-us/terms-of-use (a confirmar para o feed) | pendente | 1 |
| fr_bis, fr_ofac | domínio público (obra do governo dos EUA, 17 U.S.C. § 105) | pendente; poucos atos por semana | 0 |
| bbc_mundo | pendente. Os termos antigos (2005 a 2008) pediam link de volta e proibiam cobrar | pendente | 18 |
| dw_mundo | pendente | pendente | 5 |
| france24 | pendente | pendente | 21 |
| aljazeera | aljazeera.com/terms-and-conditions/ (gerais, sem cláusula para RSS) | pendente | 25 |
| tass | pendente. A TASS processa quem copia fotos dela, o que não diz nada sobre título com link | pendente | 86 |
| cgtn_mundo | pendente | pendente | 9 |
| the_hindu | pendente | pendente | 60 |
| folha_mundo | pendente | pendente | 11 |

Tamanho de cada feed numa leitura real (rodada do GitHub de 16/10, a primeira com o banco vazio): ONU News 30,
BIS 8, OFAC 33, BBC 36, DW 11, France 24 24, Al Jazeera 25, TASS 100, CGTN 50, The Hindu 60, Folha 100. Isso é
quantos itens o feed mostra de uma vez, não quantos saem por dia. TASS e Folha mostram 100, o teto do feed: se
publicarem mais de 100 entre duas leituras, o excedente se perde. Com leitura a cada 15 minutos, isso não deve
acontecer, mas é a primeira coisa a conferir na contagem de 7 dias.

O volume certo sai de 7 dias de contagem no banco permanente: documentos por fonte por dia, pelo `conhecido_em`.
Os números de 19/10 são um piso, porque o robô rodava de horas em horas (decisão 0004). Guardamos só título, link e
trecho (decisão 0001), o uso mais aceito para feed público. Os termos precisam estar conferidos antes de abrir ao público.

## 2. A regra do grau (`grau-0.1`)

Entram os documentos do evento (fonte, título, resumo, conhecido_em, id) e as fichas. Sai o grau, com a explicação:
as vozes, quem publicou e quais documentos são oficiais. A explicação fica gravada e aparece na página do evento
("a regra que o deu"). O código está em `regra_grau.py`.

### 2.1 A voz de cada documento

1. Se o título ou o resumo credita uma agência, a voz é a agência. Vale a que aparece primeiro.
   - AFP: `AFP`, `Agence France-Presse`, `France-Presse`, `France Presse`.
   - Reuters: `Reuters` (pega "(Reuters)").
   - AP: `Associated Press` ou `(AP)`.
   - "AP" sozinho não conta: no The Hindu, costuma ser Andhra Pradesh.
2. Senão, a voz é o controlador da fonte.
3. Quem publicou é sempre o controlador da fonte, mesmo quando a voz é a agência.

### 2.2 Quase-duplicatas

Os documentos do evento são lidos na ordem de chegada (`conhecido_em`, depois `id`). Um documento quase igual a
outro que já está no evento entra no mesmo "grupo de texto". Cada grupo conta uma vez, com a voz e o dono do seu
primeiro documento.

- Os grupos nunca se fundem depois. Por isso, um documento novo nunca reduz o número de vozes: dentro da mesma
  versão da regra, o grau só sobe.
- Enquanto a regra de quase-duplicatas (MinHash, no plano) não existir, vale um substituto simples: duas manchetes
  são quase iguais quando metade das sequências de 3 palavras de título mais resumo é igual.
- No dev, o par mais parecido entre fontes diferentes chega a só 0,12 nessa medida. Ou seja, o substituto não
  muda nada no gabarito.

### 2.3 Oficial

Um documento é **ato próprio** quando a fonte é de nível 1 ou 2 e uma destas condições vale:

- a ficha diz `todos`, como no Federal Register filtrado pela BIS ou pela OFAC: cada documento é uma regra, um aviso
  ou uma sanção do próprio órgão;
- a ficha diz `por_titulo` (ONU News) e o título começa com um órgão da ONU seguido de um verbo de ato.
  - Órgãos: Conselho de Segurança, Assembleia Geral, Secretário-Geral, PMA (WFP), UNICEF, OMS, ACNUR, UNRWA,
    AIEA, CIJ e os outros do organograma do sistema ONU.
  - Verbos de ato: adopts, approves, extends, appoints, launches, suspends, cuts, rules, imposes...
  - Verbos de fala não contam (says, warns, urges, condemns). Assim, "UN chief condemns attack" e
    "Airstrike kills dozens, UN says" continuam relatado.

O evento é **oficial** quando tem pelo menos um ato próprio. Oficial é o grau mais alto. A página mostra também
quantas vozes o evento tem ("oficial; também em 3 veículos de 3 donos").

### 2.4 Pista, relatado e corroborado

O cálculo segue esta ordem:

1. Se há ato próprio, o grau é **oficial**.
2. Senão, se há pelo menos 2 vozes diferentes e pelo menos 2 donos diferentes entre os veículos que publicaram,
   o grau é **corroborado**.
   - A segunda condição impede que duas manchetes da TASS, uma delas citando a AFP, corroborem sozinhas.
   - Também impede que DW e France 24 corroborem quando as duas creditam a AFP: aí há 2 donos, mas uma voz só.
3. Senão, se há algum documento de nível 1 a 4, o grau é **relatado**.
4. Senão, o grau é **pista**: só rede social. Ela nunca conta como voz (regra 4).

Também é relatado quem é de nível 1 ou 2 e não fala de ato próprio: a ONU News noticiando um bombardeio é uma voz
(`org:ONU`), como um jornal. Empresa (nível 3) ainda não existe na lista. Quando entrar, conta como uma voz e nunca
como oficial: o plano define oficial como governo ou organismo multilateral.

### 2.5 Contestado: adiar para a 0.2

Recomendo que a 0.1 nunca devolva "contestado" e que a tela Método diga "contestado ainda não é medido". São três
motivos, todos conferidos no dev:

1. **No gabarito, a negação é outro evento.** "Kremlin rejeita acusação de envolvimento russo" (A1.E13) e "Senador
   nega acusações" (A40.E1) são eventos próprios. Isso segue a diretriz de que uma declaração é um evento. A acusação
   e a negação nunca estão no mesmo evento, então uma regra que olha só para dentro do evento não enxerga a contestação.
2. **Uma regra por verbo erra no caso mais comum.** "Rubio says no pause in intel sharing" (A8.E3) tem 3 donos
   diferentes confirmando que Rubio negou. Marcar como contestado seria dizer que há dúvida sobre a fala, o que é
   falso. No dev, as 2 manchetes com verbo de negação são exatamente esse tipo de caso.
3. **Números diferentes não são contradição.** O mesmo evento (A1.E1) traz 1.800, "mais de 2.000" e 2.400 presos,
   porque a contagem evoluiu. Uma regra por número marcaria os maiores eventos como contestados.

Regra candidata para a 0.2. Ela só entra depois que o gabarito tiver o rótulo fato × declaração e uma ligação
"contesta" entre eventos, anotados antes da regra, como manda o plano:

> O evento E fica **contestado** quando existe, na janela de 2 dias, um evento N que (a) foi ligado a E pela regra
> de agrupamento no nível "assunto"; (b) tem um documento de nível 1 ou 2 cujo controlador é o ator acusado em E
> (pelo código Wikidata, que vem com o GLiNER); e (c) cujo título tem verbo de negação (denies, rejects, refutes,
> nega, desmente). Vale também quando as fontes do próprio E se contradizem num fato binário (aconteceu ou não), mas
> isso só com casos anotados.

Mesmo assim, E continua com o grau que tinha. "Contestado" é uma marca a mais, com o link para N. Assim, o grau
nunca desce por causa de uma negação.

### 2.6 Quando o evento ganha documento novo

- A cada documento novo, o grau do evento é recalculado. Se o grau muda (ou se é o primeiro), entra uma linha nova
  em `evento_grau`.
- A linha nova traz:
  - o grau;
  - as vozes;
  - o documento que provocou a mudança;
  - o `conhecido_em` desse documento;
  - o `calculado_em`;
  - a versão da regra.
- A linha antiga nunca muda (regra 2). Documento que não muda o grau não gera linha.
- Dentro de uma versão, o grau só sobe (pista → relatado → corroborado → oficial), porque grupos de texto não se
  fundem e vozes não somem.
- Uma versão nova da regra (`grau-0.2`) recalcula todos os eventos, com linhas marcadas pela versão nova. A primeira
  linha de uma versão nova não é "mudança" no resumo; o Método diz quando a regra mudou.
- **No resumo**, entra o bloco "Mudaram de grau desde o último resumo".
  - Mostra no máximo 5 eventos, com o título, `relatado → corroborado`, as vozes e o link.
  - A seleção é pelas linhas de `evento_grau` com `calculado_em` depois do último resumo enviado que tenham uma linha
    anterior na mesma versão.
  - A ordem é: mais vozes primeiro, depois a mudança mais recente. Preço nunca entra (regra 8).

## 3. Modelo dos objetos (o que a decisão curta antes das tabelas precisa dizer)

### 3.1 Tabelas novas

Todas são só de inserção. Uma migração nova, `0003_eventos.py`, cria as tabelas, e o `downgrade` levanta
`NotImplementedError`, como nas outras migrações. Datas em UTC, sem fuso. JSON vai como `Text` (`json.dumps`)
para valer igual no PostgreSQL e no SQLite.

**`fonte_ficha`**: a ficha de cada fonte, com histórico.

- Colunas: `id`, `fonte_id`, `nivel`, `controlador_tipo`, `controlador`, `controlador_nome`, `controlador_fonte`,
  `atos_proprios`, `termos_uso`, `volume_dia`, `hash`, `conhecido_em`.
- De onde vem: do `fontes.py`, que é a lista única.
- O que a muda: o robô insere uma linha só quando o `hash` da ficha muda (por exemplo, quando um veículo troca de dono).
- Por que uma tabela à parte: a tabela `fonte` de hoje é sobrescrita a cada rodada (`gravar_fontes`). A ficha
  decide grau, então precisa de histórico. A troca de dono de um veículo não pode mudar sem rastro o grau de
  eventos antigos.

**`evento`**: um acontecimento.

- Colunas: `id`, `regra` (versão do agrupamento), `primeiro_documento_id`, `ocorreu_em`, `conhecido_em`, `calculado_em`.
- De onde vem cada data:
  - `ocorreu_em` é o `quando()` do documento que abriu o evento, ou seja, a data da fonte;
  - `conhecido_em` é o `conhecido_em` desse mesmo documento;
  - `calculado_em` é quando a regra rodou. É igual ao `conhecido_em` na rodada normal e diferente na carga do
    histórico (A23).
- O que a muda: nada. Título, países, número de fontes e última atualização saem dos documentos ligados, na exportação.

**`documento_evento`**: liga cada documento a um evento.

- Colunas: `id`, `documento_id`, `evento_id`, `regra`, `calculado_em`, `similaridade` (a nota que decidiu, para
  auditoria; nula para quem abriu o evento).
- Unicidade em (`documento_id`, `regra`): cada documento fica num evento só por versão do agrupamento, e rodar de novo
  não duplica nada.
- As duas datas do fato vêm do próprio documento; `calculado_em` é a do registro.

**`evento_grau`**: o histórico de grau.

- Colunas: `id`, `evento_id`, `grau`, `regra` (`grau-0.1`), `fichas` (hash das fichas usadas), `vozes` (JSON),
  `publicadores` (JSON), `oficiais` (JSON com ids), `documento_id` (quem provocou), `conhecido_em` (desse documento),
  `calculado_em`.
- Unicidade em (`evento_id`, `regra`, `documento_id`).
- O grau atual de um evento é a última linha dele na versão em vigor.

**`documento_pais`**: os países citados por documento.

- Colunas: `documento_id`, `iso`, `regra` (`paises-0.2`), `calculado_em`.
- Cumpre o que a decisão 0003 prometeu ("quando virarem dado, serão gravadas por documento com a versão da regra").
- Os países do evento são a união dos países dos seus documentos.

**`resumo`**: uma coluna nova, `regras`. É um JSON com as versões das regras usadas no texto enviado (A18). A coluna é
acrescentada vazia; as linhas antigas ficam como estão.

**Cópia semanal (decisão 0007).** O `copia.py` copia todas as tabelas de `db.md`, então as novas entram sozinhas,
na ordem certa (pais antes dos filhos). Nenhuma delas tem dado pessoal ou de conexão: são manchetes públicas,
fichas de fontes públicas e contas da regra. A restauração testada de toda semana passa a cobri-las sem código novo.

O `inserir_ignorando_repetidos` de hoje aceita uma coluna como chave. Para (`documento_id`, `regra`), ele precisa
aceitar uma lista de colunas: a mudança é pequena e não muda o comportamento atual.

### 3.2 O caminho numa rodada

A ordem é: coleta → **eventos** → agendador → resumo → status.json. O módulo novo `stratum/eventos.py` usa as
regras puras de `domain/agrupamento.py` e `domain/grau.py`. O esqueleto testável é o `online.py` desta pasta.

1. **Novos** são os documentos sem linha em `documento_evento` na versão em vigor do agrupamento. Eles são
   processados um a um, na ordem (`conhecido_em`, `id`). Se a rodada cair no meio, os que faltaram entram na próxima.
2. **Janela de 2 dias.** São candidatos os eventos da versão em vigor que têm algum documento com `quando()` a no
   máximo 48 horas do `quando()` do documento novo.
   - Do banco, carrega-se só o que cai nessa faixa, com a mesma consulta de `export.documentos_desde` e o filtro
     final em Python. Isso dá umas centenas a poucos milhares de manchetes.
   - Uma manchete atrasada, de uma fonte que voltou depois de dias, é comparada com os eventos da época do fato,
     não com os de hoje.
   - Evento fora da janela não recebe mais nada.
3. A manchete entra no primeiro candidato que a regra de agrupamento aceitar, ou abre um evento. Nunca muda de evento
   depois, e eventos nunca se fundem (regra 2).
4. O grau do evento que recebeu a manchete é recalculado. Linha nova só se o grau mudou.
5. Se o hash das fichas mudou, os eventos da janela são recalculados, e as linhas novas levam o hash novo.
6. **Versão nova do agrupamento.** Todos os documentos guardados passam de novo pelo caminho, na ordem de chegada,
   gerando eventos e ligações com a versão nova e o `calculado_em` do dia (A23). As linhas antigas continuam no banco.
   A exportação usa só a versão em vigor.

### 3.3 Exportação (status.json)

O site continua sem calcular nada (regra 9). Tudo sai pronto.

- `eventos_24h`: os eventos com algum documento das últimas 24 horas.
  - Cada um traz: id, título (do primeiro documento), grau, número de vozes, de documentos e de fontes, países,
    `ocorreu_em`, `conhecido_em`, última atualização e as versões das regras.
  - A ordem é a atualização mais recente. A ordem por importância vem na segunda volta, nunca por preço (regra 8).
- `contagens.graus`: quantos eventos de cada grau nas 24 horas.
- **Um arquivo por evento** (`dados/eventos/<id>.json`), lido por uma página só.
  - Traz: os documentos (título, link, fonte, país e dono da fonte, as duas datas), o histórico de grau e a
    explicação ("2 vozes: estado:QAT, grupo:the_hindu").
  - Só os eventos dos últimos 30 dias são escritos, para a rodada não crescer sem fim. O prazo depende da decisão
    de retenção.
- **Países**: cada país ganha a contagem de eventos e a lista dos últimos eventos. A cor do globo continua pelas
  citações (`paises-0.2`) até a tela nova decidir.
- **Método**:
  - as versões em vigor (`paises-0.2`, `eventos-x`, `grau-0.1`);
  - a tabela de fichas;
  - o que não se mede:
    - contestado;
    - fato × declaração;
    - agência reescrita sem crédito;
    - veículo que publica texto de agência sem dizer (comum no The Hindu e na Al Jazeera).

### 3.4 Resumo do Telegram

O resumo continua só às 7:30, 12:00 e 19:00 (decisão 0005).

- **Primeira linha**: "Desde 19/10 7:30: 120 notícias, 85 eventos novos (1 oficial, 12 corroborados, 72 relatados)".
  Pista fica fora das contagens (regra 4).
- **Destaques**: para cada um dos 3 países mais citados, o maior evento do país no período. "Maior" quer dizer, nesta
  ordem: mais vozes, mais documentos, mais recente. É a troca que a decisão 0005 já previa.
- **Mudaram de grau**: o bloco descrito na seção 2.6.
- **Problemas e agendador**: como hoje.
- A coluna `resumo.regras` guarda as versões das regras usadas.

### 3.5 SQLite das branches e PostgreSQL da main

- O código e a migração são os mesmos, só com SQLAlchemy Core e sem função própria do PostgreSQL: sem JSONB,
  sem ARRAY, com as datas comparadas em Python.
- Na branch, o banco temporário começa vazio. Os eventos só juntam as manchetes da própria rodada, o grau só muda
  dentro dela e nenhum resumo sai (regra 13).
- Na main, o PostgreSQL guarda tudo. Os eventos e as linhas de grau são poucos bytes por documento, muito menos
  que o próprio documento. A decisão de retenção mede isso.
- Uma rodada por vez (decisão 0004). As chaves únicas tornam a repetição inofensiva.

## 4. Casos de referência (antes do código)

Todos estão em `test_casos.py` e passam. O `doc(...)` lá é a entrada (fonte, título, resumo); a saída esperada
está no `assert`. Ao levar para `jobs/tests/test_referencia.py`, ficam como estão.

| # | Entrada | Saída esperada |
|---|---|---|
| G1 | 2 manchetes da TASS sobre a varredura em Dobropolye (dev 108, 114) | relatado; vozes `estado:RUS` |
| G2 | DW "…officials told AFP." + France 24 "…(AFP)." | relatado; voz `agencia:afp`; 2 donos publicando |
| G3 | Federal Register da OFAC "Notice of OFAC Sanctions Actions", sozinho | oficial |
| G4 | ONU News "Airstrike on market kills dozens in Sudan's El Fasher, UN says" | relatado; voz `org:ONU` |
| G5 | ONU News "Security Council extends UNIFIL mandate…" e "WFP cuts aid to 500,000…" | oficial |
| G6 | ONU News "UN chief condemns attack…" e "Security Council members warn…" | relatado (fala não é ato) |
| G7 | Al Jazeera + DW sobre a deputada australiana atropelada (dev 5, 54) | corroborado; `estado:DEU`, `estado:QAT` |
| G8 | TASS "…cited by AFP…" + TASS sem crédito (dev 148, 167) | relatado: 2 vozes, mas 1 dono publicando |
| G9 | BBC + TASS "…cited by AFP" | corroborado |
| G10 | The Hindu e Al Jazeera com o mesmo texto de agência sem crédito | relatado; 1 grupo de texto; vale a voz da primeira |
| G11 | Só rede social; depois rede social + TASS | pista; depois relatado com voz só `estado:RUS` |
| G12 | "AP Chief Minister…" / "told The Associated Press" / "(Reuters) -" / "Agence France-Presse" | nenhum / ap / reuters / afp |
| G13 | As 3 manchetes "Rubio says no pause…" (dev 11, 115, 190) | corroborado, nunca contestado na 0.1 |
| G14 | France 24 + outro veículo do Estado francês | relatado (mesma chave `estado:FRA`) |
| O1 | TASS abre o evento; BBC chega 1 hora depois | linhas `relatado` e depois `corroborado`; a primeira continua igual; a mudança aponta o documento da BBC e aparece no resumo |
| O2 | Duas manchetes da TASS no mesmo evento | 2 ligações, 1 linha de grau |
| O3 | Manchete do mesmo assunto 49 horas depois | abre evento novo; o antigo não muda |
| O4 | A mesma rodada processada duas vezes | nada duplicado |
| O5 | A manchete 3 combina com os eventos 1 e 2 | entra só no 1; os eventos não se fundem; a 2 não se move |
| O6 | Manchete que chega 3 dias atrasada, com data do fato 1 hora depois do evento | entra no evento antigo (janela pela data do fato); a mudança de grau leva a data em que o sistema soube |

Faltam três casos para quando houver código de banco e de resumo:

- **Rede social fora das contagens do resumo**: o evento pista não entra em "eventos novos". Estende o caso 8 do relatório.
- **Carga do histórico**: o evento montado de documentos antigos tem `conhecido_em` do documento e `calculado_em` da
  carga (caso 10 do relatório).
- **Versão nova da regra de grau**: cria linhas novas, sem apagar nem mudar as antigas, e não aparece como
  "mudança" no resumo.

## 5. Rascunho da decisão 0008

A tarefa pedia "0007", mas esse número já foi usado pela cópia semanal do banco. O rascunho fica como 0008.

```markdown
# 0008. Eventos, grau de confirmação e ficha das fontes

Data: 2026-10-XX

## Contexto

A fase 1 troca notícias soltas por eventos (o mesmo acontecimento contado por várias manchetes), cada um com grau de
confirmação. O plano lista os graus, mas não dizia o que conta como "duas fontes", nem onde guardar o grau sem
reescrever nada (regra 2). As 11 fontes de hoje são de donos diferentes, mas quatro são de Estados (TASS, CGTN,
Al Jazeera e, como emissoras públicas, BBC, DW e France 24), e várias publicam texto de agência.

## Decisão

- **Ficha da fonte** em `fontes.py`: nível (1 governo, 2 multilateral, 3 empresa, 4 imprensa, 5 rede social),
  tipo de controle (privado, público, estatal), controlador com a fonte pública que o documenta, atos próprios,
  termos de uso e volume esperado. Veículos do mesmo Estado têm o mesmo controlador. A ficha tem histórico próprio
  (`fonte_ficha`).
- **Grau `grau-0.1`**, por regra pura (`domain/grau.py`):
  - oficial: documento do próprio órgão sobre o próprio ato (Federal Register filtrado pelo órgão; na ONU News,
    título com órgão da ONU e verbo de ato; fala não é ato);
  - corroborado: 2 vozes independentes e 2 donos diferentes publicando; texto que credita AFP, Reuters ou AP conta
    como a agência; texto quase igual conta uma vez;
  - relatado: o resto com imprensa ou fonte oficial; pista: só rede social.
  - Contestado fica para a 0.2: no gabarito, a negação é outro evento, e regra por verbo ou por número erra.
    O Método diz que não é medido.
- **Tabelas novas, só de inserção** (migração 0003): `evento`, `documento_evento`, `evento_grau`, `fonte_ficha`,
  `documento_pais` e a coluna `resumo.regras`. Cada linha tem as duas datas e a versão da regra que a produziu.
  Sem dado pessoal: entram na cópia semanal (decisão 0007) sem decisão à parte.
- **Agrupamento online** com janela de 2 dias pela data do fato: a manchete entra num evento ou abre outro; nunca
  muda de evento, e eventos não se fundem. Versão nova de regra reprocessa tudo com linhas novas.
- **Mudança de grau** vira linha nova e entra no resumo seguinte ("mudaram de grau"). O status.json traz os eventos
  das últimas 24 horas e a contagem por grau prontas, e um arquivo por evento.

## Consequências

- No gabarito dev (19/10), a regra dá 155 eventos relatados, 22 corroborados e nenhum oficial. 57 eventos só têm a
  TASS. Isso é honesto: corroborado aparece com mais fontes, não com regra mais frouxa.
- Não detectamos agência reescrita sem crédito, nem veículo que publica texto de agência sem dizer. O Método diz isso.
- "Corroborado" quer dizer que fontes independentes contam a mesma coisa, não que a coisa é verdade. Duas fontes que
  repetem a Guarda Revolucionária confirmam que ela disse (fato × declaração, ainda sem regra).
- A tabela `fonte` continua sendo cópia do código; o histórico do que decide grau fica em `fonte_ficha`.
```

## 6. A regra aplicada aos eventos do gabarito dev

Para o teste, os grupos do gabarito fazem o papel do agrupamento, e as fichas acima dão os donos. Comando:
`venv/bin/python eventos/grau/aplicar_dev.py`, que roda em menos de 0,1 segundo. O conjunto de teste não foi aberto.

| Grau | Eventos | Com 1 manchete | Com 2 ou mais |
|---|---|---|---|
| pista | 0 | 0 | 0 |
| relatado | 155 | 144 | 11 |
| corroborado | 22 | 0 | 22 |
| oficial | 0 | 0 | 0 |
| **total** | **177** | 144 | 33 |

O que os números mostram:

- **Por tipo de evento (rótulo do gabarito)**: dos 155 relatados, 117 são fatos, 37 são análises e 1 é resenha de
  imprensa. Os 22 corroborados são todos fatos. Ou seja, entre os 139 fatos, 22 (16%) saem corroborados.
  Análise com um veículo só é "relatado" por definição; quando a regra fato × análise existir, a página pode mostrar
  "análise" no lugar do grau. Na 0.1, o grau vale para todos, e o Método diz isso.
- **Tempo**: recalcular o grau a cada manchete que chega, com 2.832 manchetes (12 cópias do dev, mais que 2 dias com
  o dobro das fontes), leva 0,17 segundo. Não pesa nos 14 minutos da rodada. Nenhuma biblioteca nova: só `re` e
  `unicodedata`, da biblioteca padrão do Python.
- **Sensibilidade**: trocar a chave da AFP para `estado:FRA` não muda o grau de nenhum evento do dev.
- **O resultado é o mesmo nas 3 ordens de chegada** (crescente, decrescente e embaralhada com `Random(1)`). A ordem
  só pesaria nas quase-duplicatas, e não há nenhuma no dev.
- **Dos 33 eventos com 2 ou mais manchetes, 22 ficam corroborados.** Os outros 11 são de um dono só: 10 da TASS
  (por exemplo, Lavrov no Irã, o boletim do Grupo Norte e as indicações de Mishustin) e 1 da France 24 (a limpeza
  das cidades, com 2 manchetes).
- **57 eventos só têm a TASS**, um terço do total, como a decisão 0006 já previa.
- **Crédito de agência**: 2 manchetes creditam a AFP (TASS 148 e The Hindu 192). As duas estão em eventos que já
  seriam corroborados sem o crédito, então nenhum grau muda por causa dele no dev.
- **Nenhum evento oficial.** O dev não tem documento do Federal Register, e a única manchete da ONU News (biodiversidade na Armênia)
  não é ato de órgão da ONU pelo título.
- **Corroborados com mais vozes**:
  - os distúrbios na França: 7 manchetes, 6 vozes;
  - o incêndio na base canadense: 7 manchetes, 5 vozes;
  - o corte do PMA em Gaza: 4 manchetes, 4 vozes.

  A lista completa está em `graus_dev.json`.
- **Exemplo do limite "corroborado não é verdade".** O petroleiro em Ormuz (A9.E1) sai corroborado pela TASS e pelo
  The Hindu, mas as duas citam a mesma origem, a Guarda Revolucionária. O que está confirmado é o que a Guarda disse.
  É o caso que o rótulo fato × declaração vai resolver.

## 7. Pendências

1. Conferir os endereços marcados ✱ e achar fonte primária para TASS e CGTN (cadastro oficial). Daqui, a leitura
   direta das páginas foi bloqueada.
2. Termos de uso de 8 fontes e volume por dia de todas. A busca de 20/10 não achou os termos dos feeds de BBC, DW,
   France 24 e Folha (só textos antigos ou de terceiros); é preciso abrir o rodapé de cada site num navegador. O volume sai de 7 dias de banco permanente.
3. O dono decide duas classificações: AFP separada do Estado francês, e Al Jazeera como estatal ou pública.
   Nenhuma das duas muda graus no dev.
4. A regra da ONU News por título foi feita só com a lista oficial de órgãos e com verbos gerais. O dev tem uma
   manchete da ONU News. Antes de ligar, ela precisa ser conferida com uma semana de títulos reais da ONU News
   (amostra guardada, como pede o plano para fonte nova). Se errar, a ficha volta a `nenhum` e a ONU News conta
   só como voz.
5. Contestado e fato × declaração: anotar no gabarito primeiro (a ligação "contesta" entre eventos e o rótulo de
   declaração), depois a regra 0.2.
6. Quase-duplicatas: trocar o substituto pela regra MinHash quando ela existir, com o limiar medido.
7. O `inserir_ignorando_repetidos` precisa aceitar chave de várias colunas.
8. Retenção: decide quantos dias de arquivo por evento o site publica e se as linhas de versões antigas das
   regras ficam para sempre (regra 2 manda que fiquem).
