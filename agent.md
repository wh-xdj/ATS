# Agent节点需求文档

## 文档信息

| 项目名称 | 自动化测试管理平台（ATS）Agent节点 |
|---------|-------------------------------------------|
| 文档版本 | v1.0 |
| 编写日期 | 2025-12-14 |
| 文档状态 | 待评审 |
| 技术栈 | Python (脚本) |

---

## 1. 项目概述

### 1.1 项目背景

Agent节点是自动化测试管理平台的分布式执行节点，类似于Jenkins的Slave节点。Agent负责在远程机器上执行测试任务，与云端平台通过WebSocket建立实时连接，接收任务指令并上报执行结果和系统状态。

### 1.2 项目目标

1. **分布式执行**：支持在多个远程节点上并行执行测试任务，提高测试执行效率
2. **实时通信**：通过WebSocket实现与云端平台的实时双向通信
3. **状态监控**：定期上报节点系统资源信息（CPU、内存、磁盘等），便于云端监控节点状态
4. **任务执行**：接收云端下发的测试任务，在本地工作目录执行并上报结果
5. **自动化管理**：自动创建工作目录，管理任务执行环境

### 1.3 核心功能

- **连接管理**：通过Token认证连接云端平台
- **工作目录管理**：根据云端配置自动创建和管理工作目录
- **系统监控**：定期收集和上报系统资源信息
- **任务执行**：接收和执行测试任务
- **日志上报**：实时上报任务执行日志和结果

### 1.4 与云端交互

- **连接方式**：WebSocket长连接
- **认证方式**：Token认证（启动时传入）
- **通信协议**：JSON格式消息
- **心跳机制**：每5秒上报系统状态
- **任务接收**：通过WebSocket接收任务指令
- **结果上报**：通过WebSocket上报任务执行结果

---

## 2. 功能需求

### 2.1 启动与认证

#### 2.1.1 启动方式

- **脚本形式**：Agent以独立脚本形式运行，支持命令行启动
- **启动参数**：
  - `--token`：必需参数，用于连接云端平台的认证Token
  - `--server-url`：可选参数，云端平台WebSocket服务器地址（默认从配置文件读取）
  - `--log-level`：可选参数，日志级别（DEBUG/INFO/WARNING/ERROR，默认INFO）
  - `--config`：可选参数，配置文件路径

**启动示例**：
```bash
python agent.py --token "your-auth-token-here" --server-url "ws://localhost:8000/ws/agent"
```

#### 2.1.2 Token认证

- **认证流程**：
  1. Agent启动时使用Token连接云端WebSocket服务器
  2. 连接时在WebSocket握手阶段传递Token（通过URL参数或首部）
  3. 云端验证Token有效性，验证通过后建立连接
  4. 如果Token无效或过期，连接失败，Agent退出并输出错误信息

- **Token格式**：
  - Token为字符串格式，由云端平台生成和分发
  - Token与Environment（测试环境）一一对应
  - Token应包含足够的信息用于标识对应的Environment

- **认证失败处理**：
  - 输出错误日志
  - 退出程序，返回非零退出码
  - 提供清晰的错误提示信息

### 2.2 WebSocket连接管理

#### 2.2.1 连接建立

- **连接地址**：`ws://{server_host}:{server_port}/ws/agent?token={token}`
- **连接时机**：Agent启动时立即尝试连接
- **连接超时**：连接超时时间设置为30秒
- **连接重试**：连接失败时，按照指数退避策略重试（初始间隔1秒，最大间隔60秒）

#### 2.2.2 连接保持

- **心跳机制**：Agent每5秒向云端发送一次心跳消息（包含系统状态信息）
- **连接检测**：检测WebSocket连接状态，如果连接断开，自动重连
- **重连策略**：
  - 检测到连接断开后，等待3秒后开始重连
  - 使用指数退避策略，最大重连间隔60秒
  - 重连时使用相同的Token
  - 重连成功后恢复所有功能

#### 2.2.3 消息格式

**Agent发送给云端的消息格式**：

1. **连接认证消息**（连接建立时）：
```json
{
  "type": "auth",
  "token": "agent-token",
  "agent_info": {
    "version": "1.0.0",
    "platform": "linux",
    "python_version": "3.9.0"
  }
}
```

