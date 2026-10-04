# SAT / ECU Simulator 与 ATS 集成

本次集成的是独立 SAT（SOA Automation Test），不是 ATS/xat 或独立 XAT。
SAT 位于 `/Users/xiongdejian/project/python_project/sat`；ECU 位于同级 `ecu-simulator`。
源码保留原位。SAT 使用旧 `ecu_simulator` 接口；离线验收使用当前 ECU 项目中的 `src/automotive_sdk` 内存模拟模块。

## 验收范围

- 前端集成命令模板与 Vite API/WebSocket 代理。
- 登录、项目、自动化用例、计划、环境与任务的真实 HTTP 请求。
- 后端队列调度到 Agent，实际 Python/pytest 子进程执行和用例结果入库、计划回填。
- 用例编号与 ID 顺序一致；同套并发执行按 execution_id 隔离。
- SAT 的 `_caseid_` 命名、多个数字编号和参数化 ID，以及完整 node ID / `ats_case` 标记。
- setup / teardown 错误、断言失败、跳过、未收集用例均按实际结果报告。
- 无输出进程的超时、取消、取消后继续排队；结果与完成消息先写磁盘，收到后端 ACK 后删除，重连补传去重。
- 原 XAT 示例保留，不改其中故意失败的 `assert False`。

离线模式只验证 SAT 数据类型和 ECU SDK 内存模拟的正响应、NRC、生命周期。它不加载 SAT 台架 hooks，也不连接 CAN/DoIP、车辆、SSH 或内部服务。真实 SAT hooks、旧 ECU 总线/诊断功能与台架运行尚未验收；离线通过不能证明这些流程通过。

## 安装与本机软件验收

在 ATS 根目录，使用 Python 3.11 或以上创建独立环境：

```bash
uv venv --python 3.11 .venv-integration
uv pip install --python .venv-integration/bin/python -r requirements-integration.txt
cd frontend
npm ci
cd ..
.venv-integration/bin/python scripts/local_lab.py
```

默认软件实验环境在 `http://127.0.0.1:3300`，后端在 `127.0.0.1:8800`。它每次创建独立临时 SQLite 数据库和 Agent 工作目录，并通过真实 API 建立示例项目、4 个自动化用例、计划和任务。实验账号为 `local_demo`，密码为 `ats-local-demo`，只存在于本次实验数据库。它不读取已有 ATS `.env` 数据库设置，不更改原 MySQL 数据。

如果仓库不在同级目录，传入实际路径：

```bash
.venv-integration/bin/python scripts/local_lab.py \
  --sat-root /path/to/sat --ecu-root /path/to/ecu-simulator \
  --port 8800 --frontend-port 3300
```

登录后到“测试任务”执行预置的“SAT / ECU 离线验收”，或者创建自动化用例编号 `sat_import`、`ecu_positive`、`ecu_negative`、`ecu_lifecycle`，在任务编辑器选择“使用离线软件验收”。执行命令为：

```text
ats-sat --mode offline
```

Ctrl+C 关闭实验服务。数据库和执行目录保留在终端打印的临时路径，方便核对证据。可修改端口避免和已有服务冲突。

## 在已有 ATS 环境接入 Agent

保留正常后端/前端启动方式及已有环境 Token。参考 `agent/config.sat.yaml.example` 配置 SAT 根目录、ECU 根目录和 Python 解释器；解释器需安装 pytest，台架模式还需 SAT 与旧 ECU 的完整依赖。

```bash
.venv-integration/bin/python -m agent.agent \
  --token '<ATS 环境管理中生成的 Token>' \
  --config agent/config.sat.yaml.example
```

同级现有仓库会作为默认路径；配置可覆盖。前端仍使用已有“环境 / 测试计划 / 测试任务”流程，不新增数据库字段。修复了创建用例时未持久化自动化标记、创建环境时丢失重连延迟、创建任务时丢失 Git 开关，以及启动时未注册任务队列模型的问题。用例需求编号、模块路径、等级和步骤预期可正常编辑；计划环境与通知配置元数据保存在已有字段，已接入真实执行完成和报告生成的站内通知；邮件、Webhook、短信等外发尚未实现，计划内通知配置只保存元数据。前端计划详情使用真实状态统计，新增详情编辑/执行、任务取消/日志和创建文件夹确认入口。

每次运行产物在 `<Agent 工作目录>/suites/<suite_id>/executions/<execution_id>/`：

- `selection.json`：编号与 ATS 用例 ID 的对应关系。
- `results.json`、`junit.xml`：实际测试阶段结果。
- `output.log`：执行输出。
- `run.json`：任务状态、实际退出码与 timeout/cancelled 等 outcome。

结果上传按执行 ID 和用例 ID 生成稳定记录 ID，重复回传不新增记录。`sat-outbox` 内的消息得到数据库处理后的 ACK 才删除。命令启动失败或所选用例未运行不会记为成功。

## 台架模式：已提供适配入口，尚未连接硬件验收

默认 `allow_hardware: false`。仅在经批准且具备完整依赖的台架设置为 true 后，使用实际 SAT 路径和配置：

