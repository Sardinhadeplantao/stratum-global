"""Títulos em português (decisão 0010): tradução gravada uma vez, original preservado, sistema funciona sem ela."""
from datetime import datetime, timedelta

from stratum import db, export, fontes, traducao

T0 = datetime(2026, 10, 20, 12, 0)


def _inserir(engine, manchetes):
    with engine.begin() as c:
        db.gravar_fontes(c, fontes.FONTES)
        for k, (fonte, titulo) in enumerate(manchetes):
            q = T0 + timedelta(minutes=k)
            c.execute(db.documento.insert().values(hash=f"h{k}", fonte_id=fonte, titulo=titulo, publicado_em=q, conhecido_em=q))


def falso(textos):
    return [f"[pt] {t}" for t in textos]


def test_traduz_so_o_que_nao_esta_em_portugues_e_uma_vez_so(engine):
    _inserir(engine, [("bbc_mundo", "Floods hit Assam"), ("folha_mundo", "Chuvas atingem Assam")])
    assert traducao.atualizar(engine, T0 + timedelta(hours=1), falso)["traduzidos"] == 1
    assert traducao.atualizar(engine, T0 + timedelta(hours=2), falso)["traduzidos"] == 0
    with engine.connect() as c:
        linhas = c.execute(db.traducao.select()).mappings().all()
        original = c.execute(db.documento.select().where(db.documento.c.fonte_id == "bbc_mundo")).mappings().one()
    assert [(l["texto"], l["modelo"]) for l in linhas] == [("[pt] Floods hit Assam", traducao.MODELO)]
    assert original["titulo"] == "Floods hit Assam"  # o original não muda (regra 2)


def test_site_mostra_o_titulo_em_portugues_com_o_original_junto(engine):
    _inserir(engine, [("bbc_mundo", "Floods hit Assam"), ("folha_mundo", "Chuvas atingem Assam")])
    traducao.atualizar(engine, T0 + timedelta(hours=1), falso)
    docs = {d["fonte"]: d for d in export.montar(engine, agora=lambda: T0 + timedelta(hours=1))["ultimos_documentos"]}
    assert (docs["bbc_mundo"]["titulo"], docs["bbc_mundo"]["titulo_original"]) == ("[pt] Floods hit Assam", "Floods hit Assam")
    assert (docs["folha_mundo"]["titulo"], docs["folha_mundo"]["titulo_original"]) == ("Chuvas atingem Assam", None)


def test_sem_traducao_o_site_mostra_o_original(engine):
    _inserir(engine, [("bbc_mundo", "Floods hit Assam")])
    doc = export.montar(engine, agora=lambda: T0 + timedelta(hours=1))["ultimos_documentos"][0]
    assert (doc["titulo"], doc["titulo_original"]) == ("Floods hit Assam", None)


def test_pedacos_do_modelo_viram_texto_com_espacos():
    # Saída real do modelo na sonda de 20/10: os pedaços chegam com "▁" no lugar do espaço
    pedacos = ["▁A", "▁Indonésia", "▁combate", "▁piores", "▁incêndios", "▁em", "▁11", "▁anos", "."]
    assert traducao.juntar(pedacos, "Indonesia battles worst fires in 11 years") == "A Indonésia combate piores incêndios em 11 anos"
    assert traducao.juntar(["▁EUA", "▁sobem", "▁tarifas", "."], "US raises tariffs.") == "EUA sobem tarifas."
