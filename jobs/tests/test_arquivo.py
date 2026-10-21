"""Arquivo conferido (decisão 0015): o que passou do prazo sai do banco só depois de guardado e conferido."""
import gzip
import hashlib
import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from conftest import fonte
from stratum import arquivo, db, export

AGORA = datetime(2027, 11, 2, 11, 0)
VELHO = AGORA - timedelta(days=400)      # passou dos 12 meses
NOVO = AGORA - timedelta(days=10)
URL = "https://github.com/dono/repo/releases/tag/arquivo-2027-11-02-1100"


def _contar(engine, tabela):
    with engine.connect() as c:
        return c.execute(select(func.count()).select_from(tabela)).scalar()


def _encher(engine):
    """3 notícias antigas (uma é a primeira de uma história que continua numa notícia nova), 1 nova, traduções e
    ligações, e o registro de leituras de duas épocas."""
    with engine.begin() as c:
        db.gravar_fontes(c, [fonte("a", "https://a/feed"), fonte("b", "https://b/feed")])
        rid = c.execute(db.rodada.insert().values(iniciada_em=VELHO, situacao="ok", banco="temporario", versao="t")
                        ).inserted_primary_key[0]
        docs = [(1, "a", VELHO), (2, "a", VELHO), (3, "b", VELHO), (4, "b", NOVO)]
        c.execute(db.documento.insert(), [
            dict(id=i, hash=hashlib.sha256(str(i).encode()).hexdigest(), fonte_id=f, rodada_id=rid, url=f"https://{f}/{i}",
                 titulo=f"Notícia {i}", resumo="Trecho", publicado_em=quando, conhecido_em=quando) for i, f, quando in docs])
        c.execute(db.historia_documento.insert(), [
            dict(documento_id=1, historia_id=1, conhecido_em=VELHO, regra="historias-0.1"),
            dict(documento_id=2, historia_id=2, conhecido_em=VELHO, regra="historias-0.1"),
            dict(documento_id=4, historia_id=2, conhecido_em=NOVO, regra="historias-0.1")])  # a 2 continua na 4
        c.execute(db.traducao.insert(), [
            dict(documento_id=i, campo="titulo", idioma="pt", texto=f"Notícia {i}", modelo="argos", conhecido_em=VELHO)
            for i in (1, 3)])
        c.execute(db.coleta.insert(), [
            dict(rodada_id=rid, fonte_id="a", iniciada_em=quando, terminada_em=quando, situacao="ok", itens_lidos=3,
                 itens_novos=1) for quando in (AGORA - timedelta(days=40), AGORA - timedelta(days=5))])


def _linhas(pasta, tabela):
    with gzip.open(pasta / f"{tabela}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f]


def test_separa_so_o_que_passou_do_prazo_e_nada_sai_ainda(engine, tmp_path):
    _encher(engine)
    m = arquivo.separar(engine, tmp_path, agora=AGORA)
    # a notícia 2 é a primeira de uma história que continua numa notícia que fica: fica também
    assert [d["id"] for d in _linhas(tmp_path, "documento")] == [1, 3]
    assert [x["documento_id"] for x in _linhas(tmp_path, "historia_documento")] == [1]
    assert [x["documento_id"] for x in _linhas(tmp_path, "traducao")] == [1, 3]
    assert len(_linhas(tmp_path, "coleta")) == 1
    assert {t: x["linhas"] for t, x in m["tabelas"].items()} == {"documento": 2, "historia_documento": 1, "traducao": 2,
                                                                    "coleta": 1}
    assert m["por_fonte"] == {"a": 1, "b": 1} and m["etiqueta"] == "arquivo-2027-11-02-1100"
    assert _contar(engine, db.documento) == 4  # separar não tira nada


def test_nada_a_arquivar_nao_gera_arquivo(engine, tmp_path):
    _encher(engine)
    assert arquivo.separar(engine, tmp_path / "vazio", agora=VELHO) is None
    assert not (tmp_path / "vazio").exists()


def test_tira_depois_de_conferir_registra_e_os_numeros_continuam_inteiros(engine, tmp_path):
    _encher(engine)
    arquivo.separar(engine, tmp_path, agora=AGORA)
    tirados = arquivo.conferir_e_tirar(engine, tmp_path, url=URL)
    assert tirados == {"traducao": 2, "historia_documento": 1, "documento": 2, "coleta": 1}
    with engine.connect() as c:
        assert sorted(c.execute(select(db.documento.c.id)).scalars()) == [2, 4]
        registros = c.execute(select(db.arquivo)).mappings().all()
    assert {r["tabela"]: r["linhas"] for r in registros}["documento"] == 2 and all(r["url"] == URL for r in registros)
    assert _contar(engine, db.documento_arquivado) == 2
    s = export.montar(engine, agora=lambda: AGORA)
    assert s["totais"]["documentos"] == 4  # 2 no banco + 2 no arquivo
    assert {f["id"]: f["documentos"] for f in s["fontes"]} == {"a": 2, "b": 2}
    assert s["arquivo"]["documentos"] == 2 and s["arquivo"]["ultimo"]["url"] == URL


@pytest.mark.parametrize("estragar", ["sem_refazer_a_impressao", "refazendo_a_impressao"])
def test_arquivo_diferente_do_banco_nada_sai(engine, tmp_path, estragar):
    _encher(engine)
    m = arquivo.separar(engine, tmp_path, agora=AGORA)
    linhas = _linhas(tmp_path, "documento")
    linhas[0]["titulo"] = "Título trocado"
    with gzip.open(tmp_path / "documento.jsonl.gz", "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in linhas)
    if estragar == "refazendo_a_impressao":
        m["tabelas"]["documento"]["sha256"] = hashlib.sha256((tmp_path / "documento.jsonl.gz").read_bytes()).hexdigest()
        (tmp_path / "manifesto.json").write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(ValueError, match="nada saiu do banco"):
        arquivo.conferir_e_tirar(engine, tmp_path, url=URL)
    assert _contar(engine, db.documento) == 4 and _contar(engine, db.coleta) == 2 and _contar(engine, db.arquivo) == 0


def test_restaurar_devolve_o_arquivo_sem_repetir(engine, tmp_path):
    _encher(engine)
    arquivo.separar(engine, tmp_path, agora=AGORA)
    arquivo.conferir_e_tirar(engine, tmp_path, url=URL)
    assert arquivo.restaurar(tmp_path, engine) == {"documento": 2, "historia_documento": 1, "traducao": 2, "coleta": 1}
    assert arquivo.restaurar(tmp_path, engine) == {"documento": 0, "historia_documento": 0, "traducao": 0, "coleta": 0}
    assert _contar(engine, db.documento) == 4 and _contar(engine, db.coleta) == 2
