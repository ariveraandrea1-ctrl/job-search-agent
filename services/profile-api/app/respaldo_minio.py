"""Respaldo y prueba de restauración de MinIO (lo usan los scripts de scripts/).

Se corre DENTRO del contenedor de profile-api (que tiene acceso a MinIO):

    python -m app.respaldo_minio exportar > respaldo.tar     # todos los archivos + manifiesto
    python -m app.respaldo_minio importar BUCKET < respaldo.tar
    python -m app.respaldo_minio resumen [BUCKET]            # "objetos N" y "huella X"
    python -m app.respaldo_minio borrar BUCKET               # borra un bucket de prueba

"huella" es un SHA-256 de la lista ordenada (ruta, sha256 de cada archivo):
si coincide entre el original y el restaurado, son exactamente los mismos
archivos con exactamente el mismo contenido.
"""
import hashlib
import io
import json
import sys
import tarfile

from app import almacen

MANIFIESTO = "manifiesto.json"


def _objetos(cliente, b: str):
    if not cliente.bucket_exists(b):
        return []
    return sorted(o.object_name for o in cliente.list_objects(b, recursive=True))


def _leer(cliente, b: str, clave: str) -> bytes:
    r = cliente.get_object(b, clave)
    try:
        return r.read()
    finally:
        r.close()
        r.release_conn()


def huella_total(pares: list[tuple[str, str]]) -> str:
    return hashlib.sha256("\n".join(f"{k} {h}" for k, h in sorted(pares)).encode()).hexdigest()


def resumen(b: str) -> dict:
    cliente = almacen._cliente()
    pares = [(k, almacen.huella(_leer(cliente, b, k))) for k in _objetos(cliente, b)]
    return {"objetos": len(pares), "huella": huella_total(pares)}


def exportar(salida) -> None:
    cliente, b = almacen._cliente(), almacen.bucket()
    manifiesto = {}
    with tarfile.open(fileobj=salida, mode="w|") as tar:
        for clave in _objetos(cliente, b):
            datos = _leer(cliente, b, clave)
            manifiesto[clave] = almacen.huella(datos)
            info = tarfile.TarInfo(name="objetos/" + clave)
            info.size = len(datos)
            tar.addfile(info, io.BytesIO(datos))
        m = json.dumps(manifiesto, indent=1).encode()
        info = tarfile.TarInfo(name=MANIFIESTO)
        info.size = len(m)
        tar.addfile(info, io.BytesIO(m))


def importar(entrada, b: str) -> int:
    n = 0
    with tarfile.open(fileobj=entrada, mode="r|") as tar:
        for miembro in tar:
            if miembro.isfile() and miembro.name.startswith("objetos/"):
                datos = tar.extractfile(miembro).read()
                almacen.guardar(miembro.name[len("objetos/"):], datos, miembro.name, nombre_bucket=b)
                n += 1
    return n


def borrar(b: str) -> None:
    cliente = almacen._cliente()
    for clave in _objetos(cliente, b):
        cliente.remove_object(b, clave)
    if cliente.bucket_exists(b):
        cliente.remove_bucket(b)


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else ""
    if accion == "exportar":
        exportar(sys.stdout.buffer)
    elif accion == "importar":
        print(importar(sys.stdin.buffer, sys.argv[2]))
    elif accion == "resumen":
        r = resumen(sys.argv[2] if len(sys.argv) > 2 else almacen.bucket())
        print(f"objetos {r['objetos']}\nhuella {r['huella']}")
    elif accion == "borrar":
        borrar(sys.argv[2])
    else:
        sys.exit(__doc__)
