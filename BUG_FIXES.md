# 测试用例模块 Bug 修复报告

## 修复日期
2025-12-24

## 发现并修复的Bug

### Bug 1: module_id 外键约束问题 ✅ 已修复

**问题描述**:
- `test_cases.module_id` 字段有 `ForeignKey("modules.id")` 约束
- 但模块管理尚未落库（仍使用模拟数据）
- 导致创建测试用例时报外键约束错误

**影响范围**:
- 创建测试用例失败
- 用例复制失败
- SQLAlchemy 关系映射错误

**修复方案**:
- 移除 `module_id` 的外键约束
- 保留字段为 `nullable=True`
- 在 `TestCase.module` relationship 中显式指定 `foreign_keys=[module_id]`
- 在 `Module.test_cases` relationship 中移除 `cascade="all, delete-orphan"`
- 添加 TODO 注释，待模块管理落库后恢复外键约束

**修改文件**:
- `backend/models/test_case.py`
- `backend/models/module.py`

```python
# backend/models/test_case.py

# 修复前
module_id = Column(String(36), ForeignKey("modules.id"), nullable=True, index=True)
...
module = relationship("Module", back_populates="test_cases")

# 修复后
# TODO: 当模块管理落库后，恢复外键约束 ForeignKey("modules.id")
module_id = Column(String(36), nullable=True, index=True)
...
# 显式指定 foreign_keys，因为暂时移除了外键约束
module = relationship("Module", foreign_keys=[module_id], back_populates="test_cases")
```

```python
# backend/models/module.py

# 修复前
test_cases = relationship("TestCase", back_populates="module", cascade="all, delete-orphan")

# 修复后
# 暂时移除 cascade="all, delete-orphan"，因为 test_cases.module_id 暂无外键约束
test_cases = relationship("TestCase", back_populates="module")
```

---

### Bug 2: 前后端字段名格式不一致 ✅ 已修复

**问题描述**:
- 后端数据库模型使用 `snake_case` 命名 (created_at, updated_at, case_code)
- 前端期望接收 `camelCase` 命名 (createdAt, updatedAt, caseCode)
- 导致前端无法正确读取某些字段

**影响范围**:
- 前端显示时间字段为空
- 前端无法正确访问某些字段
- 数据绑定错误

**修复方案**:
- 创建统一的序列化工具 `utils/serializer.py`
- 提供 `to_camel_case()` / `to_snake_case()` 转换函数
- 提供 `serialize_model()` / `serialize_list()` 模型序列化函数
- 在所有API响应中使用序列化器统一转换为 camelCase

**修改文件**:
- 新增: `backend/utils/serializer.py`
- 修改: `backend/api/v1/test_cases.py`
- 修改: `backend/api/v1/projects.py`

**序列化器功能**:
```python
# 单个模型序列化
serialize_model(test_case, camel_case=True)

# 列表序列化
serialize_list(test_cases, camel_case=True)

# 字段名转换
to_camel_case('created_at')  # => 'createdAt'
to_snake_case('createdAt')   # => 'created_at'
```

---

### Bug 3: 复制用例功能问题 ✅ 已修复

**问题描述**:
- 复制用例时包含了不应该复制的系统字段
- 例如：`id`, `createdAt`, `updatedAt`, `createdBy`, `updatedBy`
- 导致创建时可能出现主键冲突或数据异常

**影响范围**:
- 用例复制功能异常
- 可能导致数据库约束错误

**修复方案**:
- 明确指定需要复制的字段
- 排除系统自动生成的字段
- 让后端自动生成新的 `case_code`

**修改文件**:
- `frontend/src/views/TestCases.vue`

```typescript
// 修复前
const newCaseData = {
  ...originalCase,
  name: `${originalCase.name} (副本)`,
  caseCode: `${originalCase.caseCode}-COPY`
}
delete newCaseData.id
delete newCaseData.createdAt
delete newCaseData.updatedAt

// 修复后
const newCaseData: any = {
  name: `${originalCase.name} (副本)`,
  type: originalCase.type,
  priority: originalCase.priority,
  precondition: originalCase.precondition,
  steps: originalCase.steps,
  expectedResult: originalCase.expectedResult,
  requirementRef: originalCase.requirementRef,
  modulePath: originalCase.modulePath,
  moduleId: originalCase.moduleId,
  executorId: originalCase.executorId,
  tags: originalCase.tags,
  level: originalCase.level,
}
```

---

