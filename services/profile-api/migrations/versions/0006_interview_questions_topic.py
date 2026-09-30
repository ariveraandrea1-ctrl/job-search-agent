"""agrega "topic" a interview_questions y completa las preguntas

Entrevista adaptativa: cada pregunta tiene un tema (topic). La IA devuelve
en "faltantes" los temas que NO están en el CV, y n8n solo hace las
preguntas cuyo tema está en esa lista.

Temas (deben coincidir EXACTO con las claves del prompt v4):
rol_buscado, modalidad, ciudad, salario, disponibilidad, ingles,
contrato, certificaciones.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Columna nueva, primero sin obligar (las filas viejas aún no tienen tema).
    op.add_column(
        "interview_questions",
        sa.Column("topic", sa.String(length=50), nullable=True),
    )

    # 2. Tema de las 3 preguntas que ya existían.
    op.execute("UPDATE interview_questions SET topic = 'rol_buscado' WHERE position = 1")
    op.execute("UPDATE interview_questions SET topic = 'modalidad' WHERE position = 2")
    op.execute("UPDATE interview_questions SET topic = 'ciudad' WHERE position = 3")

    # 3. Preguntas nuevas para los demás temas.
    preguntas = sa.table(
        "interview_questions",
        sa.column("position", sa.Integer()),
        sa.column("question", sa.Text()),
        sa.column("topic", sa.String()),
    )
    op.bulk_insert(
        preguntas,
        [
            {
                "position": 4,
                "topic": "salario",
                "question": "¿Cuál es tu aspiración salarial? Puedes darme un rango y la moneda.",
            },
            {
                "position": 5,
                "topic": "disponibilidad",
                "question": "¿Desde cuándo podrías empezar a trabajar?",
            },
            {
                "position": 6,
                "topic": "ingles",
                "question": "¿Cuál es tu nivel de inglés para trabajar (lectura, escritura, conversación)?",
            },
            {
                "position": 7,
                "topic": "contrato",
                "question": "¿Qué tipo de contrato buscas: término indefinido, término fijo, prestación de servicios o freelance?",
            },
            {
                "position": 8,
                "topic": "certificaciones",
                "question": "¿Tienes certificaciones formales (por ejemplo ISTQB)? Si sí, ¿cuáles?",
            },
        ],
    )

    # 4. Ahora sí: todas tienen tema, y ningún tema se repite.
    op.alter_column("interview_questions", "topic", nullable=False)
    op.create_unique_constraint(
        "uq_interview_questions_topic", "interview_questions", ["topic"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_interview_questions_topic", "interview_questions")
    op.execute("DELETE FROM interview_questions WHERE position BETWEEN 4 AND 8")
    op.drop_column("interview_questions", "topic")
