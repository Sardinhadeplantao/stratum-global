"""Séries de dados e observações (decisão 0011).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

Id = sa.BigInteger().with_variant(sa.Integer, "sqlite")


def upgrade() -> None:
    op.create_table(
        "serie",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("fonte_id", sa.String(64), sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("codigo", sa.String(64), nullable=False),
        sa.Column("nome", sa.Text, nullable=False),
        sa.Column("unidade", sa.Text, nullable=False),
        sa.Column("pais", sa.String(3)),
        sa.Column("frequencia", sa.String(16), nullable=False),
        sa.Column("medida", sa.String(32), nullable=False),
        sa.Column("ativa", sa.Boolean, nullable=False),
    )
    op.create_table(
        "observacao",
        sa.Column("id", Id, primary_key=True, autoincrement=True),
        sa.Column("serie_id", sa.String(64), sa.ForeignKey("serie.id"), nullable=False),
        sa.Column("data", sa.Date, nullable=False),
        sa.Column("valor", sa.Float, nullable=False),
        sa.Column("rodada_id", Id, sa.ForeignKey("rodada.id")),
        sa.Column("conhecido_em", sa.DateTime, nullable=False),
    )
    op.create_index("ix_observacao_serie", "observacao", ["serie_id", "data", "conhecido_em"])


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
