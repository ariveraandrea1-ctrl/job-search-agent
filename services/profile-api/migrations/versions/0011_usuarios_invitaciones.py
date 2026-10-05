"""multiusuario: tenants, users, invitations y tenant_id en las tablas funcionales

- tenants: por ahora uno solo ("principal", id fijo TENANT_PRINCIPAL).
- users: quién puede usar el bot. rol = admin | usuario,
  estado = activo | pausado (/pausar: no recibe avisos del radar).
  La administradora se crea aquí desde ADMIN_TELEGRAM_USER_ID (.env).
- invitations: códigos de un solo uso que crea la admin con /invitar.
- tenant_id (con el tenant principal por defecto) en documents,
  interview_answers, conversation_state, profiles y opportunities, como
  pide la especificación ("todas las tablas funcionales incluirán
  tenant_id"). interview_questions NO: es un catálogo compartido.
- La restricción única de opportunities pasa a (tenant, usuario, huella).
- Los que ya usaban el bot (tienen datos) quedan registrados como usuarios.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-05
"""
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

TENANT_PRINCIPAL = "00000000-0000-0000-0000-000000000001"
TABLAS = ["documents", "interview_answers", "conversation_state", "profiles", "opportunities"]


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute(f"INSERT INTO tenants (id, nombre) VALUES ('{TENANT_PRINCIPAL}', 'principal')")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False,
                  server_default=sa.text(f"'{TENANT_PRINCIPAL}'::uuid")),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("nombre", sa.Text(), nullable=True),
        sa.Column("rol", sa.String(20), nullable=False, server_default="usuario"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="activo"),
        sa.Column("invited_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rol IN ('admin', 'usuario')", name="ck_users_rol"),
        sa.CheckConstraint("estado IN ('activo', 'pausado')", name="ck_users_estado"),
    )

    op.create_table(
        "invitations",
        sa.Column("code", sa.String(20), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False,
                  server_default=sa.text(f"'{TENANT_PRINCIPAL}'::uuid")),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_by", sa.BigInteger(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    for tabla in TABLAS:
        op.add_column(tabla, sa.Column(
            "tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False,
            server_default=sa.text(f"'{TENANT_PRINCIPAL}'::uuid")))

    op.drop_constraint("uq_opportunities_user_dedup", "opportunities", type_="unique")
    op.create_unique_constraint("uq_opportunities_tenant_user_dedup", "opportunities",
                                ["tenant_id", "telegram_user_id", "dedup_key"])

    # Administradora (desde .env) y quienes ya tenían datos.
    admin = os.environ.get("ADMIN_TELEGRAM_USER_ID", "").strip()
    if admin.isdigit():
        op.execute(f"INSERT INTO users (telegram_user_id, rol) VALUES ({admin}, 'admin') "
                   "ON CONFLICT (telegram_user_id) DO UPDATE SET rol = 'admin'")
    op.execute(
        "INSERT INTO users (telegram_user_id) "
        "SELECT DISTINCT telegram_user_id FROM ("
        "  SELECT telegram_user_id FROM documents UNION SELECT telegram_user_id FROM profiles"
        "  UNION SELECT telegram_user_id FROM opportunities) t "
        "ON CONFLICT (telegram_user_id) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_constraint("uq_opportunities_tenant_user_dedup", "opportunities", type_="unique")
    op.create_unique_constraint("uq_opportunities_user_dedup", "opportunities",
                                ["telegram_user_id", "dedup_key"])
    for tabla in TABLAS:
        op.drop_column(tabla, "tenant_id")
    op.drop_table("invitations")
    op.drop_table("users")
    op.drop_table("tenants")
