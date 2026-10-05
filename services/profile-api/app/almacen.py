"""Almacén de archivos (MinIO, compatible con S3).

La especificación: "PostgreSQL guarda metadatos, hashes y referencias;
MinIO conserva archivos". Estructura de carpetas (sección 7.1):

    tenants/{tenant_id}/users/{telegram_user_id}/cv/original/...

Las funciones puras (huella, nombre_seguro, clave_cv) se prueban con
pytest; las que hablan con MinIO usan las variables del .env
(MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_BUCKET).
"""
import hashlib
import io
import os
import re
import unicodedata

TIPOS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def huella(contenido: bytes) -> str:
    """SHA-256 del archivo: misma huella = mismo archivo, byte por byte."""
    return hashlib.sha256(contenido).hexdigest()


def nombre_seguro(nombre: str | None) -> str:
    """'Mi CV (final).pdf' → 'mi-cv-final.pdf' (sin tildes, espacios ni símbolos)."""
    nombre = unicodedata.normalize("NFD", nombre or "archivo")
    nombre = "".join(c for c in nombre if unicodedata.category(c) != "Mn").lower()
    base, punto, ext = nombre.rpartition(".")
    if not punto:
        base, ext = nombre, ""
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:60] or "archivo"
    ext = re.sub(r"[^a-z0-9]", "", ext)[:5]
    return f"{base}.{ext}" if ext else base


def clave_cv(tenant_id, telegram_user_id: int, nombre: str | None, sha256: str) -> str:
    """Ruta del CV original dentro del bucket (la huella evita choques de nombre)."""
    return (f"tenants/{tenant_id}/users/{telegram_user_id}/cv/original/"
            f"{sha256[:16]}-{nombre_seguro(nombre)}")


def _cliente():
    from minio import Minio  # import aquí: los tests de funciones puras no lo necesitan
    return Minio(os.environ.get("MINIO_ENDPOINT", "minio:9000"),
                 access_key=os.environ["MINIO_ROOT_USER"],
                 secret_key=os.environ["MINIO_ROOT_PASSWORD"],
                 secure=False)


def bucket() -> str:
    return os.environ.get("MINIO_BUCKET", "job-search-agent")


def guardar(clave: str, contenido: bytes, nombre: str | None = None, nombre_bucket: str | None = None) -> None:
    """Sube el archivo a MinIO (crea el bucket si no existe)."""
    cliente, b = _cliente(), nombre_bucket or bucket()
    if not cliente.bucket_exists(b):
        cliente.make_bucket(b)
    ext = os.path.splitext(nombre or "")[1].lower()
    cliente.put_object(b, clave, io.BytesIO(contenido), len(contenido),
                       content_type=TIPOS.get(ext, "application/octet-stream"))
