"""Sonda endereços candidatos a fonte, do jeito que o robô lê (mesmo conector e mesmo User-Agent).

Roda no GitHub Actions (workflow sondar.yml), porque a máquina do Claude não alcança a maioria dos sites.
Para cada candidato, mostra se respondeu, quantos itens trouxe, a data mais recente e as 3 primeiras manchetes.
Nada é gravado: é só para decidir o que entra em fontes.py (regra 5).

Uso:  python scripts/sondar_fontes.py

Resultado de 20/10/2026: funcionaram uk_fcdo, uk_fcdo_org, uk_ofsi (parado desde junho), ue_conselho, ue_comissao,
ue_eurlex_jo (100 atos técnicos por dia), ru_kremlin e ru_mid. Falharam: ue_conselho_b, otan (404), cn_governo e
cn_mre (não são feeds), in_pib, in_mea e jp_mofa (403) e br_itamaraty (404). Entraram em fontes.py: uk_fcdo,
ue_conselho, ue_comissao e ru_mid.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stratum import config  # noqa: E402
from stratum.connectors import rss  # noqa: E402

GOVUK = "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D="
CANDIDATOS = [
    # Reino Unido (reserva para garantir 3 blocos)
    ("uk_fcdo", GOVUK + "foreign-commonwealth-development-office"),
    ("uk_fcdo_org", "https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom"),
    ("uk_ofsi", GOVUK + "office-of-financial-sanctions-implementation"),
    # União Europeia
    ("ue_conselho", "https://www.consilium.europa.eu/en/rss/pressreleases.ashx"),
    ("ue_conselho_b", "https://www.consilium.europa.eu/en/press/press-releases/rss/"),
    ("ue_comissao", "https://ec.europa.eu/commission/presscorner/api/rss?language=en"),
    ("ue_eurlex_jo", "https://eur-lex.europa.eu/EN/display-feed.rss?rssId=222"),
    # OTAN
    ("otan", "https://www.nato.int/cps/rss/en/natohq/rssFeed.xsl/rssFeed.xml"),
    # Rússia
    ("ru_kremlin", "http://en.kremlin.ru/events/president/news/feed"),
    ("ru_mid", "https://mid.ru/en/rss.php"),
    # China
    ("cn_governo", "https://english.www.gov.cn/rss/news.xml"),
    ("cn_mre", "https://www.fmprc.gov.cn/eng/rss.xml"),
    # Índia
    ("in_pib", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"),
    ("in_mea", "https://www.mea.gov.in/rss/press-releases.xml"),
    # Brasil
    ("br_itamaraty", "https://www.gov.br/mre/pt-br/canais_atendimento/imprensa/notas-a-imprensa/RSS"),
    # Japão
    ("jp_mofa", "https://www.mofa.go.jp/rss/press.xml"),
]


def main() -> None:
    sessao, ua = rss.nova_sessao(), config.ler().user_agent
    for fid, url in CANDIDATOS:
        try:
            itens = rss.ler({"id": fid, "url": url}, sessao, ua)
        except Exception as exc:  # noqa: BLE001 - a sonda só relata
            print(f"FALHOU {fid}: {type(exc).__name__}: {str(exc)[:120]}  [{url}]")
            continue
        datas = [i.publicado_em for i in itens if i.publicado_em]
        print(f"OK {fid}: {len(itens)} itens, mais recente {max(datas) if datas else 'sem data'}  [{url}]")
        for i in itens[:3]:
            print(f"    - {i.titulo[:110]}")


if __name__ == "__main__":
    main()
