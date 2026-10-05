"""documents: referencia al archivo original del CV en MinIO

storage_key = ruta del archivo en el bucket
  (tenants/{tenant}/users/{usuario}/cv/original/...),
sha256 = huella del archivo, size_bytes = tamaño.
Nulas en los CV guardados antes (de esos no se guardó el archivo).

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("storage_key", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("sha256", sa.String(64), nullable=True))
    op.add_column("documents", sa.Column("size_bytes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "size_bytes")
    op.drop_column("documents", "sha256")
    op.drop_column("documents", "storage_key")
