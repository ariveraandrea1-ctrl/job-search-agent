"""Modelos de base de datos (tablas), definidos con SQLAlchemy.

"Document": un CV que un usuario mando por Telegram, con el texto que
le sacamos. "InterviewAnswer": la respuesta que el usuario da a la
pregunta de entrevista posterior al CV. "InterviewQuestion": la lista de
preguntas de la entrevista. "ConversationState": en que paso
de la conversacion va cada usuario (la usa n8n directamente).
"Profile": el perfil que la IA arma a partir del CV (JSON completo).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Document(Base):
    """Un archivo (CV) recibido por Telegram, con su texto extraido."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ConversationState(Base):
    """En que paso de la conversacion va cada usuario de Telegram.

    No tiene endpoint en profile-api: n8n la lee y escribe con el nodo
    Postgres. Esta aqui para que el modelo refleje el esquema real.
    """

    __tablename__ = "conversation_state"

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
