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

import re

from stratum.domain.pontos import PONTOS

_FR = "https://www.federalregister.gov/api/v1/documents.rss?order=newest&conditions%5Bagencies%5D%5B%5D="
_CRITERIO_IMPRENSA = "Veículo com feed público, publicando do próprio país; a lista cobre blocos diferentes para comparar versões."
_CRITERIO_CHANCELARIA = ("Chancelaria (ou o órgão equivalente de um bloco) com feed público: posição oficial sobre política "
                         "externa e sanções; a lista cobre blocos diferentes. Testada pela sonda (scripts/sondar_fontes.py).")
_CRITERIO_MOEDAS = ("Moedas do G20, de fonte oficial gratuita e sem chave: o câmbio reage primeiro a choque político "
                    "e mostra quem está sob pressão.")
_CRITERIO_JUROS = ("Juros do título de 10 anos, de fonte oficial: o preço do dinheiro de cada governo reage a guerra, "
                   "sanção e eleição. Os títulos de referência listados no plano da fase 2 (decisão 0013).")
_CRITERIO_YAHOO = " Cotação de mercado do mesmo dia, com o dia em andamento (decisões 0012 e 0013). Uso pessoal, não comercial."
_YAHOO = dict(tipo="dados", pais="USA", idioma="en", url="https://query1.finance.yahoo.com/v8/finance/chart/", conector="yahoo",
              validade_dias=5, dia_em_andamento=True, nivel=3, controle="privado", controlador="grupo:yahoo",  # toda rodada (0016)
              controlador_nome="Yahoo Inc., controlada por fundos da Apollo Global Management desde 2021 (a Verizon ficou com 10%)",
              controlador_fonte="https://en.wikipedia.org/wiki/Yahoo ; https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html")
