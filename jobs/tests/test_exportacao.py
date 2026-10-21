"""O status que o site mostra: citações de países na janela de 24h, mais citados e origem das fontes."""
from datetime import datetime, timedelta

from stratum import export, robo
from conftest import SessaoFalsa, fonte

AGORA = datetime(2026, 10, 16, 12, 0, 0)


def _rss(itens: list[tuple[str, str, datetime | None]], prefixo: str = "n") -> bytes:
    corpo = "".join(
        f"<item><title>{t}</title><link>https://{prefixo}.example/{i}</link>"
        + (f"<pubDate>{d.strftime('%a, %d %b %Y %H:%M:%S')} GMT</pubDate>" if d else "") + "</item>"
        for i, (t, _, d) in enumerate(itens))
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{corpo}</channel></rss>'.encode()


def _rodar(engine, cfg, feeds: dict[str, tuple[dict, bytes]]):
    fontes = [f for f, _ in feeds.values()]
    respostas = {f["url"]: conteudo for f, conteudo in feeds.values()}
    robo.rodar(engine, fontes, SessaoFalsa(respostas), cfg, agora=lambda: AGORA)
    return export.montar(engine, agora=lambda: AGORA)


def test_citacoes_por_pais_na_janela(engine, cfg):
    imprensa = _rss([
        ("Russia strikes Ukrainian ports", "", AGORA - timedelta(hours=1)),
        ("Kremlin and Brazil sign deal", "", AGORA - timedelta(hours=3)),
        ("Old news about Russia", "", AGORA - timedelta(hours=30)),       # fora da janela de 24h
        ("Russia from the future", "", AGORA + timedelta(hours=5)),       # data adiantada demais: vale a da coleta
        ("Weather report", "", AGORA - timedelta(hours=2)),
        ("India exports rice", "", None),                                 # sem data da fonte: vale a da coleta
    ])
    oficial = _rss([("Treasury sanctions Iranian network", "", AGORA - timedelta(hours=4))], prefixo="oficial")
    social = _rss([("Russia Russia Austria", "", AGORA - timedelta(hours=1))], prefixo="social")  # pista: não conta
    s = _rodar(engine, cfg, {
        "a": (fonte("imprensa_gbr", "https://a/feed", pais="GBR"), imprensa),
        "b": (fonte("oficial_usa", "https://b/feed", pais="USA", tipo="oficial"), oficial),
        "c": (fonte("social_usa", "https://c/feed", pais="USA", tipo="social"), social),
    })
    a = s["atencao"]
    assert a["documentos"] == 6 and a["documentos_com_pais"] == 5 and a["oficiais"] == 1 and a["paises_citados"] == 5
    assert a["regra"] == "paises-0.2" and "Georgia" in a["ignorados"]
    rus = s["paises"]["RUS"]
    assert rus["nome"] == "Rússia" and rus["citacoes"] == 3 and rus["nivel"] == 2
    assert [d["titulo"] for d in rus["documentos"]] == [
        "Russia from the future", "Russia strikes Ukrainian ports", "Kremlin and Brazil sign deal"]
    assert "AUT" not in s["paises"]
    # empate: ordem alfabética sem acento (Índia vem antes de Irã e de Ucrânia)
    assert [p["iso"] for p in s["mais_citados"]] == ["RUS", "BRA", "IND", "IRN", "UKR"]
    assert s["mais_citados"][0]["proporcao"] == 1.0 and s["mais_citados"][1]["proporcao"] == 0.3333
    assert s["origem_fontes"] == [{"pais": "GBR", "nome": "Reino Unido", "documentos": 5, "proporcao": 1.0},
                                  {"pais": "USA", "nome": "Estados Unidos", "documentos": 1, "proporcao": 0.2}]
    assert s["avisar_atraso_apos"] == "2026-10-16T14:00:00Z"
    # 25 h depois, a notícia de data adiantada sai da janela (vale a hora da coleta, não a data futura)
    depois = export.montar(engine, agora=lambda: AGORA + timedelta(hours=25))
    assert depois["atencao"]["documentos"] == 0 and "RUS" not in depois["paises"]


def test_ultimos_documentos_mais_recentes_primeiro_com_paises(engine, cfg):
    feed = _rss([("Older: China exports", "", AGORA - timedelta(hours=5)),
                 ("Newer: India election", "", AGORA - timedelta(minutes=30))])
    s = _rodar(engine, cfg, {"a": (fonte("a", "https://a/feed", pais="IND", controle="privado"), feed)})
    primeiro, segundo = s["ultimos_documentos"]
    assert primeiro["titulo"] == "Newer: India election" and primeiro["paises"] == [{"iso": "IND", "nome": "Índia"}]
    assert primeiro["fonte_pais_nome"] == "Índia" and primeiro["fonte_tipo"] == "imprensa"
    assert primeiro["fonte_controle"] == "privado"  # quem é dono da fonte, ao lado de cada notícia (decisão 0014)
    assert segundo["paises"][0]["iso"] == "CHN"


def test_sem_noticias_na_janela(engine, cfg):
    feed = _rss([("Russia old", "", AGORA - timedelta(days=3))])
    s = _rodar(engine, cfg, {"a": (fonte("a", "https://a/feed"), feed)})
    assert s["paises"] == {} and s["mais_citados"] == [] and s["atencao"]["documentos"] == 0
    assert len(s["ultimos_documentos"]) == 1  # a lista de últimas notícias não fica vazia por causa da janela


def test_diagnostico_mostra_termos_e_paises(engine, cfg):
    feed = _rss([("Kremlin rejects US plan", "", AGORA - timedelta(hours=1)), ("Weather", "", AGORA - timedelta(hours=1))])
    _rodar(engine, cfg, {"a": (fonte("a", "https://a/feed"), feed)})
    linhas = export.diagnostico(engine, agora=lambda: AGORA)
    assert linhas[0].startswith("[RUS,USA] (Kremlin; US) a: Kremlin rejects US plan")
    assert linhas[1].startswith("[-] () a: Weather")


def test_niveis_de_cor():
    assert [export.nivel(n) for n in (0, 1, 2, 3, 9, 10, 29, 30, 500)] == [0, 1, 1, 2, 2, 3, 3, 4, 4]
