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
        assert f["criterio"] and f["tipo"] in {"oficial", "imprensa", "dados", "social"} and f["conector"] == "rss"
        assert f["url"].startswith("https://")


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
