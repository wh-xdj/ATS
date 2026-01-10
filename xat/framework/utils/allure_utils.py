# -*- coding: utf-8 -*-
"""Allure工具函数"""
from typing import Optional, Any
from pathlib import Path


def attach_screenshot(file_path: str, name: str = "截图") -> None:
    """
    附加截图到Allure报告
    
    Args:
        file_path: 截图文件路径
        name: 附件名称
    """
    try:
        import allure
        
        if Path(file_path).exists():
            with open(file_path, "rb") as f:
                allure.attach(
                    f.read(),
                    name=name,
                    attachment_type=allure.attachment_type.PNG
                )
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 附加截图失败: {e}")


def attach_text(text: str, name: str = "文本") -> None:
    """
    附加文本到Allure报告
    
    Args:
        text: 文本内容
        name: 附件名称
    """
    try:
        import allure
        
        allure.attach(
            text,
            name=name,
            attachment_type=allure.attachment_type.TEXT
        )
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 附加文本失败: {e}")


def attach_json(data: Any, name: str = "JSON数据") -> None:
    """
    附加JSON数据到Allure报告
    
    Args:
        data: JSON数据（字典或可序列化对象）
        name: 附件名称
    """
    try:
        import allure
        import json
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        allure.attach(
            json_str,
            name=name,
            attachment_type=allure.attachment_type.JSON
        )
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 附加JSON失败: {e}")


def attach_html(html: str, name: str = "HTML") -> None:
    """
    附加HTML到Allure报告
    
    Args:
        html: HTML内容
        name: 附件名称
    """
    try:
        import allure
        
        allure.attach(
            html,
            name=name,
            attachment_type=allure.attachment_type.HTML
        )
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 附加HTML失败: {e}")


def step(step_name: str):
    """
    Allure步骤装饰器
    
    Args:
        step_name: 步骤名称
    
    Usage:
        @step("执行登录操作")
        def login():
            pass
    """
    try:
        import allure
        return allure.step(step_name)
    except ImportError:
        # 如果Allure未安装，返回一个空装饰器
        def decorator(func):
            return func
        return decorator


def label(name: str, value: str) -> None:
    """
    添加标签到Allure报告
    
    Args:
        name: 标签名称
        value: 标签值
    """
    try:
        import allure
        allure.dynamic.label(name, value)
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 添加标签失败: {e}")


def description(text: str) -> None:
    """
    添加描述到Allure报告
    
    Args:
        text: 描述文本
    """
    try:
        import allure
        allure.dynamic.description(text)
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 添加描述失败: {e}")


def severity(severity_level: str) -> None:
    """
    设置测试严重级别
    
    Args:
        severity_level: 严重级别 (blocker, critical, normal, minor, trivial)
    """
    try:
        import allure
        from allure_commons.types import Severity
        
        severity_map = {
            "blocker": Severity.BLOCKER,
            "critical": Severity.CRITICAL,
            "normal": Severity.NORMAL,
            "minor": Severity.MINOR,
            "trivial": Severity.TRIVIAL,
        }
        
        severity_obj = severity_map.get(severity_level.lower(), Severity.NORMAL)
        allure.dynamic.severity(severity_obj)
    except ImportError:
        pass
    except Exception as e:
        from framework.logger import get_logger
        get_logger().warning(f"[Allure] 设置严重级别失败: {e}")

