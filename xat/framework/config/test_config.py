# -*- coding: utf-8 -*-
"""测试配置管理"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class TestConfig(BaseSettings):
    """测试配置类"""
    
    # 测试数据库配置
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    USE_TEST_DATABASE: bool = True
    
    # 测试环境配置
    TEST_ENVIRONMENT: str = "test"
    TEST_API_V1_STR: str = "/api/v1"
    
    # 测试用户配置
    TEST_ADMIN_USERNAME: str = "test_admin"
    TEST_ADMIN_PASSWORD: str = "test_password"
    TEST_ADMIN_EMAIL: str = "test_admin@example.com"
    
    # JWT测试配置
    TEST_JWT_SECRET_KEY: str = "test-secret-key-for-testing-only"
    TEST_JWT_ALGORITHM: str = "HS256"
    
    # 测试客户端配置
    TEST_CLIENT_BASE_URL: str = "http://testserver"
    
    # 日志配置
    TEST_LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    TEST_LOG_TO_FILE: bool = True  # 是否输出到文件
    TEST_LOG_FILE_DIR: str = "logs"  # 日志文件目录
    TEST_LOG_FILE_PREFIX: str = "test"  # 日志文件前缀
    
    # 覆盖率配置
    COVERAGE_ENABLED: bool = True
    COVERAGE_FAIL_UNDER: int = 80
    
    # Allure配置
    ALLURE_ENABLED: bool = True
    ALLURE_RESULTS_DIR: str = "allure-results"
    ALLURE_REPORT_DIR: str = "allure-report"
    
    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局测试配置实例
_test_config: Optional[TestConfig] = None


def get_test_config() -> TestConfig:
    """获取测试配置实例（单例模式）"""
    global _test_config
    if _test_config is None:
        _test_config = TestConfig()
    return _test_config

