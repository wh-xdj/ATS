#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成随机测试用例脚本"""
import sys
import os
import random
import uuid
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.test_case import TestCase
from models.project import Project
from models.user import User
from core.security import get_password_hash
from utils.datetime_utils import beijing_now


# 测试用例类型
TEST_CASE_TYPES = ["functional", "interface", "ui", "performance", "security"]

# 优先级
PRIORITIES = ["P0", "P1", "P2", "P3"]

# 状态
STATUSES = ["not_executed", "passed", "failed", "blocked", "skipped"]

# 标签
TAGS_OPTIONS = [
    ["回归", "冒烟"],
    ["回归"],
    ["冒烟"],
    ["性能"],
    ["安全"],
    ["接口"],
    ["UI"],
    ["功能"],
    ["自动化"],
    ["手动"],
]

# 测试用例名称模板
CASE_NAME_TEMPLATES = [
    "验证{feature}的{action}功能",
    "测试{feature}的{action}操作",
    "检查{feature}的{action}行为",
    "验证{feature}在{condition}下的表现",
    "测试{feature}的{action}流程",
    "验证{feature}的{action}异常处理",
    "测试{feature}的{action}边界条件",
    "验证{feature}的{action}性能",
]

# 功能特性
FEATURES = [
    "用户登录", "用户注册", "密码重置", "个人信息", "订单管理",
    "购物车", "支付流程", "商品搜索", "商品详情", "评论系统",
    "消息通知", "文件上传", "数据导出", "权限管理", "角色配置",
    "系统设置", "日志查看", "报表生成", "数据统计", "接口调用",
]

# 操作
ACTIONS = [
    "创建", "删除", "修改", "查询", "提交", "取消", "确认", "重置",
    "上传", "下载", "导出", "导入", "搜索", "筛选", "排序", "分页",
]

# 条件
CONDITIONS = [
    "正常情况", "异常情况", "边界条件", "并发场景", "大数据量",
    "网络延迟", "超时情况", "权限不足", "数据为空", "数据异常",
]

# 前置条件模板
PRECONDITION_TEMPLATES = [
    "用户已登录系统",
    "用户具有相应权限",
    "测试数据已准备完成",
    "系统环境已配置",
    "相关依赖服务已启动",
    "数据库连接正常",
    "网络连接正常",
    None,  # 有些用例可能没有前置条件
]

# 测试步骤动作模板
STEP_ACTIONS = [
    "打开{page}页面",
    "输入{field}为{value}",
    "点击{button}按钮",
    "选择{option}选项",
    "验证{element}显示{content}",
    "等待{time}秒",
    "检查{field}的值",
    "提交表单",
    "刷新页面",
    "返回上一页",
]

# 测试步骤预期结果模板
STEP_EXPECTED = [
    "页面正常显示",
    "{field}显示为{value}",
    "操作成功提示",
    "数据保存成功",
    "页面跳转到{page}",
    "错误提示信息正确",
    "数据验证通过",
    "操作被正确执行",
    "状态更新为{status}",
    "返回正确的数据",
]


def generate_random_steps(count: int = None) -> list:
    """生成随机测试步骤"""
    if count is None:
        count = random.randint(3, 8)
    
    steps = []
    pages = ["首页", "登录页", "列表页", "详情页", "设置页"]
    fields = ["用户名", "密码", "邮箱", "手机号", "地址", "金额", "数量"]
    values = ["test", "123456", "test@example.com", "13800138000", "测试地址", "100", "5"]
    buttons = ["提交", "确认", "取消", "保存", "删除", "搜索", "重置"]
    options = ["选项1", "选项2", "选项A", "选项B"]
    
    for i in range(count):
        action_template = random.choice(STEP_ACTIONS)
        expected_template = random.choice(STEP_EXPECTED)
        
        # 替换模板中的占位符
        action = action_template
        if "{page}" in action:
            action = action.replace("{page}", random.choice(pages))
        if "{field}" in action:
            action = action.replace("{field}", random.choice(fields))
        if "{value}" in action:
            action = action.replace("{value}", random.choice(values))
        if "{button}" in action:
            action = action.replace("{button}", random.choice(buttons))
        if "{option}" in action:
            action = action.replace("{option}", random.choice(options))
        if "{time}" in action:
            action = action.replace("{time}", str(random.randint(1, 5)))
        
        expected = expected_template
        if "{field}" in expected:
            expected = expected.replace("{field}", random.choice(fields))
        if "{value}" in expected:
            expected = expected.replace("{value}", random.choice(values))
        if "{page}" in expected:
            expected = expected.replace("{page}", random.choice(pages))
        if "{status}" in expected:
            expected = expected.replace("{status}", random.choice(["成功", "失败", "进行中"]))
        
        steps.append({
            "step": i + 1,
            "action": action,
            "expected": expected
        })
    
    return steps


