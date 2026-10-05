"""Modelos de base de datos (tablas), definidos con SQLAlchemy.

"Document": un CV que un usuario mando por Telegram, con el texto que
le sacamos. "InterviewAnswer": la respuesta que el usuario da a la
pregunta de entrevista posterior al CV. "InterviewQuestion": la lista de
preguntas de la entrevista. "ConversationState": en que paso
de la conversacion va cada usuario (la usa n8n directamente).
"Profile": el perfil que la IA arma a partir del CV (JSON completo).
"Opportunity": una vacante o proyecto freelance encontrado por el radar.
"Tenant", "User", "Invitation": multiusuario (migración 0011). Todas las
tablas funcionales llevan tenant_id (por ahora un solo tenant, el principal).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

TENANT_PRINCIPAL = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _tenant_id():
    """Columna tenant_id: la pone Postgres (tenant principal por defecto)."""
    return mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False,
        server_default=text(f"'{TENANT_PRINCIPAL}'::uuid"),
    )


class Tenant(Base):
    """Organización/espacio. En el Proyecto 1 hay uno solo ("principal")."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class User(Base):
    """Quién puede usar el bot. rol: admin | usuario. estado: activo | pausado."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("rol IN ('admin', 'usuario')", name="ck_users_rol"),
        CheckConstraint("estado IN ('activo', 'pausado')", name="ck_users_estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    nombre: Mapped[str | None] = mapped_column(Text, nullable=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="usuario")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")
    invited_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Invitation(Base):
    """Código de invitación de un solo uso (lo crea la admin con /invitar)."""

    __tablename__ = "invitations"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(Base):
    """Un archivo (CV) recibido por Telegram, con su texto extraido."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class InterviewAnswer(Base):
    """Respuesta del usuario a la pregunta de entrevista posterior al CV."""

    __tablename__ = "interview_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # Tema de la pregunta respondida (ej. "salario"). NULL en respuestas
    # guardadas antes de que existieran los temas.
    topic: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ConversationState(Base):
    """En que paso de la conversacion va cada usuario de Telegram.

    No tiene endpoint en profile-api: n8n la lee y escribe con el nodo
    Postgres. Esta aqui para que el modelo refleje el esquema real.
    """

    __tablename__ = "conversation_state"

    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    step: Mapped[str] = mapped_column(Text, nullable=False)
    # En que pregunta de interview_questions va (None si no esta en entrevista).
    question_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class InterviewQuestion(Base):
    """Una pregunta de la entrevista. El orden lo da "position" (1, 2, 3...).

    No tiene endpoint en profile-api: n8n la lee con el nodo Postgres.
    """

    __tablename__ = "interview_questions"

    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    # Tema de la pregunta (ej. "salario"). Coincide con las claves que la
    # IA devuelve en "faltantes" (prompt v4): solo se pregunta lo que falta.
    topic: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


class Profile(Base):
    """El perfil que la IA arma a partir de un CV.

    "data" guarda el JSON completo tal como lo devolvio la IA (contacto,
    experiencia, proyectos, habilidades, faltantes...). Cada CV nuevo
    agrega una fila; el perfil vigente es la fila mas reciente del usuario.
    """

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Opportunity(Base):
    """Una vacante (empleo) o proyecto (freelance) que encontró el radar.

    "dedup_key" es la huella de la vacante: con ella la misma oportunidad
    nunca se guarda dos veces para el mismo usuario.
    """

    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "telegram_user_id", "dedup_key", name="uq_opportunities_tenant_user_dedup"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_id()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="nueva")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    score_prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dedup_key: Mapped[str] = mapped_column(Text, nullable=False)
    # Número corto para Telegram (#12). Lo pone Postgres (secuencia, migración 0010).
    numero: Mapped[int] = mapped_column(
        BigInteger, server_default=text("nextval('opportunities_numero_seq')"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
