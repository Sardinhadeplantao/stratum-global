"""Traduções dos títulos para o português (decisão 0010).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

Id = sa.BigInteger().with_variant(sa.Integer, "sqlite")


def upgrade() -> None:
    op.create_table(
        "traducao",
        sa.Column("documento_id", Id, sa.ForeignKey("documento.id"), primary_key=True),
        sa.Column("campo", sa.String(16), primary_key=True),
        sa.Column("idioma", sa.String(8), primary_key=True),
        sa.Column("texto", sa.Text, nullable=False),
        sa.Column("modelo", sa.String(64), nullable=False),
        sa.Column("conhecido_em", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