### Bug 4: case_tree 路由路径不一致 ✅ 已修复

**问题描述**:
- 前端调用: `GET /test-cases/case-tree`
- 后端定义: `GET /test-cases/tree`
- 路径不匹配导致 404 错误

**影响范围**:
- 用例树加载失败
- 模块树无法显示

**修复方案**:
- 统一前端路径为 `/test-cases/tree`

**修改文件**:
- `frontend/src/api/testCase.ts`

```typescript
// 修复前
getCaseTree: async (projectId: string): Promise<any[]> => {
  return apiClient.get('/test-cases/case-tree', {
    params: { project_id: projectId }
  })
}

// 修复后
getCaseTree: async (projectId: string): Promise<any[]> => {
  return apiClient.get('/test-cases/tree', {
    params: { project_id: projectId }
  })
}
```

---

### Bug 5: SQLAlchemy 关系映射错误 ✅ 已修复

**问题描述**:
```
sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize - can't proceed with initialization of other mappers. Triggering mapper: 'Mapper[Module(modules)]'. Original exception was: Could not determine join condition between parent/child tables on relationship Module.test_cases - there are no foreign keys linking these tables.
```
- 移除 `module_id` 外键约束后，SQLAlchemy 无法自动推断 Module 和 TestCase 的关系
- 导致应用启动失败

**影响范围**:
- 后端服务无法启动
- 所有依赖模型的功能都受影响

**修复方案**:
- 在 `TestCase.module` relationship 中显式指定 `foreign_keys=[module_id]`
- 移除 `Module.test_cases` 的 `cascade="all, delete-orphan"`（因为没有外键约束）
- 添加 Python 文件编码声明 `# -*- coding: utf-8 -*-`

**修改文件**:
- `backend/models/test_case.py` - 显式指定 foreign_keys
- `backend/models/module.py` - 移除 cascade
- `backend/models/__init__.py` - 添加编码声明
- `backend/database.py` - 添加编码声明

---

## 数据一致性改进

### 改进点 1: 统一API响应格式
- 所有测试用例相关的API现在返回统一的 camelCase 格式
- 项目相关的API也使用统一的序列化器

### 改进点 2: 序列化器的可扩展性
- 支持 `camel_case` 参数控制是否转换命名
- 自动处理 `datetime` 类型转换为 ISO 格式
- 可复用于其他模块

---

## 测试建议

### 功能测试
1. ✅ 创建测试用例（带模块ID和不带模块ID）
2. ✅ 查询测试用例列表（验证字段名格式）
3. ✅ 获取测试用例详情（验证时间字段）
4. ✅ 更新测试用例
5. ✅ 删除测试用例
6. ✅ 复制测试用例
7. ✅ 获取用例树

### 集成测试
1. 创建项目 → 创建用例 → 查询用例 → 复制用例
2. 验证前端能正确显示所有字段
3. 验证时间字段格式正确

---

## 待办事项

### 高优先级
- [ ] 将模块管理改为数据库持久化
- [ ] 恢复 `test_cases.module_id` 的外键约束
- [ ] 创建数据库迁移文件应用模型变更

### 中优先级
- [ ] 为其他模块（测试计划、执行历史等）应用序列化器
- [ ] 添加批量操作的错误处理
- [ ] 完善用例导入导出功能

### 低优先级
- [ ] 优化序列化器性能（大数据量场景）
- [ ] 添加字段白名单/黑名单支持
- [ ] 支持嵌套对象的序列化

---

## 相关文件清单

### 新增文件
- `backend/utils/serializer.py` - 数据序列化工具

### 修改文件（后端）
- `backend/models/test_case.py` - 移除module_id外键约束
- `backend/api/v1/test_cases.py` - 使用序列化器
- `backend/api/v1/projects.py` - 使用序列化器

### 修改文件（前端）
- `frontend/src/api/testCase.ts` - 修复路由路径
- `frontend/src/views/TestCases.vue` - 修复复制用例逻辑

---

## 总结

本次修复解决了测试用例模块的 **5 个关键bug**，主要集中在：
1. **数据库约束** - 解决外键约束导致的创建失败
2. **数据格式** - 统一前后端字段命名格式
3. **业务逻辑** - 修复复制用例的字段处理
4. **接口一致性** - 修正路由路径匹配
5. **关系映射** - 修复 SQLAlchemy 关系映射错误

所有修复均已完成并通过代码检查，建议进行完整的功能测试验证。

