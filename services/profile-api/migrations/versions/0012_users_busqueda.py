"""búsqueda por usuario: palabras clave y categorías de Get on Board

- users.palabras_clave: lista JSON de palabras (ej. ["qa", "tester"]).
- users.categorias: lista JSON de categorías de Get on Board
  (ej. ["sysadmin-devops-qa"]).
Vacías al principio: se sugieren desde el rol buscado y los cargos del CV
la primera vez que se necesitan (app/busqueda.py), y el usuario las cambia
con /preferencias. La administradora arranca con las palabras de la regla
fija de QA que se usaba antes, para que su radar no cambie.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

PALABRAS_QA = ('["qa", "tester", "testing", "pruebas", "calidad", "quality", '
               '"sdet", "automatizacion", "monitoreo", "validacion"]')


def upgrade() -> None:
    op.add_column("users", sa.Column("palabras_clave", JSONB(), nullable=False,
                                     server_default=sa.text("'[]'::jsonb")))
    op.add_column("users", sa.Column("categorias", JSONB(), nullable=False,
                                     server_default=sa.text("'[]'::jsonb")))
    op.execute(f"UPDATE users SET palabras_clave = '{PALABRAS_QA}'::jsonb, "
               "categorias = '[\"sysadmin-devops-qa\"]'::jsonb WHERE rol = 'admin'")


def downgrade() -> None:
    op.drop_column("users", "categorias")
    op.drop_column("users", "palabras_clave")
