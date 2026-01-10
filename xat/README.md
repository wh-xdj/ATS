# XAT - Pytest自动化测试框架

XAT (eXtensible Automated Testing) 是一个基于pytest的自动化测试框架，采用面向对象的设计，实现了hooks和fixtures的完全解耦封装。

## 目录结构

```
xat/
├── framework/
│   ├── __init__.py              # Framework主入口
│   ├── config/                   # 测试配置模块
│   │   ├── __init__.py
│   │   └── test_config.py        # 测试配置管理
│   ├── hooks/                    # Hook模块
│   │   ├── __init__.py           # Hook模块入口，自动注册所有hooks
│   │   ├── base.py               # Hook基类定义
│   │   ├── registry.py           # Hook注册管理器
│   │   └── impl/                 # Hook实现类
│   │       ├── __init__.py
│   │       ├── config_hooks.py   # 配置类hooks
│   │       ├── session_hooks.py  # Session类hooks
│   │       └── collection_hooks.py # Collection类hooks
│   ├── fixtures/                 # Fixtures模块
│   │   ├── __init__.py
│   │   ├── database.py           # 数据库相关fixtures
│   │   ├── client.py             # FastAPI客户端fixtures
│   │   ├── auth.py               # 认证相关fixtures
│   │   └── data.py               # 测试数据fixtures
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       └── helpers.py            # 测试辅助函数
└── conftest.py                   # Pytest配置文件（仅导入）
```

## 特性

### 1. 基于类的Hook设计

- **抽象基类**: 使用`BaseHook`定义统一的Hook接口
- **类型安全**: 通过抽象基类确保类型安全
- **易于扩展**: 继承基类即可创建自定义Hook
- **统一管理**: 通过`HookRegistry`集中管理所有Hooks

### 2. 解耦的Fixtures

- **模块化设计**: 按功能划分fixtures模块
- **数据库隔离**: 使用SQLite内存数据库或事务回滚确保测试隔离
- **依赖覆盖**: 使用FastAPI的`dependency_overrides`覆盖数据库依赖
- **可复用性**: 提供丰富的测试数据和工具函数

### 3. 配置管理

- **Pydantic Settings**: 使用Pydantic进行配置管理
- **环境变量支持**: 支持通过`.env.test`文件配置
- **单例模式**: 全局配置实例，确保一致性

## 快速开始

### 1. 安装依赖

```bash
# 在backend目录下安装测试依赖
cd backend
pip install pytest pytest-asyncio pytest-cov httpx pydantic-settings
```

### 2. 使用框架

在测试文件中直接使用fixtures：

```python
# tests/test_example.py
import pytest
from framework.utils import assert_response_success


@pytest.mark.asyncio
async def test_example_with_async_client(async_client, admin_auth_headers):
    """使用异步客户端测试"""
    response = await async_client.get(
        "/api/v1/projects",
        headers=admin_auth_headers
    )
    data = assert_response_success(response, expected_status=200)
    assert "items" in data


def test_example_with_sync_client(test_client, auth_headers):
    """使用同步客户端测试"""
    response = test_client.get(
        "/api/v1/projects",
        headers=auth_headers
    )
    data = assert_response_success(response, expected_status=200)
    assert "items" in data


@pytest.mark.database
def test_example_with_database(db_session, sample_project):
    """使用数据库测试"""
    from models import Project
    
    project = db_session.query(Project).filter(
        Project.id == sample_project["id"]
    ).first()
    
    assert project is not None
    assert project.name == "测试项目"
```

## 核心组件

### Hooks

#### 配置类Hooks

- **PytestConfigureHook**: 基础pytest配置
- **MarkerRegistrationHook**: 注册自定义标记（slow, integration, unit等）
- **AsyncioConfigHook**: 配置pytest-asyncio

#### Session类Hooks

- **SessionStartHookImpl**: Session开始逻辑
- **TestEnvironmentSetupHook**: 测试环境设置
- **SessionFinishHookImpl**: Session结束和清理

