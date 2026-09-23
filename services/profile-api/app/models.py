"""Modelos de base de datos (tablas), definidos con SQLAlchemy.

"Document": un CV que un usuario mando por Telegram, con el texto que
le sacamos. "InterviewAnswer": la respuesta que el usuario da a la
pregunta de entrevista posterior al CV. "ConversationState": en que paso
de la conversacion va cada usuario (la usa n8n directamente). Mas
adelante se agregaran las tablas de perfil, etc.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
