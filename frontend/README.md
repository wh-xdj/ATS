# ATS Frontend

自动化测试系统 (Automated Test System) 前端应用

## 技术栈

- **框架**: Vue 3.4+ (Composition API)
- **语言**: TypeScript 5.3+
- **构建工具**: Vite 5.0+
- **UI 组件库**: Ant Design Vue 4.0+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **HTTP 客户端**: Axios 1.6+
- **图表库**: ECharts 5.4+ / Vue-ECharts
- **工具库**: 
  - Day.js (日期处理)
  - Lodash-es (工具函数)
  - VueUse (Vue 组合式工具集)
  - Vue-Draggable-Plus (拖拽功能)

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API 接口定义
│   ├── components/     # 公共组件
│   ├── layouts/        # 布局组件
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia 状态管理
│   ├── styles/         # 全局样式
│   ├── types/          # TypeScript 类型定义
│   ├── utils/          # 工具函数
│   ├── views/          # 页面组件
│   ├── App.vue         # 根组件
│   └── main.ts         # 入口文件
├── index.html          # HTML 模板
├── package.json        # 项目配置
├── tsconfig.json       # TypeScript 配置
└── vite.config.ts      # Vite 配置
```

## 环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0 或 yarn >= 1.22.0 或 pnpm >= 8.0.0

## 快速开始

### 安装依赖

```bash
npm install
# 或
yarn install
# 或
pnpm install
```

### 开发环境运行

```bash
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

应用将在 `http://localhost:3000` 启动

### 构建生产版本

```bash
npm run build
# 或
yarn build
# 或
pnpm build
```

构建产物将输出到 `dist/` 目录

### 预览生产构建

```bash
npm run preview
# 或
yarn preview
# 或
pnpm preview
```

### 代码检查

```bash
# ESLint 检查并自动修复
npm run lint

# TypeScript 类型检查
npm run type-check
```

## 开发配置

### 环境变量

创建 `.env` 文件（可选）：

```env
# API 基础路径
VITE_API_BASE_URL=/api/v1

# WebSocket 地址
VITE_WS_URL=ws://localhost:8000/ws
```

### 代理配置

开发环境已配置代理，将 `/api` 请求代理到后端服务器 `http://127.0.0.1:8000`

配置位置：`vite.config.ts`

### 路径别名

项目配置了以下路径别名：

- `@` → `src/`
- `@components` → `src/components/`
- `@views` → `src/views/`
- `@stores` → `src/stores/`
- `@utils` → `src/utils/`
- `@types` → `src/types/`
- `@api` → `src/api/`

## 功能模块

### 1. 用户认证
- 登录/登出
- Token 自动刷新
- 权限验证

### 2. 项目管理
- 项目列表
- 项目创建/编辑/删除
- 项目成员管理
- 项目模块管理

### 3. 测试用例管理
- 用例树形结构
- 用例创建/编辑/删除
- 用例导入/导出
- 用例搜索和筛选

### 4. 测试计划
- 计划创建/编辑/执行
- 计划状态管理
- 计划执行历史

### 5. 测试执行
- 执行记录查看
- 执行结果统计
- 执行日志查看

### 6. 测试报告
- 报告生成
- 报告查看/下载
- 报告统计图表

### 7. 环境管理
- 环境配置
- 环境变量管理

### 8. 仪表盘
- 数据统计
- 图表展示
- 执行趋势

## 代码规范

### 命名规范

- **组件**: PascalCase (如 `TestCaseDetail.vue`)
- **文件/目录**: kebab-case (如 `test-case.ts`)
- **变量/函数**: camelCase (如 `getUserInfo`)
- **常量**: UPPER_SNAKE_CASE (如 `API_BASE_URL`)
- **类型/接口**: PascalCase (如 `User`, `Project`)

### 组件规范

- 使用 `<script setup>` 语法
- 使用 TypeScript 类型定义
- Props 和 Emits 使用 `defineProps` 和 `defineEmits`
- 使用 Composition API

### 样式规范

- 使用 Scoped CSS
- 优先使用 Ant Design Vue 组件样式
- 自定义样式使用 CSS 变量

## 常见问题

### 1. 端口被占用

修改 `vite.config.ts` 中的 `server.port` 配置

### 2. API 请求失败

检查：
- 后端服务是否启动
- 代理配置是否正确
- 网络连接是否正常

### 3. 类型错误

运行 `npm run type-check` 检查类型错误

### 4. 构建失败

- 检查 Node.js 版本是否符合要求
- 清除 `node_modules` 和锁文件后重新安装
- 检查是否有语法错误

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 开发工具推荐

- **IDE**: VS Code
- **VS Code 插件**:
  - Volar (Vue 3 支持)
  - ESLint
  - Prettier
  - TypeScript Vue Plugin (Volar)

## 相关文档

- [Vue 3 文档](https://vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [Ant Design Vue 文档](https://antdv.com/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)

## 许可证

MIT License

