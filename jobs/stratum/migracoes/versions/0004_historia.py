"""Histórias: a ligação de cada notícia com a sua história (decisão 0009).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

Id = sa.BigInteger().with_variant(sa.Integer, "sqlite")


def upgrade() -> None:
    op.create_table(
        "historia_documento",
        sa.Column("documento_id", Id, sa.ForeignKey("documento.id"), primary_key=True),
        sa.Column("historia_id", Id, sa.ForeignKey("documento.id"), nullable=False),
        sa.Column("conhecido_em", sa.DateTime, nullable=False),
        sa.Column("regra", sa.String(32), nullable=False),
    )
    op.create_index("ix_historia_documento_historia", "historia_documento", ["historia_id"])


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