#### Collection类Hooks

- **CollectionModifyItemsHook**: 基础collection处理
- **TestMarkerHook**: 自动为测试添加标记
- **TestSorterHook**: 测试排序

### Fixtures

#### 数据库Fixtures

- `db_engine`: Session级别，创建测试数据库引擎
- `db_session`: Function级别，数据库会话（自动回滚）
- `test_db`: Function级别，数据库会话别名
- `test_database`: Session级别，数据库引擎别名

#### 客户端Fixtures

- `test_client`: 同步TestClient（用于同步测试）
- `async_client`: 异步AsyncClient（用于异步测试）

#### 认证Fixtures

- `test_user`: 创建测试用户
- `admin_user`: 创建管理员用户
- `auth_headers`: 普通用户认证headers
- `admin_auth_headers`: 管理员认证headers

#### 数据Fixtures

- `sample_project`: 示例项目数据
- `sample_module`: 示例模块数据
- `sample_test_case`: 示例测试用例数据

### 工具函数

- `assert_response_success()`: 断言响应成功
- `assert_response_error()`: 断言响应错误
- `create_test_user()`: 创建测试用户
- `create_test_project()`: 创建测试项目

## 自定义Hook

### 创建自定义Hook

```python
# framework/hooks/impl/custom_hooks.py
from framework.hooks.base import ConfigHook
import pytest


class CustomConfigHook(ConfigHook):
    """自定义配置Hook示例"""
    
    def execute(self, config: pytest.Config) -> None:
        """执行自定义配置逻辑"""
        if not self.enabled:
            return
        
        # 你的自定义逻辑
        print(f"[Custom Hook] {self.name}: 执行自定义配置")
```

### 注册自定义Hook

```python
# 在conftest.py中
from framework.hooks import get_hook_registry
from framework.hooks.impl.custom_hooks import CustomConfigHook

# 获取注册器
registry = get_hook_registry()

# 注册自定义hook
registry.register(CustomConfigHook())

# 或者禁用某个hook
# registry.get_hooks("config")[0].disable()
```

## 配置

### 环境变量

创建`.env.test`文件：

```env
# 测试数据库配置
TEST_DATABASE_URL=sqlite:///./test.db
USE_TEST_DATABASE=true

# 测试环境配置
TEST_ENVIRONMENT=test
TEST_API_V1_STR=/api/v1

# 测试用户配置
TEST_ADMIN_USERNAME=test_admin
TEST_ADMIN_PASSWORD=test_password
TEST_ADMIN_EMAIL=test_admin@example.com

# JWT测试配置
TEST_JWT_SECRET_KEY=test-secret-key-for-testing-only
TEST_JWT_ALGORITHM=HS256

# 日志配置
TEST_LOG_LEVEL=DEBUG
TEST_LOG_TO_FILE=false
```

### 测试标记

框架自动注册以下测试标记：

- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.database`: 需要数据库的测试
- `@pytest.mark.auth`: 需要认证的测试
- `@pytest.mark.api`: API测试
- `@pytest.mark.websocket`: WebSocket测试

使用示例：

```bash
# 只运行单元测试
pytest -m unit

# 跳过慢速测试
pytest -m "not slow"

# 只运行集成测试
pytest -m integration
```

## 运行测试

### 基本用法

```bash
# 运行所有测试
pytest

# 运行指定目录的测试
pytest tests/

# 运行指定文件
pytest tests/test_example.py

# 运行指定测试函数
pytest tests/test_example.py::test_example_with_async_client
```

### 带覆盖率的测试

```bash
# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term-missing

# 查看HTML报告
open htmlcov/index.html
```

### 并行运行测试

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 并行运行测试
pytest -n auto
```

## 最佳实践

### 1. 测试隔离

每个测试函数使用独立的数据库事务，测试结束后自动回滚，确保测试之间数据隔离。

### 2. 使用标记

合理使用测试标记，便于分类管理和选择性运行：

