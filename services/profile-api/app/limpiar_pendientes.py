"""Limpieza única de vacantes viejas sin puntaje (después de BUG-28).

Las vacantes que entraron ANTES del filtro de palabras (BUG-28) siguen en la
fila de puntaje y gastan cuota de IA en vacantes que no sirven. Este comando
les pasa el MISMO filtro (busqueda.filtrar_por_palabras, con las palabras de
cada usuario) y marca como "descartada" las que no tienen ninguna palabra.
No borra nada.

Uso (dentro del contenedor profile-api):
  python -m app.limpiar_pendientes            # solo muestra, no cambia nada
  python -m app.limpiar_pendientes --aplicar  # marca las que no sirven
"""
import sys

from sqlalchemy import select

from app.busqueda import titulo_coincide
from app.db import SessionLocal
from app.models import Opportunity, User


def main(aplicar: bool) -> None:
    db = SessionLocal()
    try:
        total_quedan = total_descartar = 0
        for user in db.scalars(select(User).order_by(User.telegram_user_id)).all():
            palabras = list(user.palabras_clave or [])
            pendientes = db.scalars(
                select(Opportunity)
                .where(Opportunity.telegram_user_id == user.telegram_user_id,
                       Opportunity.scored_at.is_(None),
                       Opportunity.status != "descartada")
                .order_by(Opportunity.created_at)
            ).all()
            if not pendientes:
                continue
            print(f"\n=== Usuario {user.telegram_user_id}: {len(pendientes)} sin puntaje")
            if not palabras:
                print("  (sin palabras clave: no se toca nada)")
                continue
            print(f"  Palabras: {', '.join(palabras)}")
            quedan = [v for v in pendientes if titulo_coincide(v.title, palabras)]
            descartar = [v for v in pendientes if not titulo_coincide(v.title, palabras)]
            print(f"\n  QUEDAN ({len(quedan)}):")
            for v in quedan:
                print(f"    #{v.numero} {v.title}")
            print(f"\n  SE DESCARTAN ({len(descartar)}):")
            for v in descartar:
                print(f"    #{v.numero} {v.title}")
                if aplicar:
                    v.status = "descartada"
            total_quedan += len(quedan)
            total_descartar += len(descartar)
        if aplicar:
            db.commit()
            print(f"\nAPLICADO: {total_descartar} descartadas, {total_quedan} siguen pendientes.")
        else:
            print(f"\nSOLO VISTA PREVIA: se descartarían {total_descartar}, quedarían {total_quedan}.")
            print("Para aplicar: python -m app.limpiar_pendientes --aplicar")
    finally:
        db.close()


if __name__ == "__main__":
    main("--aplicar" in sys.argv[1:])