_GOVUK = "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D="

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
    dict(id="uk_fcdo", nome="GOV.UK: Relações Exteriores (FCDO, Reino Unido)", tipo="oficial", pais="GBR", idioma="en",
         conector="rss", url=_GOVUK + "foreign-commonwealth-development-office", criterio=_CRITERIO_CHANCELARIA,
         nivel=1, controle="estatal", controlador="estado:GBR",
         controlador_nome="Governo do Reino Unido (Foreign, Commonwealth & Development Office)",
         controlador_fonte="https://www.gov.uk/government/organisations/foreign-commonwealth-development-office"),
    dict(id="ue_conselho", nome="Conselho da União Europeia: comunicados", tipo="oficial", pais=None, idioma="en",
         conector="rss", url="https://www.consilium.europa.eu/en/rss/pressreleases.ashx", criterio=_CRITERIO_CHANCELARIA,
         nivel=2, controle="multilateral", controlador="org:UE",
         controlador_nome="Conselho da União Europeia (os governos dos países-membros)",
         controlador_fonte="https://www.consilium.europa.eu/en/council-eu/"),
    dict(id="ue_comissao", nome="Comissão Europeia: sala de imprensa", tipo="oficial", pais=None, idioma="en",
         conector="rss", url="https://ec.europa.eu/commission/presscorner/api/rss?language=en",
         criterio=_CRITERIO_CHANCELARIA + " Inclui medidas de comércio e a chefe da diplomacia da UE.",
         nivel=2, controle="multilateral", controlador="org:UE",
         controlador_nome="Comissão Europeia",
         controlador_fonte="https://commission.europa.eu/about/organisation-european-commission_en"),
    dict(id="ru_mid", nome="Ministério das Relações Exteriores da Rússia", tipo="oficial", pais="RUS", idioma="en",
         conector="rss", url="https://mid.ru/en/rss.php", criterio=_CRITERIO_CHANCELARIA,
         nivel=1, controle="estatal", controlador="estado:RUS",
         controlador_nome="Governo da Federação Russa (Ministério das Relações Exteriores)",
         controlador_fonte="https://mid.ru/en/about/"),
    # Dados (decisão 0011): lidos no ritmo de cada fonte (a_cada_horas); a série fica parada depois de validade_dias
    dict(id="bce_cambio", nome="BCE: taxas de referência do euro", tipo="dados", pais=None, idioma="en", conector="bce",
         url="https://data-api.ecb.europa.eu/service/data/EXR/", a_cada_horas=3, validade_dias=5,
         criterio=_CRITERIO_MOEDAS + " O BCE publica a cada dia útil, por volta das 16h de Frankfurt.",
         nivel=2, controle="multilateral", controlador="org:BCE",
         controlador_nome="Banco Central Europeu, instituição da União Europeia independente por tratado",
         controlador_fonte="https://www.ecb.europa.eu/ecb/orga/independence/html/index.en.html ; https://data.ecb.europa.eu/data/datasets/EXR"),
    # Saiu da lista em 21/10 (decisão 0012): o Fed publica uma vez por semana; o que foi gravado fica
    dict(id="fred_cambio", nome="FRED: câmbio do Fed (H.10) e índice do dólar", tipo="dados", pais="USA", idioma="en",
         conector="fred", url="https://fred.stlouisfed.org/graph/fredgraph.csv", a_cada_horas=12, validade_dias=12,
         ativa=False,
         criterio=_CRITERIO_MOEDAS + " O Fed publica a tabela H.10 às segundas, com a semana anterior; o índice amplo "
                                     "mede o dólar contra as moedas dos parceiros comerciais dos EUA.",
         nivel=1, controle="publico", controlador="estado:USA",
         controlador_nome="Federal Reserve (Conselho do Fed, autor da H.10; republicada pelo Banco do Fed de St. Louis)",
         controlador_fonte="https://www.federalreserve.gov/releases/h10/ ; https://fred.stlouisfed.org/legal/"),
    dict(id="yahoo_cambio", nome="Yahoo Finance: dólar no mercado (não oficial)", tipo="dados", pais="USA", idioma="en",
         conector="yahoo", url="https://query1.finance.yahoo.com/v8/finance/chart/", validade_dias=5,  # toda rodada (0016)
         dia_em_andamento=True,
         criterio=_CRITERIO_MOEDAS + " Cotação de mercado do mesmo dia, com o dia em andamento; não há fonte oficial "
                                     "diária contra o dólar. Conferida com o BCE (decisão 0012). Uso pessoal, não comercial.",
         nivel=3, controle="privado", controlador="grupo:yahoo",
         controlador_nome="Yahoo Inc., controlada por fundos da Apollo Global Management desde 2021 (a Verizon ficou com 10%)",
         controlador_fonte="https://en.wikipedia.org/wiki/Yahoo ; https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html"),
    dict(_YAHOO, id="yahoo_bolsas", nome="Yahoo Finance: bolsas (não oficial)",
         criterio="Índice principal da bolsa de cada membro do G20 com histórico, e o da zona do euro." + _CRITERIO_YAHOO),
    dict(_YAHOO, id="yahoo_commodities", nome="Yahoo Finance: commodities (não oficial)",
         criterio="Contratos futuros de referência mundial de energia, metais e grãos, que pesam em conflitos e sanções; "
                  "na troca de contrato, o preço pode saltar." + _CRITERIO_YAHOO),
    dict(_YAHOO, id="yahoo_cripto", nome="Yahoo Finance: cripto (não oficial)",
         criterio="As duas maiores criptomoedas por valor de mercado." + _CRITERIO_YAHOO),
    # Eventos com lugar no mapa (decisão 0014)
    dict(id="usgs_terremotos", nome="USGS: terremotos de magnitude 4,5 ou mais", tipo="dados", pais="USA", idioma="en",
         conector="usgs", url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson",
         criterio="Terremotos de magnitude 4,5 ou mais no mundo, nas últimas 24 horas, do serviço geológico oficial dos "
                  "EUA (feed público, sem chave): camada de contexto do mapa (decisão 0014).",
         nivel=1, controle="estatal", controlador="estado:USA",
         controlador_nome="Governo federal dos EUA (U.S. Geological Survey, Departamento do Interior)",
         controlador_fonte="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php ; https://www.usgs.gov/about/about-us"),
    # Navios por dia nos estreitos (decisão 0018)
    dict(id="portwatch", nome="FMI PortWatch: navios por dia nos estreitos", tipo="dados", pais=None, idioma="en",
         conector="portwatch",
         url="https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer",
         a_cada_horas=24, validade_dias=12,
         criterio="Navios por dia nos estreitos dos pontos críticos, contados pelo sinal AIS que os navios transmitem "
                  "(base pública do FMI com a Universidade de Oxford, sem chave, atualizada uma vez por semana). Navio "
                  "com o sinal desligado não entra na conta. Reuso permitido citando \"FMI, PortWatch\".",
         nivel=2, controle="multilateral", controlador="org:FMI",
         controlador_nome="Fundo Monetário Internacional (FMI), com a Universidade de Oxford",
         controlador_fonte="https://portwatch.imf.org/ ; https://www.imf.org/en/about/copyright-and-terms"),
    # Juros de 10 anos, oficiais (decisão 0013)
    dict(id="tesouro_eua", nome="Tesouro dos EUA: curva de juros diária", tipo="dados", pais="USA", idioma="en",
         conector="tesouro", url="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/",
         a_cada_horas=6, validade_dias=5, criterio=_CRITERIO_JUROS,
         nivel=1, controle="estatal", controlador="estado:USA", controlador_nome="Governo federal dos EUA (Departamento do Tesouro)",
         controlador_fonte="https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics"),
    dict(id="bundesbank", nome="Bundesbank: juros dos títulos federais alemães", tipo="dados", pais="DEU", idioma="en",
         conector="bundesbank", url="https://api.statistiken.bundesbank.de/rest/data/", a_cada_horas=6, validade_dias=5,
         criterio=_CRITERIO_JUROS, nivel=1, controle="publico", controlador="estado:DEU",
         controlador_nome="Deutsche Bundesbank, banco central da Alemanha, independente por lei (Lei do Bundesbank) e parte do Eurosistema",
         controlador_fonte="https://www.bundesbank.de/en/bundesbank/organisation ; https://www.bundesbank.de/en/statistics/time-series-databases"),
    dict(id="boe", nome="Banco da Inglaterra: juros dos títulos do governo", tipo="dados", pais="GBR", idioma="en",
         conector="boe", url="https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp", a_cada_horas=6,
         validade_dias=5, criterio=_CRITERIO_JUROS, nivel=1, controle="publico", controlador="estado:GBR",
         controlador_nome="Bank of England, banco central do Reino Unido, independente na política monetária desde 1998 (Bank of England Act)",
         controlador_fonte="https://www.bankofengland.co.uk/about ; https://www.bankofengland.co.uk/boeapps/database/"),
    dict(id="japao_mof", nome="Ministério das Finanças do Japão: juros dos títulos do governo", tipo="dados", pais="JPN",
         idioma="en", conector="japao", url="https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/",
         a_cada_horas=6, validade_dias=5, criterio=_CRITERIO_JUROS, nivel=1, controle="estatal", controlador="estado:JPN",
         controlador_nome="Governo do Japão (Ministério das Finanças)",
         controlador_fonte="https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/index.htm"),
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



