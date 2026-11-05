from sqlalchemy.orm import Session

from . import models

STATUS_LABELS = {
    "recue": "reçue", "preselectionnee": "présélectionnée", "entretien": "retenue pour un entretien",
    "acceptee": "acceptée", "refusee": "refusée",
}


def notify(db: Session, user_id: int, message: str) -> None:
    db.add(models.Notification(user_id=user_id, message=message))
