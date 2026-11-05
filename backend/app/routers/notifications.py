from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_user_unrestricted as get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(user: models.User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    items = (db.query(models.Notification).filter_by(user_id=user.id)
             .order_by(models.Notification.created_at.desc()).limit(50).all())
    unread = sum(1 for n in items if not n.is_read)
    return {"unread": unread, "items": [schemas.NotificationOut.model_validate(n) for n in items]}


@router.post("/read-all")
def read_all(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(models.Notification).filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.commit()
    return {"ok": True}