def _serie(fonte: str, codigo: str, nome: str, unidade: str, pais: str | None, grupo: str, **extra) -> dict:
    ident = f"{fonte.split('_')[0]}_{re.sub(r'[^a-z0-9]', '', codigo.lower().replace('=x', '').replace('=f', ''))}"
    return dict(id=ident, fonte=fonte, codigo=codigo, nome=nome, unidade=unidade, pais=pais, grupo=grupo,
                frequencia="diaria", medida="variacao_pct") | extra


def _moeda(fonte: str, codigo: str, nome: str, unidade: str, pais: str | None, **extra) -> dict:
    return _serie(fonte, codigo, nome, unidade, pais, "moedas", **extra)


def _juros(fonte: str, codigo: str, nome: str, pais: str) -> dict:
    return _serie(fonte, codigo, nome, "% ao ano", pais, "juros", id=f"juros_{pais.lower()}_10a", medida="diferenca")


# Região de cada bolsa, só para agrupar o painel de mercados (decisão 0014): a do país do índice
REGIOES = {"americas": "Américas", "europa_africa": "Europa, Oriente Médio e África", "asia_pacifico": "Ásia e Pacífico"}
_REGIAO_DO_PAIS = {**dict.fromkeys(["USA", "BRA", "CAN", "MEX", "ARG"], "americas"),
                   **dict.fromkeys(["GBR", "DEU", "FRA", "ITA", "TUR", "ZAF"], "europa_africa"),
                   **dict.fromkeys(["CHN", "JPN", "IND", "AUS", "KOR", "IDN"], "asia_pacifico")}


