"""Cópia semanal do banco (decisão 0007): copia só as tabelas do projeto e a cópia volta idêntica."""
import gzip
import json
from datetime import datetime

import pytest

from stratum import copia, db, export, fontes, resumo
from tests.conftest import fonte


def _encher(engine):
    """Um pouco de cada tabela, com acento, data com microssegundo e campo vazio."""
    agora = datetime(2026, 10, 19, 12, 0, 0, 123456)
    with engine.begin() as c:
        db.gravar_fontes(c, fontes.FONTES + [fonte("x", "https://x.example/rss", nome="Fonte ç")])
        rid = c.execute(db.rodada.insert().values(iniciada_em=agora, terminada_em=None, situacao="ok", banco="permanente",
                                                  versao="t")).inserted_primary_key[0]
        c.execute(db.coleta.insert().values(rodada_id=rid, fonte_id="x", iniciada_em=agora, terminada_em=agora,
                                            situacao="falhou", itens_lidos=0, itens_novos=0, erro="O site demorou."))
        c.execute(db.documento.insert(), [
            dict(hash=f"h{i}", fonte_id="x", rodada_id=rid, url=None if i == 0 else f"https://x.example/{i}",
                 titulo=f"Manchete nº {i}: “aspas”", resumo=None, publicado_em=None if i == 1 else agora,
                 conhecido_em=agora) for i in range(2500)])  # mais de um lote
        c.execute(db.resumo.insert().values(horario=agora, enviado_em=agora, situacao="enviado", texto="Resumo\ncom linha"))


def test_copia_so_as_tabelas_do_projeto():
    # O cofre (vault), o pg_cron e o pg_net não são tabelas do projeto e nunca entram na cópia pública
    assert {t.name for t in copia.tabelas()} == set(db.md.tables)
    assert not {"secrets", "decrypted_secrets", "job", "job_run_details", "_http_response"} & set(db.md.tables)


def test_copia_volta_identica(engine, tmp_path):
    _encher(engine)
    manifesto = copia.exportar(engine, tmp_path / "copia")
    assert manifesto["tabelas"]["documento"]["linhas"] == 2500
    assert manifesto["migracao"]
    assert json.loads((tmp_path / "copia" / "manifesto.json").read_text(encoding="utf-8")) == manifesto
    assert copia.testar_restauracao(tmp_path / "copia") == []


def test_restaurar_recupera_os_registros(engine, tmp_path):
    _encher(engine)
    copia.exportar(engine, tmp_path / "copia")
    destino = db.conectar(f"sqlite:///{tmp_path / 'novo.db'}")
    contagens = copia.restaurar(tmp_path / "copia", destino)
    assert contagens["documento"] == 2500 and contagens["resumo"] == 1
    with destino.connect() as c:
        doc = c.execute(db.documento.select().where(db.documento.c.hash == "h1")).mappings().one()
    assert doc["publicado_em"] is None
    assert doc["conhecido_em"] == datetime(2026, 10, 19, 12, 0, 0, 123456)
    assert doc["titulo"] == "Manchete nº 1: “aspas”"


def test_restaurar_so_em_banco_vazio(engine, tmp_path):
    # Nada é sobrescrito (regra 2): restaurar por cima de um banco com dados é recusado
    _encher(engine)
    copia.exportar(engine, tmp_path / "copia")
    with pytest.raises(ValueError, match="não está vazio"):
        copia.restaurar(tmp_path / "copia", engine)


