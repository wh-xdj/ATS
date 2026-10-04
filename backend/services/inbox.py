"""Local persisted inbox events; no external delivery."""
import uuid
from models import Notification
from utils.datetime_utils import beijing_now


def notify(db, user_id, event_key, event_type, title, content, related_id):
    identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, 'ats-inbox:'+event_key+':'+str(user_id)))
    if not db.get(Notification, identifier):
        db.add(Notification(id=identifier, user_id=str(user_id), type=event_type, title=title,
            content=content, related_id=related_id, created_at=beijing_now()))