def _bolsa(codigo: str, nome: str, pais: str | None, regiao: str | None = None) -> dict:
    return _serie("yahoo_bolsas", codigo, nome, "pontos", pais, "bolsas", id=f"bolsa_{re.sub(r'[^a-z0-9]', '', codigo.lower())}",
                  regiao=regiao or _REGIAO_DO_PAIS[pais])


def _commodity(codigo: str, nome: str, unidade: str) -> dict:
    return _serie("yahoo_commodities", codigo, nome, unidade, None, "commodities",
                  id=f"commodity_{codigo.lower().replace('=f', '')}")


def _dolar(codigo: str, nome: str, unidade: str, pais: str, conferir: tuple[str, str] | None) -> dict:
    """Yahoo (decisão 0012). `conferir`: a mesma cotação pela conta do BCE, numerador ÷ denominador."""
    return _moeda("yahoo_cambio", codigo, nome, unidade, pais, conferir=conferir)


def _fred(codigo: str, nome: str, unidade: str, pais: str) -> dict:
    return _moeda("fred_cambio", codigo, nome, unidade, pais, ativa=False)  # saiu em 21/10 (decisão 0012)


# Séries (decisões 0011 e 0012). O nome segue a fonte, sem conta: "Euro em reais" sobe quando o euro fica mais caro.
SERIES: list[dict] = [
    _moeda("bce_cambio", "USD", "Euro em dólares", "US$ por €", "USA"),
    _moeda("bce_cambio", "JPY", "Euro em ienes", "¥ por €", "JPN"),
    _moeda("bce_cambio", "GBP", "Euro em libras", "£ por €", "GBR"),
    _moeda("bce_cambio", "CNY", "Euro em yuans", "CN¥ por €", "CHN"),
    _moeda("bce_cambio", "BRL", "Euro em reais", "R$ por €", "BRA"),
    _moeda("bce_cambio", "INR", "Euro em rupias indianas", "₹ por €", "IND"),
    _moeda("bce_cambio", "IDR", "Euro em rupias indonésias", "Rp por €", "IDN"),
    _moeda("bce_cambio", "KRW", "Euro em wons", "₩ por €", "KOR"),
    _moeda("bce_cambio", "MXN", "Euro em pesos mexicanos", "MX$ por €", "MEX"),
    _moeda("bce_cambio", "TRY", "Euro em liras turcas", "₺ por €", "TUR"),
    _moeda("bce_cambio", "ZAR", "Euro em rands", "R por €", "ZAF"),
    _moeda("bce_cambio", "AUD", "Euro em dólares australianos", "A$ por €", "AUS"),
    _moeda("bce_cambio", "CAD", "Euro em dólares canadenses", "C$ por €", "CAN"),
    _dolar("BRL=X", "Dólar em reais", "R$ por US$", "BRA", ("bce_brl", "bce_usd")),
    _dolar("CNY=X", "Dólar em yuans", "CN¥ por US$", "CHN", ("bce_cny", "bce_usd")),
    _dolar("JPY=X", "Dólar em ienes", "¥ por US$", "JPN", ("bce_jpy", "bce_usd")),
    _dolar("GBPUSD=X", "Libra em dólares", "US$ por £", "GBR", ("bce_usd", "bce_gbp")),
    _dolar("INR=X", "Dólar em rupias indianas", "₹ por US$", "IND", ("bce_inr", "bce_usd")),
    _dolar("IDR=X", "Dólar em rupias indonésias", "Rp por US$", "IDN", ("bce_idr", "bce_usd")),
    _dolar("KRW=X", "Dólar em wons", "₩ por US$", "KOR", ("bce_krw", "bce_usd")),
    _dolar("MXN=X", "Dólar em pesos mexicanos", "MX$ por US$", "MEX", ("bce_mxn", "bce_usd")),
    _dolar("TRY=X", "Dólar em liras turcas", "₺ por US$", "TUR", ("bce_try", "bce_usd")),
    _dolar("ZAR=X", "Dólar em rands", "R por US$", "ZAF", ("bce_zar", "bce_usd")),
    _dolar("AUDUSD=X", "Dólar australiano em dólares americanos", "US$ por A$", "AUS", ("bce_usd", "bce_aud")),
    _dolar("CAD=X", "Dólar em dólares canadenses", "C$ por US$", "CAN", ("bce_cad", "bce_usd")),
    _dolar("DX-Y.NYB", "Índice do dólar (DXY)", "índice (mar/1973 = 100)", "USA", None),
    # Juros de 10 anos (decisão 0013); medida: diferença em pontos percentuais
    _juros("tesouro_eua", "10 Yr", "EUA: título de 10 anos", "USA"),
    _juros("bundesbank", "BBSIS.D.I.ZAR.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A", "Alemanha: título de 10 anos", "DEU"),
    _juros("boe", "IUDMNPY", "Reino Unido: título de 10 anos", "GBR"),
    _juros("japao_mof", "10Y", "Japão: título de 10 anos", "JPN"),
    # Bolsas (decisão 0013): índice principal de cada membro do G20 com histórico, e o da zona do euro
    _bolsa("^GSPC", "EUA: S&P 500", "USA"),
    _bolsa("^BVSP", "Brasil: Ibovespa", "BRA"),
    _bolsa("000001.SS", "China: Xangai (SSE Composite)", "CHN"),
    _bolsa("^N225", "Japão: Nikkei 225", "JPN"),
    _bolsa("^NSEI", "Índia: Nifty 50", "IND"),
    _bolsa("^FTSE", "Reino Unido: FTSE 100", "GBR"),
    _bolsa("^GDAXI", "Alemanha: DAX", "DEU"),
    _bolsa("^FCHI", "França: CAC 40", "FRA"),
    _bolsa("FTSEMIB.MI", "Itália: FTSE MIB", "ITA"),
    _bolsa("^GSPTSE", "Canadá: S&P/TSX", "CAN"),
    _bolsa("^AXJO", "Austrália: S&P/ASX 200", "AUS"),
    _bolsa("^KS11", "Coreia do Sul: KOSPI", "KOR"),
    _bolsa("^MXX", "México: IPC", "MEX"),
    _bolsa("^JKSE", "Indonésia: IDX Composite", "IDN"),
    _bolsa("XU100.IS", "Turquia: BIST 100", "TUR"),
    _bolsa("^J203.JO", "África do Sul: JSE All Share", "ZAF"),
    _bolsa("^MERV", "Argentina: Merval (em pesos)", "ARG"),
    _bolsa("^STOXX50E", "Zona do euro: EURO STOXX 50", None, regiao="europa_africa"),
    # Commodities (decisão 0013): contrato futuro mais próximo
    _commodity("BZ=F", "Petróleo Brent", "US$ por barril"),
    _commodity("CL=F", "Petróleo WTI", "US$ por barril"),
    _commodity("NG=F", "Gás natural nos EUA (Henry Hub)", "US$ por milhão de BTU"),
    _commodity("TTF=F", "Gás natural na Europa (TTF)", "€ por MWh"),
    _commodity("GC=F", "Ouro", "US$ por onça troy"),
    _commodity("SI=F", "Prata", "US$ por onça troy"),
    _commodity("HG=F", "Cobre", "US$ por libra-peso"),
    _commodity("ALI=F", "Alumínio", "US$ por tonelada"),
    _commodity("ZW=F", "Trigo", "centavos de US$ por bushel"),
    _commodity("ZC=F", "Milho", "centavos de US$ por bushel"),
    _commodity("ZS=F", "Soja", "centavos de US$ por bushel"),
    # Cripto (decisão 0013)
    _serie("yahoo_cripto", "BTC-USD", "Bitcoin", "US$", None, "cripto", id="cripto_btc"),
    _serie("yahoo_cripto", "ETH-USD", "Ether", "US$", None, "cripto", id="cripto_eth"),
    _fred("DTWEXBGS", "Índice amplo do dólar", "índice (jan/2006 = 100)", "USA"),
    _fred("DEXBZUS", "Dólar em reais", "R$ por US$", "BRA"),
    _fred("DEXCHUS", "Dólar em yuans", "CN¥ por US$", "CHN"),
    _fred("DEXJPUS", "Dólar em ienes", "¥ por US$", "JPN"),
    _fred("DEXUSUK", "Libra em dólares", "US$ por £", "GBR"),
    _fred("DEXINUS", "Dólar em rupias indianas", "₹ por US$", "IND"),
    _fred("DEXKOUS", "Dólar em wons", "₩ por US$", "KOR"),
    _fred("DEXMXUS", "Dólar em pesos mexicanos", "MX$ por US$", "MEX"),
    _fred("DEXCAUS", "Dólar em dólares canadenses", "C$ por US$", "CAN"),
    _fred("DEXUSAL", "Dólar australiano em dólares americanos", "US$ por A$", "AUS"),
    _fred("DEXSFUS", "Dólar em rands", "R por US$", "ZAF"),
]


