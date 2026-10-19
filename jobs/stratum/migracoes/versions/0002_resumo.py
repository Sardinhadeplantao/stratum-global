"""Resumos enviados ao Telegram, para nunca mandar o mesmo duas vezes (decisão 0005).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

Id = sa.BigInteger().with_variant(sa.Integer, "sqlite")


def upgrade() -> None:
    op.create_table(
        "resumo",
        sa.Column("id", Id, primary_key=True, autoincrement=True),
        sa.Column("horario", sa.DateTime, nullable=False, unique=True),
        sa.Column("enviado_em", sa.DateTime, nullable=False),
        sa.Column("situacao", sa.String(16), nullable=False),
        sa.Column("texto", sa.Text, nullable=False),
    )


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
