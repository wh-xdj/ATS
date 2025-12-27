# ATS Agent 节点

自动化测试管理平台（ATS）的分布式执行节点，类似于Jenkins的Slave节点。

## 功能特性

- ✅ Token认证连接云端平台
- ✅ WebSocket实时双向通信
- ✅ 自动创建工作目录
- ✅ 每5秒上报系统状态（CPU、内存、磁盘等）
- ✅ 接收和执行测试任务
- ✅ 实时上报任务日志和结果
- ✅ 自动重连机制
- ✅ 跨平台支持（Linux、Windows、macOS）

## 环境要求

- Python 3.8 或更高版本
- 网络连接（能够访问云端平台的WebSocket服务器）
- 工作目录的读写权限

## 安装

### 使用 uv（推荐）

[uv](https://github.com/astral-sh/uv) 是一个快速的 Python 包管理器和项目管理工具。

1. **安装 uv**（如果尚未安装）：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **安装依赖并运行**：

```bash
# 进入agent目录
cd agent

# 安装依赖
uv sync

# 运行Agent（从agent目录运行）
uv run python agent.py --token "your-token" --server-url "ws://localhost:8000/ws/agent"
```

或者从项目根目录运行：

```bash
# 从ATS项目根目录运行
uv run python -m agent.agent --token "your-token" --server-url "ws://localhost:8000/ws/agent"
```

### 使用 pip（传统方式）

1. **安装依赖包**：

```bash
cd agent
pip install -r requirements.txt
```

或者使用pip3：

```bash
pip3 install -r requirements.txt
```

2. **运行Agent**：

从agent目录运行（需要设置PYTHONPATH）：

```bash
cd agent
PYTHONPATH=. python agent.py --token "your-token" --server-url "ws://localhost:8000/ws/agent"
```

或者从项目根目录运行：

```bash
# 从ATS项目根目录
python -m agent.agent --token "your-token" --server-url "ws://localhost:8000/ws/agent"
```

## 使用方法

### 基本使用

```bash
python agent.py --token "your-auth-token-here" --server-url "ws://localhost:8000/ws/agent"
```

### 命令行参数

- `--token` (必需): 认证Token，用于连接云端平台
- `--server-url`: WebSocket服务器地址，如 `ws://localhost:8000/ws/agent`
- `--log-level`: 日志级别，可选值：DEBUG、INFO、WARNING、ERROR（默认：INFO）
- `--config`: 配置文件路径（YAML格式）
- `--work-dir`: 工作目录路径（可选，优先使用云端下发的）

### 配置文件

支持YAML格式的配置文件，示例：

```yaml
server:
  url: "ws://localhost:8000/ws/agent"

logging:
  level: "INFO"
  max_size: 10485760  # 10MB
  backup_count: 5

task:
  max_concurrent: 1  # 最大并发任务数
  timeout: 3600      # 默认超时时间（秒）
  cleanup:
    keep_tasks: 10   # 保留最近N个任务
    keep_days: 7     # 保留最近N天的任务

monitor:
  interval: 5        # 监控上报间隔（秒）
```

使用配置文件：

```bash
python agent.py --token "your-token" --config config.yaml
```

## 运行模式

### 前台运行

直接运行脚本，输出日志到控制台：

```bash
python agent.py --token "your-token" --server-url "ws://your-server:8000/ws/agent"
```

### 后台运行

#### Linux/macOS

使用 `nohup`：

```bash
nohup python agent.py --token "your-token" --server-url "ws://your-server:8000/ws/agent" > agent.out 2>&1 &
```

使用 `screen`：

```bash
screen -S agent
python agent.py --token "your-token" --server-url "ws://your-server:8000/ws/agent"
# 按 Ctrl+A 然后按 D 退出screen
```

使用 `tmux`：

```bash
tmux new -s agent
python agent.py --token "your-token" --server-url "ws://your-server:8000/ws/agent"
# 按 Ctrl+B 然后按 D 退出tmux
```

#### Windows

使用 `start` 命令：

```cmd
start /B python agent.py --token "your-token" --server-url "ws://your-server:8000/ws/agent"
```

## 目录结构

Agent运行后会在工作目录下创建以下结构：

```
{work_dir}/
├── tasks/              # 任务执行目录
│   ├── {task_id_1}/    # 每个任务独立目录
│   ├── {task_id_2}/
│   └── ...
├── logs/               # 日志目录
│   ├── agent.log       # Agent运行日志
│   └── tasks/          # 任务日志
│       ├── {task_id_1}.log
│       └── ...
└── cache/              # 缓存目录（可选）
```

## 获取Token

Token需要从云端平台获取，通常与Environment（测试环境）关联。请联系平台管理员获取Agent认证Token。

## 故障排查

### 连接失败

1. 检查网络连接是否正常
2. 检查WebSocket服务器地址是否正确
3. 检查Token是否有效
4. 检查防火墙设置

### 认证失败

1. 确认Token是否正确
2. 确认Token是否已过期
3. 联系平台管理员检查Token状态

### 工作目录创建失败

1. 检查目录路径是否正确
2. 检查是否有写权限
3. 检查磁盘空间是否充足

## 日志

Agent的日志保存在 `{work_dir}/logs/agent.log`，任务日志保存在 `{work_dir}/logs/tasks/{task_id}.log`。

日志文件会自动轮转，单个文件最大10MB，保留5个历史文件。

## 安全建议

1. **Token安全**：
   - 妥善保管Token，不要泄露
   - 定期轮换Token
   - 不要在公共场合暴露Token

2. **通信安全**：
   - 生产环境使用WSS（WebSocket Secure）加密连接
   - 验证服务器证书

3. **执行安全**：
   - 使用非root用户运行Agent
   - 限制任务执行权限
   - 定期检查任务执行日志

## 开发

### 项目结构

```
agent/
├── __init__.py          # 包初始化
├── agent.py             # 主程序入口
├── config.py            # 配置管理
├── websocket_client.py  # WebSocket客户端
├── system_monitor.py    # 系统监控
├── task_executor.py     # 任务执行器
├── logger.py            # 日志管理
├── utils.py             # 工具函数
├── requirements.txt     # 依赖包
└── README.md            # 使用说明
```

## 许可证

与ATS项目保持一致。

## 支持

如有问题或建议，请联系项目维护者。