# Navios por dia em cada ponto crítico (decisão 0018): todos os tipos e só os petroleiros, pela média de 7 dias
for _p in PONTOS:
    for _campo, _quem, _simb in (("n_total", "navios", "Navios"), ("n_tanker", "petroleiros", "Petroleiros")):
        SERIES.append(dict(id=f"{_quem}_{_p['id']}", fonte="portwatch", codigo=f"{_p['portwatch']}:{_campo}",
                           nome=f"{_p['nome']}: {_quem} por dia", unidade=f"{_quem} por dia", pais=None, grupo="navios",
                           frequencia="diaria", medida="media_7d", simbolo=_simb, ponto=_p["id"]))


def ativas(fontes: list[dict] = FONTES) -> list[dict]:
    return [f for f in fontes if f.get("ativa", True)]


# Símbolo no padrão do mercado (decisão 0016). Moedas como BASE/COTADA: USD/CAD = quantos C$ vale US$ 1.
_MOEDA_DO_PAIS = {"BRA": "BRL", "CHN": "CNY", "JPN": "JPY", "GBR": "GBP", "IND": "INR", "IDN": "IDR", "KOR": "KRW",
                  "MEX": "MXN", "TUR": "TRY", "ZAF": "ZAR", "AUS": "AUD", "CAN": "CAD"}
