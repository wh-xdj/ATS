# -*- coding: utf-8 -*-
"""测试模型导入和关系映射"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_import():
    """测试模型导入"""
    try:
        from models import TestCase, Module, Project
        print("✅ 模型导入成功")
        return True
    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_relationships():
    """测试模型关系"""
    try:
        from models import TestCase, Module
        
        # 检查 TestCase.module relationship
        assert hasattr(TestCase, 'module'), "TestCase 缺少 module 关系"
        print("✅ TestCase.module 关系存在")
        
        # 检查 Module.test_cases relationship
        assert hasattr(Module, 'test_cases'), "Module 缺少 test_cases 关系"
        print("✅ Module.test_cases 关系存在")
        
        return True
    except Exception as e:
        print(f"❌ 模型关系检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        from database import engine, SessionLocal
        from sqlalchemy import text
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"⚠️  数据库连接失败（可能是数据库未启动）: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("测试用例模块 Bug 修复验证")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. 测试模型导入...")
    results.append(test_model_import())
    print()
    
    if results[0]:
        print("2. 测试模型关系...")
        results.append(test_model_relationships())
        print()
        
        print("3. 测试数据库连接...")
        results.append(test_database_connection())
        print()
    
    print("=" * 60)
    if all(results):
        print("✅ 所有测试通过！Bug 修复成功！")
    elif results[0] and results[1]:
        print("⚠️  模型修复成功，数据库连接失败（请确保 MySQL 已启动）")
    else:
        print("❌ 测试失败，请检查错误信息")
    print("=" * 60)

