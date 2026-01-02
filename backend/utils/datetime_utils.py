"""时间工具函数"""
from datetime import datetime, timezone, timedelta

# 北京时间（UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """获取当前北京时间（UTC+8）"""
    return datetime.now(BEIJING_TZ)


def beijing_utcnow() -> datetime:
    """获取当前北京时间（UTC+8），兼容utcnow的命名"""
    return beijing_now()


def to_beijing_time(dt: datetime) -> datetime:
    """将datetime转换为北京时间"""
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是UTC时间
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BEIJING_TZ)


def beijing_now_iso() -> str:
    """获取当前北京时间的ISO格式字符串"""
    return beijing_now().isoformat()

