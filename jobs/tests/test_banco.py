from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from stratum import db, fontes


def test_migracoes_batem_com_o_esquema(engine):
    with engine.connect() as c:
        diferencas = compare_metadata(MigrationContext.configure(c), db.md)
    assert diferencas == []


def test_preparar_de_novo_nao_muda_nada(engine):
    db.preparar(engine)  # o robô faz isso a cada rodada


def test_conectar_converte_url_do_supabase():
    e = db.conectar("postgresql://u:senha@host:5432/postgres")
    assert e.url.drivername == "postgresql+psycopg"


def test_toda_fonte_tem_criterio_e_ids_unicos():
    ids = [f["id"] for f in fontes.FONTES]
    assert len(ids) == len(set(ids))
    for f in fontes.FONTES:
        assert f["criterio"] and f["tipo"] in {"oficial", "imprensa", "dados", "social"}
        assert (f["conector"] == "rss") == (f["tipo"] != "dados") and f["url"].startswith("https://")


def test_toda_serie_tem_fonte_de_dados_e_medida_da_regua():
    # Decisão 0011: a série herda o critério da fonte; a fonte de dados diz o ritmo e a validade
    from stratum import robo
    from stratum.domain import regua
    por_id = {f["id"]: f for f in fontes.FONTES}
    ids = [s["id"] for s in fontes.SERIES]
    assert len(ids) == len(set(ids))
    ativas = {s["id"]: s for s in fontes.SERIES if s.get("ativa", True)}
    assert len(ativas) == 26  # 13 moedas contra o euro (BCE), 12 contra o dólar e o DXY (Yahoo, decisão 0012)
    for s in fontes.SERIES:
        f = por_id[s["fonte"]]
        assert f["tipo"] == "dados" and f["conector"] in robo.CONECTORES_SERIES
        assert f["a_cada_horas"] > 0 and f["validade_dias"] > 0
        assert s["medida"] in regua.MEDIDAS and s["frequencia"] in regua.MINIMO and s["nome"] and s["unidade"]
        assert f.get("ativa", True) or not s.get("ativa", True)  # fonte fora da lista leva as séries junto
        # É verdade? A conferência usa séries oficiais ativas (decisão 0012)
        for outra in s.get("conferir") or ():
            assert outra in ativas and por_id[ativas[outra]["fonte"]]["nivel"] in {1, 2}
    assert all(s.get("conferir") for s in ativas.values() if s["fonte"] == "yahoo_cambio" and "DX-Y" not in s["codigo"])


def test_toda_fonte_tem_ficha_com_fonte_da_informacao():
    # Decisão 0008: sem saber quem controla a fonte, não dá para dizer se duas notícias são vozes independentes
    for f in fontes.FONTES:
        assert f["nivel"] in {1, 2, 3, 4, 5}
        assert f["controle"] in {"privado", "publico", "estatal", "multilateral"}
        assert f["controlador"].split(":")[0] in {"estado", "grupo", "org"} and f["controlador_nome"]
        assert all(u.strip().startswith("https://") for u in f["controlador_fonte"].split(";"))
        # O tipo de hoje e o nível novo não podem se contradizer
        assert {"oficial": {1, 2}, "imprensa": {4}, "dados": {1, 2, 3}, "social": {5}}[f["tipo"]] >= {f["nivel"]}
        if f["controle"] in {"publico", "estatal"}:
            assert f["controlador"].startswith("estado:")  # público e estatal do mesmo país são a mesma voz


def test_ficha_da_fonte_vai_para_o_banco_e_para_o_site(engine):
    from stratum import export
    with engine.begin() as c:
        db.gravar_fontes(c, fontes.FONTES)
    tass = next(f for f in export.montar(engine)["fontes"] if f["id"] == "tass")
    assert (tass["nivel"], tass["controle"]) == (4, "estatal")
    assert tass["controlador_fontes"][0].startswith("https://")