def generate_test_case_name() -> str:
    """生成随机测试用例名称"""
    template = random.choice(CASE_NAME_TEMPLATES)
    feature = random.choice(FEATURES)
    action = random.choice(ACTIONS)
    condition = random.choice(CONDITIONS)
    
    name = template.replace("{feature}", feature).replace("{action}", action)
    if "{condition}" in name:
        name = name.replace("{condition}", condition)
    
    return name


def get_or_create_user(db) -> User:
    """获取或创建用户"""
    user = db.query(User).first()
    if not user:
        # 创建默认用户
        user = User(
            id=str(uuid.uuid4()),
            username="test_user",
            email="test@example.com",
            password_hash=get_password_hash("test123456"),
            full_name="测试用户",
            status=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ 创建默认用户: {user.username} (ID: {user.id})")
    else:
        print(f"✅ 使用现有用户: {user.username} (ID: {user.id})")
    
    return user


def get_or_create_project(db, user_id: str) -> Project:
    """获取或创建项目"""
    project = db.query(Project).first()
    if not project:
        # 创建默认项目
        project = Project(
            id=str(uuid.uuid4()),
            name="测试项目",
            description="用于生成测试用例的默认项目",
            owner_id=user_id,
            created_by=user_id,
            status="active"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"✅ 创建默认项目: {project.name} (ID: {project.id})")
    else:
        print(f"✅ 使用现有项目: {project.name} (ID: {project.id})")
    
    return project


def generate_case_code(db) -> str:
    """生成唯一的用例编号"""
    from utils.datetime_utils import beijing_now
    timestamp = int(beijing_now().timestamp() * 1000) % 1000000
    case_code = f"{timestamp:06d}"
    
    # 确保case_code唯一
    while db.query(TestCase).filter(TestCase.case_code == case_code).first():
        timestamp = (timestamp + 1) % 1000000
        case_code = f"{timestamp:06d}"
    
    return case_code


def generate_test_cases(count: int = 100):
    """生成指定数量的随机测试用例"""
    db = SessionLocal()
    
    try:
        # 获取或创建用户和项目
        user = get_or_create_user(db)
        project = get_or_create_project(db, user.id)
        
        print(f"\n开始生成 {count} 条测试用例...")
        
        created_count = 0
        for i in range(count):
            try:
                # 生成随机数据
                case_code = generate_case_code(db)
                name = generate_test_case_name()
                case_type = random.choice(TEST_CASE_TYPES)
                priority = random.choice(PRIORITIES)
                precondition = random.choice(PRECONDITION_TEMPLATES)
                steps = generate_random_steps()
                tags = random.choice(TAGS_OPTIONS)
                is_automated = random.choice([True, False])
                
                # 创建测试用例
                test_case = TestCase(
                    id=str(uuid.uuid4()),
                    project_id=project.id,
                    module_id=None,  # 暂时不关联模块
                    case_code=case_code,
                    name=name,
                    type=case_type,
                    priority=priority,
                    precondition=precondition,
                    steps=steps,
                    requirement_ref=f"REQ-{random.randint(1000, 9999)}" if random.random() > 0.5 else None,
                    module_path=None,
                    level=priority,
                    executor_id=None,
                    tags=tags,
                    status="not_executed",
                    is_automated=is_automated,
                    created_by=user.id,
                    updated_by=user.id
                )
                
                db.add(test_case)
                created_count += 1
                
                if (i + 1) % 10 == 0:
                    db.commit()  # 每10条提交一次
                    print(f"  已生成 {i + 1}/{count} 条测试用例...")
            
            except Exception as e:
                print(f"  ⚠️  生成第 {i + 1} 条测试用例时出错: {e}")
                db.rollback()
                continue
        
        # 提交剩余的
        db.commit()
        
        print(f"\n✅ 成功生成 {created_count} 条测试用例！")
        print(f"   项目: {project.name}")
        print(f"   用户: {user.username}")
        
    except Exception as e:
        print(f"❌ 生成测试用例时出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成随机测试用例")
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="要生成的测试用例数量（默认: 100）"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("测试用例生成工具")
    print("=" * 60)
    
    generate_test_cases(args.count)
    
    print("=" * 60)
    print("完成！")
    print("=" * 60)