2. **心跳消息**（每5秒）：
```json
{
  "type": "heartbeat",
  "timestamp": "2025-12-14T10:30:00Z",
  "system_info": {
    "cpu": {
      "usage_percent": 45.2,
      "cores": 8,
      "model": "Intel Core i7-9700K",
      "frequency": "3.6GHz"
    },
    "memory": {
      "total": 16384,
      "used": 8192,
      "free": 8192,
      "usage_percent": 50.0,
      "unit": "MB"
    },
    "disk": {
      "total": 500000,
      "used": 200000,
      "free": 300000,
      "usage_percent": 40.0,
      "unit": "MB"
    },
    "network": {
      "ip": "192.168.1.100",
      "hostname": "agent-node-01"
    },
    "os": {
      "type": "Linux",
      "version": "Ubuntu 20.04.3 LTS",
      "kernel": "5.4.0-74-generic"
    }
  }
}
```

3. **任务执行结果消息**：
```json
{
  "type": "task_result",
  "task_id": "task-uuid",
  "status": "success|failed|error",
  "exit_code": 0,
  "output": "任务执行输出...",
  "error": "错误信息（如果有）",
  "duration": 120.5,
  "timestamp": "2025-12-14T10:35:00Z"
}
```

4. **任务日志消息**（实时）：
```json
{
  "type": "task_log",
  "task_id": "task-uuid",
  "level": "info|warning|error",
  "message": "日志内容",
  "timestamp": "2025-12-14T10:35:15Z"
}
```

**云端发送给Agent的消息格式**：

1. **连接确认消息**：
```json
{
  "type": "auth_success",
  "environment_id": "env-uuid",
  "work_dir": "/home/agent/workspace",
  "server_time": "2025-12-14T10:30:00Z"
}
```

2. **任务执行指令**：
```json
{
  "type": "task",
  "task_id": "task-uuid",
  "command": "python test_runner.py --case-id case-123",
  "work_dir": "/home/agent/workspace/task-uuid",
  "env_vars": {
    "PYTHONPATH": "/opt/tests",
    "TEST_ENV": "staging"
  },
  "timeout": 3600
}
```

3. **任务取消指令**：
```json
{
  "type": "cancel_task",
  "task_id": "task-uuid"
}
```

### 2.3 工作目录管理

#### 2.3.1 工作目录创建

- **目录来源**：云端在连接确认消息中传递`work_dir`参数，指定Agent的工作目录路径
- **自动创建**：
  - Agent接收到`work_dir`后，检查目录是否存在
  - 如果目录不存在，自动创建（包括所有父目录）
  - 如果目录已存在，检查是否有写权限
  - 如果无权限，输出错误并退出

- **目录结构**：
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

#### 2.3.2 任务目录管理

- **任务目录**：每个任务在`{work_dir}/tasks/{task_id}/`下创建独立目录
- **目录清理**：
  - 任务执行完成后，保留任务目录和日志（用于调试）
  - 可配置自动清理策略（如：保留最近N个任务，或保留最近N天的任务）
  - 清理策略可通过配置文件或云端指令设置

### 2.4 系统监控

#### 2.4.1 监控指标

Agent需要收集以下系统信息：

1. **CPU信息**：
   - CPU使用率（百分比）
   - CPU核心数
   - CPU型号
   - CPU频率

2. **内存信息**：
   - 总内存（MB）
   - 已用内存（MB）
   - 可用内存（MB）
   - 内存使用率（百分比）

3. **磁盘信息**：
   - 总磁盘空间（MB）
   - 已用磁盘空间（MB）
   - 可用磁盘空间（MB）
   - 磁盘使用率（百分比）
   - 工作目录所在磁盘的信息

4. **网络信息**：
   - 本机IP地址
   - 主机名

5. **操作系统信息**：
   - 操作系统类型（Linux/Windows/macOS）
   - 操作系统版本
   - 内核版本

#### 2.4.2 监控频率

- **上报间隔**：每5秒向云端上报一次系统状态
- **数据采集**：在每次上报前采集最新的系统信息
- **异常处理**：如果采集某个指标失败，使用上一次的值或标记为"未知"

#### 2.4.3 监控实现

- **跨平台支持**：使用Python的`psutil`库实现跨平台的系统监控
- **性能优化**：系统信息采集应快速完成，避免影响Agent性能
- **错误容错**：监控功能失败不应导致Agent崩溃

### 2.5 任务执行

#### 2.5.1 任务接收

- **接收方式**：通过WebSocket接收云端下发的任务指令
- **任务验证**：验证任务消息格式和必需字段
- **任务队列**：支持接收多个任务，按顺序执行（或支持并发执行，可配置）

