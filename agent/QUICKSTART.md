# Agent 快速开始指南

## 快速启动

### 方式一：使用 uv（推荐）

1. **安装 uv**（如果尚未安装）：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **安装依赖并运行**：

```bash
cd agent
uv sync
uv run python agent.py --token "your-token-here" --server-url "ws://localhost:8000/ws/agent"
```

或者从项目根目录运行：

```bash
# 从ATS项目根目录
uv run python -m agent.agent --token "your-token-here" --server-url "ws://localhost:8000/ws/agent"
```

### 方式二：使用 pip（传统方式）

1. **安装依赖**：

```bash
cd agent
pip install -r requirements.txt
```

2. **运行Agent**：

从agent目录运行：

```bash
cd agent
PYTHONPATH=. python agent.py --token "your-token-here" --server-url "ws://localhost:8000/ws/agent"
```

或者从项目根目录运行：

```bash
# 从ATS项目根目录
python -m agent.agent --token "your-token-here" --server-url "ws://localhost:8000/ws/agent"
```

### 3. 使用配置文件（可选）

```bash
# 复制示例配置文件
cp config.yaml.example config.yaml

# 编辑配置文件，填入Token和服务器地址
# 然后运行
python agent.py --token "your-token" --config config.yaml
```

## 常见问题

### Q: 如何获取Token？

A: Token需要从ATS平台获取，通常与Environment（测试环境）关联。请联系平台管理员。

### Q: 连接失败怎么办？

A: 检查以下几点：
1. 网络连接是否正常
2. WebSocket服务器地址是否正确（注意是 `ws://` 或 `wss://`）
3. Token是否有效
4. 防火墙是否阻止了连接

### Q: 如何查看日志？

A: Agent日志保存在 `{work_dir}/logs/agent.log`，任务日志保存在 `{work_dir}/logs/tasks/{task_id}.log`。

### Q: 如何后台运行？

**Linux/macOS:**
```bash
nohup python agent.py --token "your-token" --server-url "ws://server:8000/ws/agent" > agent.out 2>&1 &
```

**使用screen:**
```bash
screen -S agent
python agent.py --token "your-token" --server-url "ws://server:8000/ws/agent"
# 按 Ctrl+A 然后按 D 退出
```

**使用tmux:**
```bash
tmux new -s agent
python agent.py --token "your-token" --server-url "ws://server:8000/ws/agent"
# 按 Ctrl+B 然后按 D 退出
```

## 测试连接

如果只是想测试Agent是否能正常启动（不连接服务器），可以查看帮助信息：

```bash
python agent.py --help
```

## 更多信息

详细文档请参考 [README.md](README.md)