```python
@pytest.mark.integration
@pytest.mark.slow
async def test_complex_integration(async_client):
    """复杂的集成测试"""
    pass
```

### 3. 使用辅助函数

使用框架提供的辅助函数简化测试代码：

```python
from framework.utils import assert_response_success

def test_api_endpoint(test_client, auth_headers):
    response = test_client.get("/api/v1/projects", headers=auth_headers)
    data = assert_response_success(response, expected_status=200, expected_keys=["items"])
    assert len(data["items"]) > 0
```

### 4. 自定义Hook

根据项目需求创建自定义Hook，扩展框架功能。

## 架构设计

### Hook系统架构

```
HookRegistry (单例)
    ├── ConfigHooks
    │   ├── PytestConfigureHook
    │   ├── MarkerRegistrationHook
    │   └── AsyncioConfigHook
    ├── SessionStartHooks
    │   ├── SessionStartHookImpl
    │   └── TestEnvironmentSetupHook
    ├── SessionFinishHooks
    │   └── SessionFinishHookImpl
    └── CollectionHooks
        ├── CollectionModifyItemsHook
        ├── TestMarkerHook
        └── TestSorterHook
```

### Fixture依赖关系

```
db_engine (session)
    └── db_session (function)
        ├── test_db (alias)
        ├── test_client
        ├── async_client
        ├── test_user
        ├── admin_user
        └── sample_project
            ├── sample_module
            └── sample_test_case
```

## 故障排除

### 1. 导入错误

确保`xat`目录在Python路径中，或者在`conftest.py`中添加路径：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### 2. 数据库连接错误

检查`TEST_DATABASE_URL`配置，确保数据库服务已启动。

### 3. Hook未执行

检查hook是否已注册，使用`get_hook_registry().get_hooks("config")`查看已注册的hooks。

## 贡献

欢迎提交Issue和Pull Request来改进框架。

## Allure集成

框架已集成Allure测试报告工具，可以生成美观的HTML测试报告。

### 安装Allure

框架已自动安装Allure依赖，但需要安装Allure命令行工具：

```bash
# macOS
brew install allure

# Linux (使用npm)
npm install -g allure-commandline

# Windows (使用Scoop)
scoop install allure
```

### 运行测试并生成Allure报告

```bash
# 运行测试（自动生成allure-results）
pytest tests/ --alluredir=allure-results

# 生成HTML报告
allure generate allure-results -o allure-report --clean

# 打开报告（自动启动本地服务器）
allure open allure-report
```

### 使用Allure功能

在测试代码中使用Allure功能：

```python
import pytest
from framework.utils import step, attach_text, attach_json, severity, label

@pytest.mark.api
def test_with_allure(test_client):
    """使用Allure功能的测试示例"""
    # 设置严重级别
    severity("critical")
    
    # 添加标签
    label("component", "api")
    label("team", "backend")
    
    # 使用步骤
    with step("准备测试数据"):
        data = {"username": "test", "password": "test123"}
        attach_json(data, "测试数据")
    
    with step("发送请求"):
        response = test_client.post("/api/v1/login", json=data)
        attach_text(f"响应状态码: {response.status_code}", "响应信息")
    
    with step("验证结果"):
        assert response.status_code == 200
        result = response.json()
        attach_json(result, "响应数据")
```

### Allure配置

在`.env.test`文件中配置Allure：

```env
# Allure配置
ALLURE_ENABLED=true
ALLURE_RESULTS_DIR=allure-results
ALLURE_REPORT_DIR=allure-report
```

### Allure工具函数

框架提供了以下Allure工具函数：

- `attach_screenshot(file_path, name)`: 附加截图
- `attach_text(text, name)`: 附加文本
- `attach_json(data, name)`: 附加JSON数据
- `attach_html(html, name)`: 附加HTML
- `step(step_name)`: 步骤装饰器
- `label(name, value)`: 添加标签
- `description(text)`: 添加描述
- `severity(level)`: 设置严重级别

## 许可证

MIT License

