"""Ficha de cada fonte (proposta para fontes.py, fase 1).

Campos novos de cada fonte:
- nivel: 1 governo, 2 organismo multilateral, 3 empresa, 4 imprensa, 5 rede social (escala de O 63-65).
- controlador_tipo: privado | publico | estatal | multilateral.
    publico  = dinheiro do Estado, com independência editorial escrita em lei ou carta (BBC, DW, France 24).
    estatal  = controlado pelo governo ou partido, sem essa garantia (TASS, CGTN), ou financiado e dirigido pelo
               Estado (Al Jazeera, pela lei do Catar de 2011).
- controlador: a chave que decide independência. Duas fontes com a mesma chave são uma voz só.
    Estado (público ou estatal) -> "estado:<ISO>"; grupo privado -> "grupo:<nome>"; organismo -> "org:<sigla>".
    Público e estatal do mesmo país têm a MESMA chave: é conservador (France 24 e uma futura RFI são uma voz;
    BBC e um futuro Channel 4 também).
- controlador_nome e controlador_fonte: quem é e onde está escrito (endereço público).
- atos_proprios: "todos" (cada documento do feed é um ato do próprio órgão), "por_titulo" (só quando o título
  diz que um órgão da própria organização agiu) ou "nenhum".
- termos_uso, volume_dia: preenchidos aos poucos (None = pendente). visto_19out = manchetes da fonte no gabarito
  dev de 19/10, um piso (o robô rodava de horas em horas); o volume_dia sai de 7 dias com o banco permanente.

As agências de notícias não são fontes lidas, mas têm ficha: o documento que credita a agência conta como ela.
"""

