"""Esquema do banco e acesso. PostgreSQL (Supabase) em produção, SQLite em testes e no banco temporário.

Regras que o esquema garante:
- todo registro tem a data em que o sistema soube dele (`conhecido_em`), em UTC;
- documento repetido não entra duas vezes (`documento.hash` é único);
- nada é apagado nem reescrito: o robô só insere.
Mudou o esquema? Crie uma migração nova em `migracoes/versions/` (o robô aplica sozinho na próxima rodada).
"""
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, MetaData, String, Table, Text,
                        create_engine)
from sqlalchemy.dialects import postgresql, sqlite

md = MetaData()
Id = BigInteger().with_variant(Integer, "sqlite")  # SQLite só autoincrementa INTEGER

fonte = Table(
    "fonte", md,
    Column("id", String(64), primary_key=True),
    Column("nome", Text, nullable=False),
    Column("tipo", String(16), nullable=False),        # oficial | imprensa | dados | social
    Column("pais", String(3)),                          # ISO 3166 alfa-3 de onde a fonte publica
    Column("idioma", String(8)),
    Column("url", Text, nullable=False),                # endereço lido pelo robô
    Column("criterio", Text),                           # por que a fonte está na lista
    Column("ativa", Boolean, nullable=False),
    # Ficha da fonte (decisão 0008)
    Column("nivel", Integer),                           # 1 governo, 2 multilateral, 3 empresa, 4 imprensa, 5 rede social
    Column("controle", String(16)),                     # privado | publico | estatal | multilateral
    Column("controlador", String(64)),                  # mesmo controlador = uma voz só
    Column("controlador_nome", Text),
    Column("controlador_fonte", Text),                  # onde está escrito quem controla (endereços separados por " ; ")
)

rodada = Table(
    "rodada", md,
    Column("id", Id, primary_key=True, autoincrement=True),
    Column("iniciada_em", DateTime, nullable=False),
    Column("terminada_em", DateTime),
    Column("situacao", String(16), nullable=False),    # rodando | ok | parcial | falhou
    Column("banco", String(16), nullable=False),       # permanente | temporario
    Column("versao", String(32), nullable=False),
)

coleta = Table(
    "coleta", md,
    Column("id", Id, primary_key=True, autoincrement=True),
    Column("rodada_id", Id, ForeignKey("rodada.id"), nullable=False),
    Column("fonte_id", String(64), ForeignKey("fonte.id"), nullable=False),
    Column("iniciada_em", DateTime, nullable=False),
    Column("terminada_em", DateTime),
    Column("situacao", String(16), nullable=False),    # ok | falhou
    Column("itens_lidos", Integer, nullable=False),
    Column("itens_novos", Integer, nullable=False),
    Column("erro", Text),
    Index("ix_coleta_fonte", "fonte_id", "iniciada_em"),
)

documento = Table(
    "documento", md,
    Column("id", Id, primary_key=True, autoincrement=True),
    Column("hash", String(64), nullable=False, unique=True),
    Column("fonte_id", String(64), ForeignKey("fonte.id"), nullable=False),
    Column("rodada_id", Id, ForeignKey("rodada.id")),
    Column("url", Text),
    Column("titulo", Text, nullable=False),
    Column("resumo", Text),                             # trecho curto; o texto inteiro fica na fonte
    Column("publicado_em", DateTime),                   # o que a fonte diz
    Column("conhecido_em", DateTime, nullable=False),   # quando o robô viu pela primeira vez
    Index("ix_documento_conhecido", "conhecido_em"),
    Index("ix_documento_fonte", "fonte_id", "conhecido_em"),
)

resumo = Table(
    "resumo", md,
    Column("id", Id, primary_key=True, autoincrement=True),
    Column("horario", DateTime, nullable=False, unique=True),  # 7:30, 12:00 ou 19:00 de Brasília, em UTC
    Column("enviado_em", DateTime, nullable=False),
    Column("situacao", String(16), nullable=False),            # enviado | sem_telegram
    Column("texto", Text, nullable=False),                     # o que foi enviado (decisão 0005)
)

MIGRACOES = Path(__file__).parent / "migracoes"


def agora() -> datetime:
    """Momento atual em UTC, sem fuso (padrão de todas as datas do banco)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def conectar(url: str | None):
    """Abre o banco. Sem URL, cria um SQLite temporário que some no fim da execução."""
    if not url:
        caminho = os.path.join(tempfile.mkdtemp(prefix="stratum-"), "temporario.db")
        url = f"sqlite:///{caminho}"
    elif url.startswith("postgresql://") or url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    return create_engine(url, pool_pre_ping=True)


def _alembic() -> AlembicConfig:
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(MIGRACOES))
    return cfg


def preparar(engine, ate: str = "head") -> None:
    """Cria ou atualiza as tabelas aplicando as migrações pendentes. Rodar de novo não muda nada.
    `ate`: a versão do esquema a alcançar (a restauração de uma cópia sobe só até a versão dela)."""
    cfg = _alembic()
    with engine.begin() as conexao:
        cfg.attributes["connection"] = conexao
        command.upgrade(cfg, ate)


def versoes_do_esquema() -> list[str]:
    """As versões do esquema (migrações) que este código conhece, da mais antiga para a mais nova."""
    return [s.revision for s in reversed(list(ScriptDirectory.from_config(_alembic()).walk_revisions()))]


def versao_do_banco(engine) -> str | None:
    """A versão do esquema em que o banco está; None se nunca foi preparado."""
    with engine.connect() as c:
        return MigrationContext.configure(c).get_current_revision()


def inserir_ignorando_repetidos(conexao, tabela, linhas: list[dict], chave: str) -> None:
    """Insere linhas; a que já existe (mesma `chave` única) é ignorada, nunca sobrescrita."""
    if not linhas:
        return
    dialeto = postgresql if conexao.dialect.name == "postgresql" else sqlite
    for i in range(0, len(linhas), 1000):
        stmt = dialeto.insert(tabela).values(linhas[i:i + 1000]).on_conflict_do_nothing(index_elements=[chave])
        conexao.execute(stmt)


def gravar_fontes(conexao, fontes: list[dict]) -> None:
    """A lista de fontes vive no código (`fontes.py`); o banco recebe a versão atual a cada rodada.
    Fonte que saiu da lista fica no banco como inativa: os documentos dela continuam com a origem."""
    dialeto = postgresql if conexao.dialect.name == "postgresql" else sqlite
    for f in fontes:
        linha = {k: f.get(k) for k in ("id", "nome", "tipo", "pais", "idioma", "url", "criterio", "nivel", "controle",
                                       "controlador", "controlador_nome", "controlador_fonte")} | {"ativa": f.get("ativa", True)}
        stmt = dialeto.insert(fonte).values(linha)
        conexao.execute(stmt.on_conflict_do_update(index_elements=["id"], set_={k: stmt.excluded[k] for k in linha if k != "id"}))
    conexao.execute(fonte.update().where(fonte.c.id.not_in([f["id"] for f in fontes])).values(ativa=False))
