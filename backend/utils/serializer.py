"""数据序列化工具"""
from typing import Any, Dict, List
from datetime import datetime, date
from sqlalchemy.ext.declarative import DeclarativeMeta


def to_camel_case(snake_str: str) -> str:
    """将snake_case转换为camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """将camelCase转换为snake_case"""
    result = [camel_str[0].lower()]
    for char in camel_str[1:]:
        if char.isupper():
            result.append('_')
            result.append(char.lower())
        else:
            result.append(char)
    return ''.join(result)


def serialize_model(model: Any, camel_case: bool = True) -> Dict[str, Any]:
    """
    序列化SQLAlchemy模型为字典
    
    Args:
        model: SQLAlchemy模型实例
        camel_case: 是否转换为驼峰命名，默认True
    
    Returns:
        序列化后的字典
    """
    if model is None:
        return None
    
    result = {}
    
    try:
        # 获取模型的所有列
        for column in model.__table__.columns:
            try:
                value = getattr(model, column.name, None)
                
                # 处理None值
                if value is None:
                    result[to_camel_case(column.name) if camel_case else column.name] = None
                    continue
                
                # 处理datetime类型
                if isinstance(value, datetime):
                    value = value.isoformat()
                # 处理date类型
                elif isinstance(value, date):
                    value = value.isoformat()
                # JSON字段已经是字典或列表，直接使用
                # UUID类型转换为字符串
                elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, list, dict)):
                    value = str(value)
                
                # 转换字段名
                key = to_camel_case(column.name) if camel_case else column.name
                result[key] = value
            except Exception as e:
                # 如果某个字段序列化失败，记录错误但继续处理其他字段
                print(f"Warning: Failed to serialize field {column.name}: {e}")
                continue
    except Exception as e:
        print(f"Error serializing model: {e}")
        raise
    
    return result


def serialize_list(models: List[Any], camel_case: bool = True) -> List[Dict[str, Any]]:
    """
    序列化模型列表
    
    Args:
        models: SQLAlchemy模型列表
        camel_case: 是否转换为驼峰命名，默认True
    
    Returns:
        序列化后的字典列表
    """
    return [serialize_model(model, camel_case) for model in models]


def deserialize_dict(data: Dict[str, Any], snake_case: bool = True) -> Dict[str, Any]:
    """
    反序列化字典（将前端的camelCase转换为snake_case）
    
    Args:
        data: 输入字典
        snake_case: 是否转换为下划线命名，默认True
    
    Returns:
        转换后的字典
    """
    if not snake_case:
        return data
    
    result = {}
    for key, value in data.items():
        new_key = to_snake_case(key)
        result[new_key] = value
    
    return result