FICHAS: dict[str, dict] = {
    "onu_noticias": dict(
        nivel=2, controlador_tipo="multilateral", controlador="org:ONU",
        controlador_nome="Nações Unidas (Departamento de Comunicação Global)",
        controlador_fonte="https://news.un.org/en/about ; https://unic.un.org/aroundworld/unics/en/whoWeAre/aboutDPI/index.asp",
        atos_proprios="por_titulo",
        termos_uso="https://www.un.org/en/about-us/terms-of-use (a confirmar para o feed)", volume_dia=None, visto_19out=1),
    "fr_bis": dict(
        nivel=1, controlador_tipo="estatal", controlador="estado:USA",
        controlador_nome="Governo federal dos EUA (BIS, Departamento de Comércio; publicado pelo Office of the Federal Register/NARA)",
        controlador_fonte="https://www.federalregister.gov/agencies/industry-and-security-bureau",
        atos_proprios="todos",
        termos_uso="domínio público (obra do governo dos EUA, 17 U.S.C. § 105)", volume_dia=None),
    "fr_ofac": dict(
        nivel=1, controlador_tipo="estatal", controlador="estado:USA",
        controlador_nome="Governo federal dos EUA (OFAC, Departamento do Tesouro; publicado pelo Office of the Federal Register/NARA)",
        controlador_fonte="https://www.federalregister.gov/agencies/foreign-assets-control-office",
        atos_proprios="todos",
        termos_uso="domínio público (obra do governo dos EUA, 17 U.S.C. § 105)", volume_dia=None),
    "bbc_mundo": dict(
        nivel=4, controlador_tipo="publico", controlador="estado:GBR",
        controlador_nome="BBC, corporação pública por Carta Real (Reino Unido), financiada pela taxa de licença",
        controlador_fonte="https://www.bbc.com/aboutthebbc/governance/charter",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=18),
    "dw_mundo": dict(
        nivel=4, controlador_tipo="publico", controlador="estado:DEU",
        controlador_nome="Deutsche Welle, emissora pública internacional da Alemanha (Lei da DW, 1997), paga pelo orçamento federal",
        controlador_fonte="https://www.gesetze-im-internet.de/dwg/ ; https://www.dw.com/en/about-dw/profile/s-30688",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=5),
    "france24": dict(
        nivel=4, controlador_tipo="publico", controlador="estado:FRA",
        controlador_nome="France Médias Monde, 100% do Estado francês (via Agence des participations de l'État)",
        controlador_fonte="https://www.francemediasmonde.com/en/ ; https://en.wikipedia.org/wiki/France_M%C3%A9dias_Monde",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=21),
    "aljazeera": dict(
        nivel=4, controlador_tipo="estatal", controlador="estado:QAT",
        controlador_nome="Al Jazeera Media Network, 'fundação privada de utilidade pública' (lei do Catar, 2011), financiada pelo governo do Catar",
        controlador_fonte="https://network.aljazeera.net/en/about-us ; https://en.wikipedia.org/wiki/Al_Jazeera_Media_Network",
        atos_proprios="nenhum", termos_uso="https://www.aljazeera.com/terms-and-conditions/ (sem cláusula própria para RSS)",
        volume_dia=None, visto_19out=25),
    "tass": dict(
        nivel=4, controlador_tipo="estatal", controlador="estado:RUS",
        controlador_nome="TASS, empresa unitária federal do Estado russo, agência central do governo",
        controlador_fonte="https://tass.com/today ; https://en.wikipedia.org/wiki/TASS",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=86),
    "cgtn_mundo": dict(
        nivel=4, controlador_tipo="estatal", controlador="estado:CHN",
        controlador_nome="CGTN, do China Media Group, sob o Departamento Central de Propaganda do Partido Comunista e o Conselho de Estado",
        controlador_fonte="https://en.wikipedia.org/wiki/CGTN_(TV_channel) ; https://www.safeguarddefenders.com/en/blog/ownership-and-control-chinese-media",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=9),
    "the_hindu": dict(
        nivel=4, controlador_tipo="privado", controlador="grupo:the_hindu",
        controlador_nome="THG Publishing Pvt Ltd (The Hindu Group), 52% da Kasturi & Sons Ltd, família Kasturi",
        controlador_fonte="https://india.mom-rsf.org/en/owners/companies/detail/company/company/show/the-hindu-group/",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=60),
    "folha_mundo": dict(
        nivel=4, controlador_tipo="privado", controlador="grupo:folha",
        controlador_nome="Empresa Folha da Manhã S.A. (Grupo Folha), 100% da família Frias de Oliveira",
        controlador_fonte="https://www.poder360.com.br/brasil/post-engana-ao-dizer-que-lula-e-acionista-da-folha-de-s-paulo/ ; https://www.aosfatos.org/noticias/lula-nao-e-o-dono-do-jornal-folha-de-spaulo/",
        atos_proprios="nenhum", termos_uso=None, volume_dia=None, visto_19out=11),
}

# Agências: o documento que as credita conta como elas (não como o veículo que publicou).
AGENCIAS: dict[str, dict] = {
    "afp": dict(
        controlador="agencia:afp", controlador_tipo="publico",
        controlador_nome="Agence France-Presse, ente autônomo pela lei de 10/01/1957 (proibido ficar sob controle de grupo político ou econômico)",
        controlador_fonte="https://www.culture.gouv.fr/thematiques/presse-ecrite/l-agence-france-presse"),
    "reuters": dict(
        controlador="grupo:thomson_reuters", controlador_tipo="privado",
        controlador_nome="Reuters, da Thomson Reuters (maioria da Woodbridge, holding da família Thomson)",
        controlador_fonte="https://fullfact.org/online/associated-press-reuters-rothschilds/"),
    "ap": dict(
        controlador="grupo:ap", controlador_tipo="privado",
        controlador_nome="Associated Press, cooperativa sem fins lucrativos dos jornais e emissoras associados (EUA)",
        controlador_fonte="https://fullfact.org/online/associated-press-reuters-rothschilds/"),
}

# Rede social: nenhuma hoje. Quando entrar, nivel=5 e a regra a trata como pista.
