"""Ficha de cada fonte: nível, tipo de controle e quem controla (decisão 0008).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("fonte") as t:
        t.add_column(sa.Column("nivel", sa.Integer))
        t.add_column(sa.Column("controle", sa.String(16)))
        t.add_column(sa.Column("controlador", sa.String(64)))
        t.add_column(sa.Column("controlador_nome", sa.Text))
        t.add_column(sa.Column("controlador_fonte", sa.Text))


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
