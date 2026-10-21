"""Contrato futuro de cada dia e eventos com lugar no mapa (decisão 0014).

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

Id = sa.BigInteger().with_variant(sa.Integer, "sqlite")


def upgrade() -> None:
    op.create_table(
        "contrato_futuro",
        sa.Column("serie_id", sa.String(64), sa.ForeignKey("serie.id"), primary_key=True),
        sa.Column("data", sa.Date, primary_key=True),
        sa.Column("contrato", sa.String(32), primary_key=True),
        sa.Column("conhecido_em", sa.DateTime, nullable=False),
    )
    op.create_table(
        "evento_local",
        sa.Column("id", Id, primary_key=True, autoincrement=True),
        sa.Column("fonte_id", sa.String(64), sa.ForeignKey("fonte.id"), nullable=False),
        sa.Column("ext_id", sa.String(64), nullable=False),
        sa.Column("versao", sa.String(64), nullable=False),
        sa.Column("titulo", sa.Text, nullable=False),
        sa.Column("url", sa.Text),
        sa.Column("magnitude", sa.Float),
        sa.Column("lat", sa.Float, nullable=False),
        sa.Column("lon", sa.Float, nullable=False),
        sa.Column("ocorreu_em", sa.DateTime, nullable=False),
        sa.Column("conhecido_em", sa.DateTime, nullable=False),
        sa.Column("rodada_id", Id, sa.ForeignKey("rodada.id")),
    )
    op.create_index("ux_evento_local_versao", "evento_local", ["fonte_id", "ext_id", "versao"], unique=True)
    op.create_index("ix_evento_local_ocorreu", "evento_local", ["ocorreu_em"])


def downgrade() -> None:
    raise NotImplementedError("Nada é apagado: corrija com uma migração nova.")
