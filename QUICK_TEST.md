# 快速测试指南

## Bug 修复验证步骤

### 1. 后端验证

#### 方法1：使用测试脚本（推荐）
```bash
cd backend
python test_models.py
```

#### 方法2：启动后端服务
```bash
cd backend
# 如果有虚拟环境，先激活
# source venv/bin/activate  或  conda activate ats

# 启动服务
uvicorn main:app --reload --port 3000
```

如果服务正常启动，说明模型关系映射修复成功！

### 2. 前端验证

#### 启动前端
```bash
cd frontend
npm run dev
```

#### 测试流程
1. ✅ **创建项目**
   - 进入"项目管理"页面
   - 点击"新建项目"
   - 填写项目信息并保存
   - 验证项目列表是否正确显示（包括创建时间等字段）

2. ✅ **创建测试用例**
   - 进入"测试用例"页面
   - 从下拉框选择刚创建的项目
   - 点击"新建用例"
   - 填写用例信息（可以不选择模块）
   - 点击保存
   - 验证用例是否出现在列表中

3. ✅ **复制测试用例**
   - 在用例列表中找到刚创建的用例
   - 点击"操作" -> "复制"
   - 验证是否成功创建副本

4. ✅ **查看用例详情**
   - 点击用例名称查看详情
   - 验证所有字段是否正确显示
   - 特别注意时间字段（createdAt, updatedAt）

5. ✅ **查看用例树**
   - 查看左侧模块树是否正常加载
   - 验证"全部用例"和"未规划用例"节点

### 3. 预期结果

#### ✅ 成功标志
- 后端服务正常启动，无 SQLAlchemy 错误
- 可以创建测试用例（带模块ID和不带模块ID）
- 可以复制测试用例
- 前端能正确显示所有字段（包括时间字段）
- 用例树能正常加载

#### ❌ 失败标志
- 后端启动报 `InvalidRequestError` 或 `Could not determine join condition`
- 创建用例时报 422 或 400 错误
- 前端字段显示为空或 undefined
- 用例树无法加载（404 错误）

### 4. 已修复的 Bug

| Bug | 描述 | 状态 |
|-----|------|------|
| Bug 1 | module_id 外键约束导致创建失败 | ✅ 已修复 |
| Bug 2 | 前后端字段名格式不一致 | ✅ 已修复 |
| Bug 3 | 复制用例包含系统字段 | ✅ 已修复 |
| Bug 4 | case_tree 路由路径不匹配 | ✅ 已修复 |
| Bug 5 | SQLAlchemy 关系映射错误 | ✅ 已修复 |

### 5. 数据库检查（可选）

```bash
# 进入 MySQL 容器
docker exec -it ats-mysql mysql -uats_user -pats_password ats_db

# 检查测试用例表
SELECT id, case_code, name, module_id, created_at FROM test_cases LIMIT 5;

# 退出
exit
```

### 6. 常见问题

#### Q1: 后端启动失败 - ModuleNotFoundError
**A:** 确保已安装依赖并激活虚拟环境
```bash
cd backend
pip install -r requirements.txt
```

#### Q2: 数据库连接失败 - Access denied
**A:** 确保 MySQL 容器正在运行
```bash
cd backend
docker-compose up -d mysql
```

#### Q3: 前端显示字段为空
**A:** 清除浏览器缓存并刷新页面（Cmd+Shift+R / Ctrl+Shift+R）

### 7. 完成标志

当以上所有测试都通过时，说明 Bug 修复成功！🎉

---

详细的 Bug 修复报告请查看：`BUG_FIXES.md`

