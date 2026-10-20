"""Lista de fontes lidas pelo robô. É a única lista; o banco recebe uma cópia a cada rodada.

Regra de entrada: toda fonte tem `criterio` (por que está aqui). Nada entra por parecer interessante.
Fase 0: lista inicial para provar o caminho. Os endereços são conferidos na primeira rodada
(a tela Método mostra quais funcionaram).

Ficha de cada fonte (decisão 0008):
- nivel: 1 governo, 2 organismo multilateral, 3 empresa, 4 imprensa, 5 rede social;
- controle: privado | publico (dinheiro do Estado, com independência editorial escrita em lei ou carta) |
  estatal (dirigido pelo governo ou partido, sem essa garantia) | multilateral;
- controlador: quem decide a independência. Duas fontes com o mesmo controlador são uma voz só. Público e estatal
  do mesmo país têm o mesmo controlador ("estado:<ISO>"); grupo privado é "grupo:<nome>"; organismo, "org:<sigla>";
- controlador_nome e controlador_fonte: quem é e onde isso está escrito.
"""

_FR = "https://www.federalregister.gov/api/v1/documents.rss?order=newest&conditions%5Bagencies%5D%5B%5D="
_CRITERIO_IMPRENSA = "Veículo com feed público, publicando do próprio país; a lista cobre blocos diferentes para comparar versões."

FONTES: list[dict] = [
    # Oficiais
    dict(id="onu_noticias", nome="ONU News", tipo="oficial", pais=None, idioma="en", conector="rss",
         url="https://news.un.org/feed/subscribe/en/news/all/rss.xml",
         criterio="Serviço oficial de notícias das Nações Unidas (Conselho de Segurança, Assembleia, agências).",
         nivel=2, controle="multilateral", controlador="org:ONU",
         controlador_nome="Nações Unidas (Departamento de Comunicação Global)",
         controlador_fonte="https://news.un.org/en/about ; https://unic.un.org/aroundworld/unics/en/whoWeAre/aboutDPI/index.asp"),
    dict(id="fr_bis", nome="Federal Register: controles de exportação (BIS, EUA)", tipo="oficial", pais="USA", idioma="en",
         conector="rss", url=_FR + "industry-and-security-bureau",
         criterio="Diário oficial dos EUA; atos do órgão que controla exportações (Entity List, chips, tecnologia).",
         nivel=1, controle="estatal", controlador="estado:USA",
         controlador_nome="Governo federal dos EUA (BIS, Departamento de Comércio; publicado pelo Office of the Federal Register/NARA)",
         controlador_fonte="https://www.federalregister.gov/agencies/industry-and-security-bureau"),
    dict(id="fr_ofac", nome="Federal Register: sanções (OFAC, EUA)", tipo="oficial", pais="USA", idioma="en",
         conector="rss", url=_FR + "foreign-assets-control-office",
         criterio="Diário oficial dos EUA; atos do órgão de sanções do Tesouro.",
         nivel=1, controle="estatal", controlador="estado:USA",
         controlador_nome="Governo federal dos EUA (OFAC, Departamento do Tesouro; publicado pelo Office of the Federal Register/NARA)",
         controlador_fonte="https://www.federalregister.gov/agencies/foreign-assets-control-office"),
    # Imprensa, um veículo por bloco
    dict(id="bbc_mundo", nome="BBC News: World", tipo="imprensa", pais="GBR", idioma="en", conector="rss",
         url="https://feeds.bbci.co.uk/news/world/rss.xml", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="publico", controlador="estado:GBR",
         controlador_nome="BBC, corporação pública por Carta Real (Reino Unido), financiada pela taxa de licença",
         controlador_fonte="https://www.bbc.com/aboutthebbc/governance/charter"),
    dict(id="dw_mundo", nome="Deutsche Welle: World", tipo="imprensa", pais="DEU", idioma="en", conector="rss",
         url="https://rss.dw.com/rdf/rss-en-world", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="publico", controlador="estado:DEU",
         controlador_nome="Deutsche Welle, emissora pública internacional da Alemanha (Lei da DW, 1997), paga pelo orçamento federal",
         controlador_fonte="https://www.gesetze-im-internet.de/dwg/ ; https://www.dw.com/en/about-dw/profile/s-30688"),
    dict(id="france24", nome="France 24", tipo="imprensa", pais="FRA", idioma="en", conector="rss",
         url="https://www.france24.com/en/rss", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="publico", controlador="estado:FRA",
         controlador_nome="France Médias Monde, 100% do Estado francês (via Agence des participations de l'État)",
         controlador_fonte="https://www.francemediasmonde.com/en/ ; https://en.wikipedia.org/wiki/France_M%C3%A9dias_Monde"),
    dict(id="aljazeera", nome="Al Jazeera English", tipo="imprensa", pais="QAT", idioma="en", conector="rss",
         url="https://www.aljazeera.com/xml/rss/all.xml", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="estatal", controlador="estado:QAT",
         controlador_nome="Al Jazeera Media Network, 'fundação privada de utilidade pública' (lei do Catar, 2011), financiada pelo governo do Catar",
         controlador_fonte="https://network.aljazeera.net/en/about-us ; https://en.wikipedia.org/wiki/Al_Jazeera_Media_Network"),
    dict(id="tass", nome="TASS", tipo="imprensa", pais="RUS", idioma="en", conector="rss",
         url="https://tass.com/rss/v2.xml", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="estatal", controlador="estado:RUS",
         controlador_nome="TASS, empresa unitária federal do Estado russo, agência central do governo",
         controlador_fonte="https://tass.com/today ; https://en.wikipedia.org/wiki/TASS"),
    dict(id="cgtn_mundo", nome="CGTN: World", tipo="imprensa", pais="CHN", idioma="en", conector="rss",
         url="https://www.cgtn.com/subscribe/rss/section/world.xml", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="estatal", controlador="estado:CHN",
         controlador_nome="CGTN, do China Media Group, sob o Departamento Central de Propaganda do Partido Comunista e o Conselho de Estado",
         controlador_fonte="https://en.wikipedia.org/wiki/CGTN_(TV_channel) ; https://www.safeguarddefenders.com/en/blog/ownership-and-control-chinese-media"),
    dict(id="the_hindu", nome="The Hindu: International", tipo="imprensa", pais="IND", idioma="en", conector="rss",
         url="https://www.thehindu.com/news/international/feeder/default.rss", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="privado", controlador="grupo:the_hindu",
         controlador_nome="THG Publishing Pvt Ltd (The Hindu Group), 52% da Kasturi & Sons Ltd, família Kasturi",
         controlador_fonte="https://india.mom-rsf.org/en/owners/companies/detail/company/company/show/the-hindu-group/"),
    dict(id="folha_mundo", nome="Folha de S.Paulo: Mundo", tipo="imprensa", pais="BRA", idioma="pt", conector="rss",
         url="https://feeds.folha.uol.com.br/mundo/rss091.xml", criterio=_CRITERIO_IMPRENSA,
         nivel=4, controle="privado", controlador="grupo:folha",
         controlador_nome="Empresa Folha da Manhã S.A. (Grupo Folha), 100% da família Frias de Oliveira",
         controlador_fonte="https://www.poder360.com.br/brasil/post-engana-ao-dizer-que-lula-e-acionista-da-folha-de-s-paulo/ ; https://www.aosfatos.org/noticias/lula-nao-e-o-dono-do-jornal-folha-de-spaulo/"),
]


def ativas(fontes: list[dict] = FONTES) -> list[dict]:
    return [f for f in fontes if f.get("ativa", True)]