#### 2.5.2 任务执行

- **执行环境**：
  - 在任务指定的工作目录中执行（如果任务消息中指定了`work_dir`，使用该目录；否则使用默认任务目录）
  - 设置环境变量（从任务消息的`env_vars`字段读取）
  - 切换到任务工作目录

- **执行方式**：
  - 使用子进程执行命令
  - 实时捕获标准输出和标准错误
  - 支持超时控制（从任务消息的`timeout`字段读取，单位：秒）

- **日志上报**：
  - 实时将任务输出通过WebSocket上报给云端
  - 日志消息包含任务ID、日志级别、内容和时间戳
  - 支持标准输出和标准错误的分别上报

#### 2.5.3 任务结果上报

- **执行完成**：任务执行完成后，收集以下信息：
  - 退出码（exit code）
  - 执行时长
  - 标准输出内容
  - 标准错误内容（如果有）
  - 任务状态（success/failed/error/timeout）

- **结果格式**：按照2.2.3节定义的消息格式上报

#### 2.5.4 任务取消

- **取消机制**：接收云端的任务取消指令
- **取消处理**：
  - 如果任务正在执行，终止任务进程
  - 清理任务资源
  - 上报任务取消结果

### 2.6 日志管理

#### 2.6.1 Agent运行日志

- **日志文件**：`{work_dir}/logs/agent.log`
- **日志级别**：支持DEBUG/INFO/WARNING/ERROR级别
- **日志格式**：包含时间戳、日志级别、模块名、消息内容
- **日志轮转**：支持日志文件大小限制和轮转（如：单个文件最大10MB，保留5个历史文件）

#### 2.6.2 任务执行日志

- **日志文件**：每个任务的日志保存在`{work_dir}/logs/tasks/{task_id}.log`
- **日志内容**：包含任务的所有输出（标准输出和标准错误）
- **日志保留**：根据配置的清理策略保留或删除

---

## 3. 技术实现

### 3.1 技术栈

- **编程语言**：Python 3.7+
- **WebSocket客户端**：`websockets`库或`websocket-client`库
- **系统监控**：`psutil`库
- **命令行解析**：`argparse`库
- **日志处理**：`logging`库
- **JSON处理**：`json`库（标准库）
- **进程管理**：`subprocess`库（标准库）
- **文件操作**：`os`、`pathlib`库（标准库）

### 3.2 项目结构

```
agent/
├── agent.py              # 主程序入口
├── config.py             # 配置管理
├── websocket_client.py   # WebSocket客户端
├── system_monitor.py     # 系统监控
├── task_executor.py      # 任务执行器
├── logger.py             # 日志管理
├── utils.py              # 工具函数
├── requirements.txt      # 依赖包
├── config.yaml           # 配置文件（可选）
└── README.md             # 使用说明
```

### 3.3 核心模块设计

#### 3.3.1 WebSocket客户端模块

**职责**：
- 管理与云端平台的WebSocket连接
- 处理消息的发送和接收
- 实现连接重连机制
- 处理消息序列化和反序列化

**关键方法**：
- `connect(token, server_url)`: 建立连接
- `send_message(message)`: 发送消息
- `receive_message()`: 接收消息（异步）
- `reconnect()`: 重连
- `close()`: 关闭连接

#### 3.3.2 系统监控模块

**职责**：
- 收集系统资源信息
- 格式化监控数据
- 提供系统信息查询接口

**关键方法**：
- `get_cpu_info()`: 获取CPU信息
- `get_memory_info()`: 获取内存信息
- `get_disk_info(work_dir)`: 获取磁盘信息
- `get_network_info()`: 获取网络信息
- `get_os_info()`: 获取操作系统信息
- `get_all_info(work_dir)`: 获取所有系统信息

#### 3.3.3 任务执行器模块

**职责**：
- 执行任务命令
- 实时捕获任务输出
- 管理任务生命周期
- 处理任务超时和取消

**关键方法**：
- `execute_task(task_config)`: 执行任务
- `cancel_task(task_id)`: 取消任务
- `get_task_status(task_id)`: 获取任务状态

#### 3.3.4 日志管理模块

**职责**：
- 配置和管理日志系统
- 提供日志记录接口
- 处理日志轮转

**关键方法**：
- `setup_logger(log_dir, log_level)`: 设置日志
- `get_logger(name)`: 获取日志器

### 3.4 配置管理

#### 3.4.1 命令行参数

