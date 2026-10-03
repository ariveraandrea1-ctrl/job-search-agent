"""agrega a opportunities las columnas del puntaje con IA (Semana 6)

- analysis: JSON con lo que devolvió la IA ya validado (inglés exigido,
  nivel, razones a favor/en contra, señales de alerta, resumen, reglas
  fijas aplicadas).
- scored_at: cuándo se puntuó (NULL = falta puntuar).
- score_provider / score_prompt_version: qué IA y qué versión del prompt
  (para comparar y re-puntuar si cambia el prompt).
"score" (0-100) ya existía desde 0008.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("opportunities", sa.Column("analysis", postgresql.JSONB(), nullable=True))
    op.add_column("opportunities", sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("opportunities", sa.Column("score_provider", sa.String(length=50), nullable=True))
    op.add_column("opportunities", sa.Column("score_prompt_version", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("opportunities", "score_prompt_version")
    op.drop_column("opportunities", "score_provider")
    op.drop_column("opportunities", "scored_at")
    op.drop_column("opportunities", "analysis")
