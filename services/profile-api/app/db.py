"""Conexion a la base de datos (PostgreSQL) usando SQLAlchemy.

DATABASE_URL viene de una variable de entorno (definida en
docker-compose.local.yml), asi que este archivo no tiene contraseñas
ni datos sensibles escritos a mano.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre una sesion de base de datos por
    request y la cierra automaticamente al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