def test_diferenca_entre_copias_aparece(engine, tmp_path):
    _encher(engine)
    copia.exportar(engine, tmp_path / "a")
    copia.exportar(engine, tmp_path / "b")
    assert copia.diferencas(tmp_path / "a", tmp_path / "b") == []
    with gzip.open(tmp_path / "b" / "resumo.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write("{}\n")
    assert copia.diferencas(tmp_path / "a", tmp_path / "b") == [
        "resumo: 1 linhas na cópia, 1 na restauração, primeira diferença na linha 1"]


def test_sem_banco_permanente_nao_copia(monkeypatch, tmp_path, capsys):
    for nome in ("DATABASE_URL", "SUPABASE_SENHA"):
        monkeypatch.delenv(nome, raising=False)
    assert copia.main(["--saida", str(tmp_path / "c")]) == 1
    assert "nada a copiar" in capsys.readouterr().out


def test_erro_de_banco_mostra_so_o_tipo(monkeypatch, tmp_path, capsys):
    # A mensagem do banco pode conter dados da conexão (regra 12)
    monkeypatch.setenv("DATABASE_URL", "postgresql://usuario:senha-secreta@127.0.0.1:1/postgres")
    assert copia.main(["--saida", str(tmp_path / "c")]) == 1
    saida = capsys.readouterr().out
    assert "senha-secreta" not in saida and "Não foi possível copiar o banco (" in saida


@pytest.mark.parametrize("ultima, esperado", [
    (None, "sem_dado"),                      # o workflow não conseguiu conferir
    ("", "nenhuma"),                         # nenhuma cópia no GitHub
    ("null", "nenhuma"),
    ("2026-10-18T09:41:00Z", "ok"),
    ("2026-10-11T12:00:00Z", "ok"),          # 8 dias: ainda no prazo
    ("2026-10-11T11:59:00Z", "atrasada"),
    ("não é data", "sem_dado"),
])
def test_situacao_da_copia(ultima, esperado):
    estado = copia.situacao(ultima, datetime(2026, 10, 19, 12, 0))
    assert estado["situacao"] == esperado
    assert estado["texto"] == copia.TEXTOS[esperado]


def test_copia_atrasada_entra_no_resumo(engine):
    agora = datetime(2026, 10, 19, 22, 5)  # 19:05 em Brasília
    texto = resumo.montar(engine, agora, resumo.horario_devido(agora), None, None,
                          copia=copia.situacao("2026-10-01T09:41:00Z", agora))
    assert "Cópia do banco: atrasada: o normal é uma por semana (a última é de 01/10 6:41)." in texto
    em_dia = resumo.montar(engine, agora, resumo.horario_devido(agora), None, None,
                           copia=copia.situacao("2026-10-18T09:41:00Z", agora))
    assert "Cópia do banco" not in em_dia


def test_nenhuma_copia_entra_no_resumo_e_no_site(engine):
    agora = datetime(2026, 10, 19, 22, 5)
    estado = copia.situacao("", agora)
    texto = resumo.montar(engine, agora, resumo.horario_devido(agora), None, None, copia=estado)
    assert "Cópia do banco: nenhuma cópia feita ainda." in texto
    assert export.montar(engine, copia=estado)["copia"] == {"situacao": "nenhuma", "texto": "nenhuma cópia feita ainda",
                                                           "ultima": None}


def test_restaurar_pela_linha_de_comando(engine, tmp_path, monkeypatch, capsys):
    _encher(engine)
    copia.exportar(engine, tmp_path / "copia")
    monkeypatch.delenv("SUPABASE_SENHA", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'novo.db'}")
    assert copia.main(["--restaurar", str(tmp_path / "copia")]) == 0
    assert "documento 2500" in capsys.readouterr().out
    # De novo no mesmo banco: recusado, nada é sobrescrito
    assert copia.main(["--restaurar", str(tmp_path / "copia")]) == 1
    assert "Restauração recusada" in capsys.readouterr().out


def test_rodada_sem_conferir_a_copia_nao_avisa(engine):
    # Fora da main o workflow não confere a cópia: sem dado não é problema
    agora = datetime(2026, 10, 19, 22, 5)
    texto = resumo.montar(engine, agora, resumo.horario_devido(agora), None, None, copia=copia.situacao(None, agora))
    assert "Cópia do banco" not in texto