- `--token`: 认证Token（必需）
- `--server-url`: WebSocket服务器地址
- `--log-level`: 日志级别
- `--config`: 配置文件路径
- `--work-dir`: 工作目录（可选，优先使用云端下发的）

#### 3.4.2 配置文件（可选）

支持YAML格式的配置文件：

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

### 3.5 错误处理

#### 3.5.1 连接错误

- **连接失败**：输出错误信息，退出程序
- **认证失败**：输出错误信息，退出程序
- **连接断开**：自动重连，记录重连日志

#### 3.5.2 任务执行错误

- **命令执行失败**：捕获异常，上报错误结果
- **超时**：终止任务进程，上报超时结果
- **工作目录创建失败**：输出错误，退出程序

#### 3.5.3 系统监控错误

- **监控指标采集失败**：使用上一次的值或标记为"未知"，不影响Agent运行

---

## 4. 部署与运行

### 4.1 环境要求

- **Python版本**：Python 3.7或更高版本
- **操作系统**：Linux、Windows、macOS
- **网络要求**：能够访问云端平台的WebSocket服务器
- **权限要求**：能够创建和写入工作目录

### 4.2 安装步骤

1. **安装Python依赖**：
```bash
pip install -r requirements.txt
```

2. **获取Token**：
   - 从云端平台获取Agent认证Token
   - Token与Environment（测试环境）关联

3. **运行Agent**：
```bash
python agent.py --token "your-token-here" --server-url "ws://your-server:8000/ws/agent"
```

### 4.3 运行模式

- **前台运行**：直接运行脚本，输出日志到控制台
- **后台运行**：使用`nohup`、`screen`、`tmux`或系统服务方式运行
- **Docker运行**：可打包为Docker镜像，便于部署

### 4.4 系统服务（可选）

支持配置为系统服务（systemd/Linux、LaunchDaemon/macOS、Windows Service），实现：
- 开机自启动
- 自动重启
- 日志管理

---

## 5. 安全考虑

### 5.1 Token安全

- Token应妥善保管，不要泄露
- Token应定期轮换
- Token失效后，Agent应安全退出

### 5.2 通信安全

- 支持WSS（WebSocket Secure）加密连接
- 验证服务器证书（生产环境）

### 5.3 执行安全

- 任务执行在隔离的工作目录中进行
- 限制任务执行权限（如：非root用户运行）
- 对任务命令进行基本的安全检查

---

## 6. 性能要求

### 6.1 资源占用

- Agent进程内存占用应小于100MB（空闲时）
- CPU占用应小于1%（空闲时）
- 系统监控采集时间应小于100ms

### 6.2 响应时间

- WebSocket消息发送延迟应小于50ms
- 任务启动时间应小于1秒
- 连接重连时间应小于5秒

### 6.3 并发能力

- 支持同时执行多个任务（可配置）
- 任务队列管理，避免资源竞争

---

## 7. 测试要求

### 7.1 功能测试

- Token认证测试
- WebSocket连接和重连测试
- 工作目录创建测试
- 系统监控数据采集测试
- 任务执行测试
- 任务取消测试

### 7.2 异常测试

- 网络断开重连测试
- Token失效处理测试
- 任务执行超时测试
- 工作目录权限错误测试

### 7.3 性能测试

- 长时间运行稳定性测试
- 高并发任务执行测试
- 系统资源占用测试

---

## 8. 后续扩展

### 8.1 功能扩展

- 支持文件传输（从云端下载测试文件）
- 支持任务依赖管理
- 支持任务优先级
- 支持资源限制（CPU、内存限制）

### 8.2 监控扩展

- 支持更多监控指标（网络IO、磁盘IO等）
- 支持自定义监控脚本
- 支持告警机制

### 8.3 部署扩展

- 支持集群模式
- 支持自动发现和注册
- 支持配置热更新

---

## 附录

### A. 消息协议详细说明

参考2.2.3节的消息格式定义。

### B. 错误码定义

| 错误码 | 说明 |
|--------|------|
| AUTH_FAILED | 认证失败 |
| CONNECTION_FAILED | 连接失败 |
| TASK_EXECUTION_FAILED | 任务执行失败 |
| TASK_TIMEOUT | 任务超时 |
| WORK_DIR_ERROR | 工作目录错误 |

### C. 依赖包列表

```
websockets>=10.0
psutil>=5.8.0
pyyaml>=5.4.0  # 如果使用YAML配置文件
```

---

**文档结束**

