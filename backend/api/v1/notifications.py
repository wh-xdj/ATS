from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, Notification
from api.deps import get_current_user
from schemas.common import APIResponse
from utils.serializer import serialize_list

router = APIRouter()


@router.get('')
async def get_notifications(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=1000),
    is_read: bool | None = Query(None, alias='isRead'), type: str | None = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Notification).filter(Notification.user_id == str(current_user.id))
    if is_read is not None: query = query.filter(Notification.is_read == is_read)
    if type: query = query.filter(Notification.type == type)
    total=query.count(); rows=query.order_by(Notification.created_at.desc()).offset((page-1)*size).limit(size).all()
    return APIResponse(status='success', message='获取成功', data=dict(items=serialize_list(rows, camel_case=True),
        total=total,page=page,size=size,pages=(total+size-1)//size,hasNext=page*size<total,hasPrev=page>1))


@router.put('/read-all')
async def read_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == str(current_user.id)).update({'is_read': True})
    db.commit()
    return APIResponse(status='success', message='已读')


@router.put('/{notification_id}/read')
async def read_notification(notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item=db.query(Notification).filter(Notification.id==notification_id,Notification.user_id==str(current_user.id)).first()
    if not item: raise HTTPException(404,'通知不存在')
    item.is_read=True;db.commit()
    return APIResponse(status='success',message='已读')
