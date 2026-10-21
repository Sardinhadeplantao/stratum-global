"""Grupo de cada série: moedas, juros, bolsas, commodities, cripto (decisão 0013).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("serie", sa.Column("grupo", sa.String(16)))


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