```text
ats-sat --mode sat --tests test_case/your_domain/test_your_feature.py --bench-config bench_config/your_bench.yaml --case-config test_case/your_domain/config/latest_config.yaml --timeout 3600
```

`--tests`、`--bench-config`、`--case-config` 必须指向 SAT 根目录内存在的路径。台架模式加载真实 SAT conftest/hooks，并保留旧 ECU 导入路径；SAT 自身的网络、设备初始化、分布式调度与清理副作用需在台架验收。未自动安装 SAT 私有包、执行部署脚本、改主机网络或运行刷写流程。

`--mode sat` 不是“纯软件仿真”开关。不要把离线用例编号用于真实 SAT 用例；ATS 中的编号应对应 SAT 参数化 ID、函数 `_caseid_` 编号或完整 pytest node ID。多个参数化实例若共享同一 ATS 编号会报配置错误，应使用各自的 node ID。

## 回归命令与边界

```bash
# 测试会创建新 SQLite 库，监听 127.0.0.1 临时端口；不会使用现有 ATS 数据库。
ATS_SAT_ROOT=/path/to/sat ATS_ECU_ROOT=/path/to/ecu-simulator \
  .venv-integration/bin/python -m pytest tests -q -o addopts=''

# 原 XAT 基线：仍有 1 个明确 assert False 的示例失败。
PYTHONPATH=xat .venv-integration/bin/python -m pytest xat/tests -q -o addopts=''

cd frontend
npm run type-check
npm run test:unit
npm run build
```

本次在 macOS/Python 3.11 验证。前端 vue-tsc 1.8.27 与原安装的 TypeScript 5.9.3 不兼容，已固定 TypeScript 5.3.3，`npm ci` 会使用更新的锁文件。从原始 Git HEAD 提取的前端用同一编译器复测有 153 项类型错误；已修复 API 响应解包、字段契约、树过滤、事件参数和未使用声明，保持 strict/noUnused 检查，完整 `npm run type-check` 与 `npm run build`（vue-tsc + Vite）均通过。`npm run test:unit` 的 2 项请求契约测试通过。使用独立无界面 Chrome 实际验证登录、执行确认、任务完成/通过历史、用例编辑保存、真实计划统计和详情编辑按钮，没有页面脚本错误。独立临时 MySQL 8.0.28 / Redis 6.2.6 Unix socket 与实际 Celery solo 队列已完成导入创建、重复更新、导出、跨项目冲突保护验证；未接入用户的生产数据库、RabbitMQ 或 MinIO。真实 SAT 台架、所有旧 ECU 设备功能与 Windows 行为未验收，也不代表 ATS 的全部既有功能均已验收。

## 已补通的四项本地功能

- **单用例执行**：测试用例行菜单“执行”，选择同项目且包含该用例的既有 `ats-sat` 模板。生成单用例任务复用环境、命令和队列，不改原模板、不执行整套。非自动化、未包含该用例或非 `ats-sat` 模板会拒绝。实际状态和日志在“执行记录”“测试任务”查看，不会返回模拟通过。
- **工作空间上传**：节点创建人或系统管理员打开在线环境“工作空间 / 上传文件”，最大 10MB。HTTP multipart 经已有 WebSocket 到 Agent，独占创建保护已有文件；拒绝路径穿越、绝对路径、符号链接越界和非法文件名。只写入该 Agent 工作目录，不调用网盘或对象存储。Agent WebSocket 上限 16MB，容纳 base64 的 10MB 文件。
- **报告**：“测试报告”或仪表盘选择日期生成 HTML，统计和日志取实际持久化执行记录；无记录显示零执行/零通过。下载要求登录且只允许报告创建人，所有名字与日志 HTML 转义，下载携带 CSP sandbox。支持结果汇总、明细、每日记录和用例覆盖数。PDF、Excel 报告、图表建议、定时、共享、邮件发送、重新生成、执行附件/手工改结果未支持，界面明确提示或 API 返回不支持。
- **站内通知**：实际执行完成/失败/取消和报告生成产生稳定去重事件，顶部通知每5秒刷新。只能读和标记自己的通知；无模拟通知，未向外部收件人发送消息。个人通知偏好与计划外发配置尚未执行外发。

完整回归包含13项：原10项加单用例/真实记录/私有报告与通知、模板拒绝、上传正负边界。浏览器验收使用独立无头 Chrome，不占用用户浏览器。

可选验证已有生产依赖（仅本机已安装上述 MySQL/Redis 时）：

```bash
.venv-integration/bin/python scripts/isolated_production_check.py
```

脚本创建自身临时目录与 Unix socket，不监听 TCP 或使用现有数据库；用新 Celery 队列处理合成数据，然后关闭自己的实例，日志/数据保留便于核对。实际生产部署、RabbitMQ/MinIO 和硬件执行需要单独验收。Celery具体用例任务已注册；字符串 UUID 与数据库字段对齐，跨项目编号冲突不会更新别的项目，导入不删除调用者输入文件。

本文件提供工程运行与验收说明。Codex 产品项目和目标由应用管理；这份运行说明不会创建或替代产品目标。
