"""Arquivo conferido: registro dos arquivamentos e impressão curta das notícias arquivadas (decisão 0015).

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

Id = sa.BigInteger().with_variant(sa.Integer, "sqlite")


def upgrade() -> None:
    op.create_table(
        "arquivo",
        sa.Column("id", Id, primary_key=True, autoincrement=True),
        sa.Column("etiqueta", sa.String(64), nullable=False),
        sa.Column("tabela", sa.String(64), nullable=False),
        sa.Column("corte", sa.DateTime, nullable=False),
        sa.Column("linhas", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("detalhe", sa.Text),
        sa.Column("feito_em", sa.DateTime, nullable=False),
    )
    op.create_index("ux_arquivo_tabela", "arquivo", ["etiqueta", "tabela"], unique=True)
    op.create_table(
        "documento_arquivado",
        sa.Column("hash_curto", sa.BigInteger, primary_key=True, autoincrement=False),
        sa.Column("arquivado_em", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    raise NotImplementedError("Nada é reescrito: corrija com uma migração nova.")