_SIMBOLOS = {
    "DX-Y.NYB": "DXY", "DTWEXBGS": "USD amplo", "DEXUSUK": "GBP/USD", "DEXUSAL": "AUD/USD",
    "BTC-USD": "BTC/USD", "ETH-USD": "ETH/USD",
    "^GSPC": "S&P 500", "^BVSP": "Ibovespa", "000001.SS": "SSE Composite", "^N225": "Nikkei 225", "^NSEI": "Nifty 50",
    "^FTSE": "FTSE 100", "^GDAXI": "DAX", "^FCHI": "CAC 40", "FTSEMIB.MI": "FTSE MIB", "^GSPTSE": "S&P/TSX",
    "^AXJO": "S&P/ASX 200", "^KS11": "KOSPI", "^MXX": "IPC", "^JKSE": "IDX Composite", "XU100.IS": "BIST 100",
    "^J203.JO": "JSE All Share", "^MERV": "Merval", "^STOXX50E": "EURO STOXX 50",
    "BZ=F": "Brent", "CL=F": "WTI", "NG=F": "Henry Hub", "TTF=F": "TTF", "GC=F": "Ouro", "SI=F": "Prata",
    "HG=F": "Cobre", "ALI=F": "Alumínio", "ZW=F": "Trigo", "ZC=F": "Milho", "ZS=F": "Soja",
}
_JUROS = {"USA": "US10Y", "DEU": "DE10Y", "GBR": "UK10Y", "JPN": "JP10Y"}


def _simbolo(s: dict) -> str:
    if s["codigo"] in _SIMBOLOS:
        return _SIMBOLOS[s["codigo"]]
    if s["grupo"] == "juros":
        return _JUROS[s["pais"]]
    if s["fonte"] == "bce_cambio":
        return f"EUR/{s['codigo']}"
    par = s["codigo"].removesuffix("=X")
    if len(par) == 6:  # GBPUSD=X, AUDUSD=X
        return f"{par[:3]}/{par[3:]}"
    return f"USD/{par if s['fonte'] == 'yahoo_cambio' else _MOEDA_DO_PAIS[s['pais']]}"


for _s in SERIES:
    if "simbolo" not in _s:
        _s["simbolo"] = _simbolo(_s)
