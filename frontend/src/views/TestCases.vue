<template>
  <div class="test-cases-container" @click="hideModuleContextMenu">
    <!-- 顶部项目选择器 -->
    <div class="project-selector-bar">
      <a-select
        v-model:value="currentProjectId"
        style="width: 220px"
        placeholder="选择项目"
      >
        <a-select-option
          v-for="project in projects"
          :key="project.id"
          :value="project.id"
        >
          {{ project.name }}
        </a-select-option>
      </a-select>
    </div>

    <a-layout class="test-cases-layout">
      <!-- 左侧模块树 -->
      <a-layout-sider width="240" class="module-tree-sider">
        <a-input-search
          v-model:value="moduleSearchValue"
          placeholder="请输入模块名称"
          class="module-search"
          @search="handleModuleSearch"
        />

        <a-tree
          :tree-data="moduleTreeData"
          :selected-keys="selectedModuleKeys"
          :expanded-keys="expandedModuleKeys"
          block-node
          show-icon
          multiple
          draggable
          :allow-drop="allowModuleDrop"
          @select="handleModuleSelect"
          @expand="handleModuleExpand"
          @rightClick="handleModuleRightClick"
          @drop="handleModuleDrop"
        >
          <template #title="{ title, count, nodeType }">
            <span class="tree-node-title">
              {{ title }}
              <span v-if="count !== undefined && nodeType !== 'case'" class="count-badge">({{ count }})</span>
            </span>
          </template>
          <template #icon="{ nodeType, isLeaf }">
            <FolderOutlined v-if="nodeType === 'module'" style="color: #faad14" />
            <FileTextOutlined v-else-if="nodeType === 'case'" style="color: #1890ff" />
            <FileOutlined v-else-if="isLeaf" />
            <FolderOutlined v-else style="color: #faad14" />
          </template>
        </a-tree>

        <!-- 模块/用例树右键菜单 -->
        <div
          v-if="moduleContextMenu.visible"
          class="module-context-menu"
          :style="{ left: moduleContextMenu.x + 'px', top: moduleContextMenu.y + 'px' }"
          @click.stop
        >
          <a-menu @click="handleModuleContextMenuClick">
            <!-- 虚拟节点只显示新增操作 -->
            <template v-if="contextMenuNodeType === 'virtual'">
              <a-menu-item key="addModule">新增模块</a-menu-item>
              <a-menu-item key="addCase">新增用例</a-menu-item>
              <a-menu-divider />
              <a-menu-item key="export">导出用例</a-menu-item>
            </template>
            <!-- 模块节点显示全部操作 -->
            <template v-else-if="contextMenuNodeType === 'module'">
              <a-menu-item key="addModule">新增子模块</a-menu-item>
              <a-menu-item key="addCase">新增用例</a-menu-item>
              <a-menu-divider />
              <a-menu-item key="export">导出用例</a-menu-item>
              <a-menu-divider />
              <a-menu-item key="rename">重命名</a-menu-item>
              <a-menu-item key="delete">删除</a-menu-item>
              <a-menu-divider v-if="selectedModuleKeys.length > 1" />
              <a-menu-item v-if="selectedModuleKeys.length > 1" key="batchDelete">
                批量删除所选模块
              </a-menu-item>
            </template>
            <!-- 用例节点只显示删除操作 -->
            <template v-else-if="contextMenuNodeType === 'case'">
              <a-menu-item key="deleteCase">删除用例</a-menu-item>
            </template>
          </a-menu>
        </div>
      </a-layout-sider>

      <!-- 右侧主内容区 -->
      <a-layout-content class="cases-content">
        <!-- 固定顶部工具栏 -->
        <div class="fixed-toolbar">
          <a-space class="toolbar">
            <a-button type="primary" @click="handleCreateCase">
              <template #icon><PlusOutlined /></template>
              新建
            </a-button>
            <a-button @click="handleImport">
              <template #icon><ImportOutlined /></template>
              导入
            </a-button>
            <a-divider type="vertical" />
            <a-input-search
              v-model:value="searchValue"
              placeholder="通过ID/名称/标签搜索"
              style="width: 200px"
              @search="handleSearch"
              allow-clear
            />
            <a-select
              v-model:value="viewMode"
              style="width: 100px"
            >
              <a-select-option value="all">全部数据</a-select-option>
              <a-select-option value="my">我的数据</a-select-option>
            </a-select>
            <a-button @click="filterDrawerVisible = true">
              <template #icon><FilterOutlined /></template>
              筛选
            </a-button>
            <a-button-group>
              <a-button :type="viewLayout === 'list' ? 'primary' : 'default'" @click="viewLayout = 'list'">
                <template #icon><UnorderedListOutlined /></template>
              </a-button>
              <a-button :type="viewLayout === 'grid' ? 'primary' : 'default'" @click="viewLayout = 'grid'">
                <template #icon><AppstoreOutlined /></template>
              </a-button>
            </a-button-group>
            <a-button @click="loadTestCases">
              <template #icon><ReloadOutlined /></template>
            </a-button>
            <a-popover
              v-model:visible="columnSettingVisible"
              trigger="click"
              placement="bottomRight"
              title="自定义列显示"
            >
              <template #content>
                <div style="width: 200px;">
                  <a-checkbox-group
                    v-model:value="visibleColumnKeys"
                    :options="columnOptions"
                    style="display: flex; flex-direction: column; gap: 8px;"
                  />
                  <a-divider style="margin: 12px 0;" />
                  <a-space>
                    <a-button size="small" @click="resetColumnSettings">重置</a-button>
                    <a-button size="small" type="primary" @click="saveColumnSettings">保存</a-button>
                  </a-space>
                </div>
              </template>
              <a-button>
                <template #icon><SettingOutlined /></template>
                列设置
              </a-button>
            </a-popover>
          </a-space>
        </div>

        <!-- 可滚动内容区域 -->
        <div class="scrollable-table-content">
          <!-- 表格 -->
          <a-card class="table-card">
            <a-table
              :columns="columns"
              :data-source="testCases"
              :loading="loading"
              :row-selection="rowSelection"
              :pagination="false"
              :row-key="record => record.id"
              :scroll="{ x: 1500 }"
              @change="handleTableChange"
              size="middle"
              :title="() => tableTitle"
            >
            <template #bodyCell="{ column, record, index }">
              <template v-if="column.key === 'id'">
                <a @click="handleViewCase(record)" class="case-link">{{ getCaseDisplayId(record, index) }}</a>
              </template>

              <template v-else-if="column.key === 'name'">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <BugOutlined v-if="record.type === 'bug'" style="color: #ff4d4f" />
                  <ThunderboltOutlined v-else-if="record.type === 'interface'" style="color: #1890ff" />
                  <AppstoreOutlined v-else-if="record.type === 'ui'" style="color: #722ed1" />
                  <FileTextOutlined v-else style="color: #8c8c8c" />
                  <span :title="record.name">{{ record.name }}</span>
                </div>
              </template>

              <template v-else-if="column.key === 'level'">
                <a-tag :color="getLevelColor(record.priority)">
                  <template #icon>
                    <FlagOutlined />
                  </template>
                  {{ record.priority }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'reviewResult'">
                <a-tag :color="getReviewResultColor((record as any).reviewResult || 'not_reviewed')">
                  <template #icon>
                    <CheckSquareOutlined v-if="(record as any).reviewResult === 'passed'" />
                  </template>
                  {{ getReviewResultLabel((record as any).reviewResult || 'not_reviewed') }}
                </a-tag>
              </template>

              <template v-else-if="column.key === 'modulePath'">
                <span :title="getModuleName(record.moduleId) || '未规划用例'" style="color: #8c8c8c">
                  <FolderOutlined /> {{ getModuleName(record.moduleId) || '未规划用例' }}
                </span>
              </template>

              <template v-else-if="column.key === 'tags'">
                <span v-if="(record.tags || []).length === 0">-</span>
                <a-space v-else wrap :size="2">
                  <a-tag v-for="tag in (record.tags || []).slice(0, 2)" :key="tag" size="small">
                    <TagOutlined /> {{ tag }}
                  </a-tag>
                  <a-tag v-if="(record.tags || []).length > 2" size="small" color="default">
                    +{{ (record.tags || []).length - 2 }}
                  </a-tag>
                </a-space>
              </template>

              <template v-else-if="column.key === 'isAutomated'">
                <div v-if="(record.isAutomated ?? record.is_automated)" style="color: #52c41a">
                  <CodeOutlined /> 是
                </div>
                <div v-else style="color: #bfbfbf">
                  <BlockOutlined /> 否
                </div>
              </template>

              <template v-else-if="column.key === 'createdBy'">
                {{ getDisplayName(record.createdBy) }}
              </template>

              <template v-else-if="column.key === 'createdAt'">
                {{ formatDateTime(record.createdAt) }}
              </template>

              <template v-else-if="column.key === 'updatedBy'">
                {{ getDisplayName(record.updatedBy || record.createdBy) }}
              </template>

              <template v-else-if="column.key === 'updatedAt'">
                {{ formatDateTime(record.updatedAt) }}
              </template>

              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="handleEditCase(record)">
                    编辑
                  </a-button>
                  <a-button type="link" size="small" @click="handleCopyCase(record)">
                    复制
            </a-button>
            <a-dropdown>
                    <a-button type="link" size="small">
                      <template #icon><MoreOutlined /></template>
              </a-button>
              <template #overlay>
                      <a-menu>
                        <a-menu-item key="delete" @click="handleDeleteCase(record)">
                          删除
                        </a-menu-item>
                        <a-menu-item key="execute" @click="handleExecuteCase(record)">
                          执行
                        </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
        </div>

        <!-- 固定底部分页器和批量操作栏 -->
        <div class="fixed-footer">
          <!-- 批量操作栏 -->
          <div v-if="selectedRowKeys.length > 0" class="batch-actions">
            <a-space>
              <span>已选择 {{ selectedRowKeys.length }} 条</span>
              <a-dropdown>
                <a-button>
                  导出
                  <template #icon><DownOutlined /></template>
                </a-button>
                <template #overlay>
                  <a-menu @click="handleExport">
                    <a-menu-item key="excel">导出 Excel 格式 (xlsx)</a-menu-item>
                    <a-menu-item key="xmind">导出思维导图 (xmind)</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
              <a-button @click="handleBatchEdit">编辑</a-button>
              <a-button @click="handleBatchMove">移动到</a-button>
              <a-button @click="handleBatchCopy">复制到</a-button>
              <a-dropdown>
                <a-button>
                  <template #icon><MoreOutlined /></template>
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="delete" @click="handleBatchDelete">批量删除</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
              <a-button @click="clearSelection">清空</a-button>
            </a-space>
          </div>
          <!-- 分页器 -->
          <a-pagination
            v-model:current="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :show-size-changer="true"
            :show-quick-jumper="true"
            :show-total="(total) => `共 ${total} 条`"
            @change="handlePaginationChange"
            @show-size-change="handlePaginationChange"
            style="flex: 1; display: flex; justify-content: flex-end;"
          />
        </div>
      </a-layout-content>
    </a-layout>

    <!-- 详情抽屉 -->
    <a-drawer
      v-model:visible="detailCaseVisible"
      :title="viewingCaseId ? '用例详情' : ''"
      width="60%"
      placement="right"
      :mask-closable="false"
      :destroy-on-close="true"
      :closable="true"
    >
      <TestCaseDetail
        v-if="viewingCaseId"
        :case-id="viewingCaseId"
        :project-id="projectId"
        :read-only="true"
        @edit="handleEditFromDetail"
      />
    </a-drawer>

    <!-- 编辑用例抽屉 -->
    <a-drawer
      v-model:visible="editCaseVisible"
      :title="editingCaseId ? '编辑用例' : '新建用例'"
      width="60%"
      placement="right"
      :mask-closable="false"
      :destroy-on-close="true"
      :closable="true"
    >
      <TestCaseEdit
        :case-id="editingCaseId"
        :project-id="projectId"
        :default-module-id="defaultModuleId"
        @save="handleSaveCase"
        @cancel="editCaseVisible = false"
      />
    </a-drawer>

    <!-- 筛选抽屉 -->
    <TestCaseFilter
      v-model:visible="filterDrawerVisible"
      :available-fields="filterFields"
      :module-tree-data="moduleTreeData"
      @apply="handleFilterApply"
      @reset="handleFilterReset"
    />

    <!-- 导入用例对话框 -->
    <ImportCasesModal
      v-model:visible="importModalVisible"
      :project-id="projectId"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, createVNode } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal, Input } from 'ant-design-vue'
import {
  PlusOutlined,
  ImportOutlined,
  FilterOutlined,
  UnorderedListOutlined,
  AppstoreOutlined,
  ReloadOutlined,
  MoreOutlined,
  DownOutlined,
  FolderOutlined,
  FileOutlined,
  FileTextOutlined,
  SettingOutlined,
  TagOutlined,
  BugOutlined,
  CheckSquareOutlined,
  FlagOutlined,
  ThunderboltOutlined,
  CodeOutlined,
  BarsOutlined
} from '@ant-design/icons-vue'
import TestCaseEdit from '@/components/TestCase/TestCaseEdit.vue'
import TestCaseDetail from '@/components/TestCase/TestCaseDetail.vue'
import TestCaseFilter from '@/components/TestCase/TestCaseFilter.vue'
import ImportCasesModal from '@/components/TestCase/ImportCasesModal.vue'
import { testCaseApi } from '@/api/testCase'
import { projectApi } from '@/api/project'
import { useProjectStore } from '@/stores/project'
import { useUserStore } from '@/stores/user'
import type { TestCase, Project } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const userStore = useUserStore()

// 当前项目 ID：优先使用 store，其次使用已有项目列表的第一个
const projects = computed<Project[]>(() => projectStore.projects)
const projectId = computed<string>(() => {
  if (projectStore.currentProject) {
    return projectStore.currentProject.id
  }
  return projects.value[0]?.id || ''
})

// 页面内部的项目下拉（示例项目选择）
const currentProjectId = computed<string | undefined>({
  get() {
    return projectId.value
  },
  set(value: string | undefined) {
    if (!value) return
    const target = projects.value.find(p => p.id === value) || null
    projectStore.setCurrentProject(target)
    // 路由固定为 /test-cases，不需要携带 projectId
    if (route.path !== '/test-cases') {
      router.push('/test-cases')
    }
    // 重新加载数据
    loadTestCases()
    loadModuleTree()
  }
})

// 左侧模块树
const moduleSearchValue = ref('')
const moduleTreeData = ref<any[]>([])
const selectedModuleKeys = ref<string[]>(['all'])
const expandedModuleKeys = ref<string[]>([])
const modules = ref<any[]>([])
const flatModuleKeys = ref<string[]>([])
const lastSelectedModuleKey = ref<string | null>(null)
const isShiftKeyPressed = ref(false)

// 模块树右键菜单状态
const moduleContextMenu = reactive<{
  visible: boolean
  x: number
  y: number
  node: any | null
}>({
  visible: false,
  x: 0,
  y: 0,
  node: null
})

// 计算右键菜单节点类型
const contextMenuNodeType = computed(() => {
  const node = moduleContextMenu.node
  if (!node) return 'virtual'

  const key = node.key as string
  if (key === 'all' || key === 'unplanned') {
    return 'virtual'
  }

  // 检查是否是用例节点（key以case_开头）
  if (key.startsWith('case_')) {
    return 'case'
  }

  return 'module'
})

// 表格标题（自定义title信息）
const tableTitle = computed(() => {
  const selectedModule = selectedModuleKeys.value[0]
  if (!selectedModule || selectedModule === 'all') {
    return `全部用例 (${pagination.total})`
  }
  const module = findModuleById(selectedModule)
  if (module) {
    return `${module.name} (${pagination.total})`
  }
  return `用例列表 (${pagination.total})`
})

// 右侧表格
const loading = ref(false)
const testCases = ref<TestCase[]>([])
const selectedRowKeys = ref<string[]>([])
const searchValue = ref('')
const viewMode = ref('all')
const viewLayout = ref<'list' | 'grid'>('list')
const filterDrawerVisible = ref(false)

// 高级筛选条件
const advancedFilters = ref<Array<{
  field: string
  operator: string
  value: any
}>>([])
const filterLogic = ref<'and' | 'or'>('and')

// 筛选字段定义（从数据库获取）
const filterFields = ref<any[]>([])

// 加载筛选字段配置
const loadFilterFields = async () => {
  if (!projectId.value) return

  try {
    const fields = await testCaseApi.getFilterFields(projectId.value)
    // 转换后端数据格式为前端需要的格式
    filterFields.value = fields.map((field: any) => ({
      key: field.fieldKey,
      label: field.fieldLabel,
      type: field.fieldType,
      operators: field.operators,
      options: field.options
    }))
  } catch (error) {
    console.error('Failed to load filter fields:', error)
    // 如果加载失败，使用默认字段
    filterFields.value = getDefaultFilterFields()
  }
}

// 默认筛选字段（作为后备）
const getDefaultFilterFields = () => [
  {
    key: 'id',
    label: 'ID',
    type: 'text' as const,
    operators: ['contains', 'equals', 'not_equals']
  },
  {
    key: 'name',
    label: '用例名称',
    type: 'text' as const
  },
  {
    key: 'moduleId',
    label: '所属模块',
    type: 'module' as const
  },
  {
    key: 'priority',
    label: '用例等级',
    type: 'select' as const,
    options: [
      { label: 'P0', value: 'P0' },
      { label: 'P1', value: 'P1' },
      { label: 'P2', value: 'P2' },
      { label: 'P3', value: 'P3' }
    ]
  },
  {
    key: 'type',
    label: '用例类型',
    type: 'select' as const,
    options: [
      { label: '功能测试', value: 'functional' },
      { label: '接口测试', value: 'interface' },
      { label: 'UI测试', value: 'ui' },
      { label: '性能测试', value: 'performance' },
      { label: '安全测试', value: 'security' }
    ]
  },
  {
    key: 'status',
    label: '执行结果',
    type: 'select' as const,
    options: [
      { label: '未执行', value: 'not_executed' },
      { label: '通过', value: 'passed' },
      { label: '失败', value: 'failed' },
      { label: '阻塞', value: 'blocked' },
      { label: '跳过', value: 'skipped' }
    ]
  },
  {
    key: 'isAutomated',
    label: '是否自动化',
    type: 'select' as const,
    options: [
      { label: '是', value: true },
      { label: '否', value: false }
    ]
  },
  {
    key: 'tags',
    label: '标签',
    type: 'tags' as const
  },
  {
    key: 'requirementRef',
    label: '需求关联',
    type: 'text' as const
  },
  {
    key: 'precondition',
    label: '前置条件',
    type: 'text' as const
  }
]

// 旧的筛选条件（保留兼容性）
const filters = reactive({
  level: undefined as string | undefined,
  reviewResult: undefined as string | undefined,
  executionResult: undefined as string | undefined
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 所有可用的表格列定义
const allColumns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 120,
    sorter: true,
    ellipsis: true,
    defaultVisible: true
  },
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 250,
    sorter: true,
    ellipsis: true,
    defaultVisible: true
  },
  {
    title: '用例等级',
    dataIndex: 'priority',
    key: 'level',
    width: 100,
    filters: [
      { text: 'P0', value: 'P0' },
      { text: 'P1', value: 'P1' },
      { text: 'P2', value: 'P2' },
      { text: 'P3', value: 'P3' }
    ],
    defaultVisible: true
  },
  {
    title: '评审结果',
    dataIndex: 'reviewResult',
    key: 'reviewResult',
    width: 100,
    filters: [
      { text: '未评审', value: 'not_reviewed' },
      { text: '已通过', value: 'passed' },
      { text: '不通过', value: 'rejected' },
      { text: '重新提审', value: 'resubmit' }
    ],
    defaultVisible: true
  },
  {
    title: '执行结果',
    dataIndex: 'status',
    key: 'executionResult',
    width: 100,
    filters: [
      { text: '未执行', value: 'not_executed' },
      { text: '成功', value: 'passed' },
      { text: '失败', value: 'failed' },
      { text: '阻塞', value: 'blocked' },
      { text: '跳过', value: 'skipped' }
    ],
    defaultVisible: true
  },
  {
    title: '所属模块',
    dataIndex: 'modulePath',
    key: 'modulePath',
    width: 150,
    ellipsis: true,
    defaultVisible: true
  },
  {
    title: '标签',
    dataIndex: 'tags',
    key: 'tags',
    width: 120,
    ellipsis: true,
    defaultVisible: false
  },
  {
    title: '是否自动化',
    dataIndex: 'isAutomated',
    key: 'isAutomated',
    width: 100,
    align: 'center' as const,
    filters: [
      { text: '是', value: true },
      { text: '否', value: false }
    ],
    defaultVisible: true
  },
  {
    title: '创建人',
    dataIndex: 'createdByName',
    key: 'createdBy',
    width: 100,
    ellipsis: true,
    defaultVisible: false
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 200,
    sorter: true,
    defaultVisible: false
  },
  {
    title: '更新人',
    dataIndex: 'updatedByName',
    key: 'updatedBy',
    width: 100,
    ellipsis: true,
    defaultVisible: true
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    width: 200,
    sorter: true,
    defaultVisible: true
  }
]

// 操作列（始终显示）
const actionColumn = {
  title: '操作',
  key: 'actions',
  width: 150,
  fixed: 'right' as const
}

// 可选列的 key 列表（用于复选框）
const columnOptions = allColumns.map(col => ({
  label: col.title,
  value: col.key
}))

// 当前选中显示的列（从 localStorage 读取或使用默认值）
const getInitialVisibleColumns = () => {
  const saved = localStorage.getItem('testCaseVisibleColumns')
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch {
      return allColumns.filter(col => col.defaultVisible).map(col => col.key)
    }
  }
  return allColumns.filter(col => col.defaultVisible).map(col => col.key)
}

const visibleColumnKeys = ref<string[]>(getInitialVisibleColumns())

// 列设置弹窗可见性
const columnSettingVisible = ref(false)

// 动态计算显示的列
const columns = computed(() => {
  const visibleCols = allColumns.filter(col => visibleColumnKeys.value.includes(col.key))
  return [...visibleCols, actionColumn]
})

// 保存列设置
const saveColumnSettings = () => {
  localStorage.setItem('testCaseVisibleColumns', JSON.stringify(visibleColumnKeys.value))
  columnSettingVisible.value = false
  message.success('列设置已保存')
}

// 重置列设置
const resetColumnSettings = () => {
  visibleColumnKeys.value = allColumns.filter(col => col.defaultVisible).map(col => col.key)
  localStorage.removeItem('testCaseVisibleColumns')
  message.success('已重置为默认列')
}

// 生成用例显示ID
const getCaseDisplayId = (record: TestCase, index: number) => {
  // 优先使用 caseCode
  if (record.caseCode) {
    return record.caseCode
  }
  // 否则生成序号格式（001, 002, ...）
  const pageOffset = (pagination.current - 1) * pagination.pageSize
  const num = pageOffset + index + 1
  return num.toString().padStart(3, '0')
}

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: string[]) => {
    selectedRowKeys.value = keys
  },
  onSelectAll: (selected: boolean, selectedRows: TestCase[], changeRows: TestCase[]) => {
    if (selected) {
      selectedRowKeys.value = [...new Set([...selectedRowKeys.value, ...testCases.value.map(c => c.id)])]
    } else {
      const currentPageIds = testCases.value.map(c => c.id)
      selectedRowKeys.value = selectedRowKeys.value.filter(id => !currentPageIds.includes(id))
    }
  }
}))

// 详情用例
const detailCaseVisible = ref(false)
const viewingCaseId = ref<string>('')

// 编辑用例
const editCaseVisible = ref(false)
const editingCaseId = ref<string>('')
const defaultModuleId = ref<string>('')  // 右键创建用例时的默认模块

// 导入对话框
const importModalVisible = ref(false)

// 存储所有用例（用于构建模块树中的用例节点）
const allCasesForTree = ref<any[]>([])

// 加载模块树
const loadModuleTree = async () => {
  if (!projectId.value) return
  try {
    // 先获取所有用例（用于在模块树中显示用例节点）
    const allCasesResponse = await testCaseApi.getTestCases(projectId.value, {
      page: 1,
      size: 9999  // 获取所有用例
    })
    allCasesForTree.value = allCasesResponse.items || []

    const response = await projectApi.getModules(projectId.value)
    // 新的响应格式包含 modules 和 totalCaseCount
    const moduleList = response.modules || response
    const totalCaseCount = response.totalCaseCount ?? allCasesForTree.value.length

    modules.value = moduleList
    const treeData = buildModuleTree(moduleList, allCasesForTree.value)

    // 添加"全部用例"节点，使用后端返回的总数
    moduleTreeData.value = [
      {
        title: '全部用例',
        key: 'all',
        count: totalCaseCount,
        isLeaf: true
      },
      ...treeData
    ]
    rebuildFlatModuleKeys()
  } catch (error) {
    console.error('Failed to load module tree:', error)
  }
}

const buildModuleTree = (modules: any[], allCases: any[]): any[] => {
  const treeMap = new Map()
  const treeData: any[] = []

  // 第一步：构建模块节点，使用后端返回的 caseCount
  modules.forEach(module => {
    treeMap.set(module.id, {
      title: module.name,
      key: module.id,
      directCount: module.caseCount || 0,  // 从后端获取的直接用例数
      count: 0,  // 总用例数（包含子模块），稍后计算
      isLeaf: false,
      nodeType: 'module',
      children: [],
      raw: module
    })
  })

  // 第二步：建立模块父子关系
  modules.forEach(module => {
    const node = treeMap.get(module.id)
    if (module.parentId && treeMap.has(module.parentId)) {
      treeMap.get(module.parentId).children.push(node)
    } else {
      treeData.push(node)
    }
  })

  // 第三步：将用例添加到对应模块下（用于树中显示用例节点）
  // 使用传入的 allCases 参数，而不是 testCases.value
  modules.forEach(module => {
    const moduleCases = allCases.filter(c => c.moduleId === module.id)
    const moduleNode = treeMap.get(module.id)

    moduleCases.forEach(tc => {
      moduleNode.children.push({
        title: tc.name,
        key: `case_${tc.id}`,
        isLeaf: true,
        nodeType: 'case',
        caseId: tc.id,
        caseCode: tc.caseCode,
        priority: tc.priority,
        raw: tc
      })
    })
  })

  // 第四步：递归计算每个模块的总用例数（包含所有子模块）
  const calculateTotalCount = (node: any): number => {
    let total = node.directCount || 0
    if (node.children) {
      node.children.forEach((child: any) => {
        if (child.nodeType === 'module') {
          total += calculateTotalCount(child)
        }
      })
    }
    node.count = total
    return total
  }

  treeData.forEach(node => calculateTotalCount(node))

  return treeData
}

const rebuildFlatModuleKeys = () => {
  const result: string[] = []
  const traverse = (nodes: any[]) => {
    nodes.forEach(node => {
      // 包含模块和用例节点，但排除虚拟节点
      if (node.key !== 'all' && node.key !== 'unplanned') {
        result.push(node.key)
      }
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(moduleTreeData.value)
  flatModuleKeys.value = result
}

// 获取模块及其所有子模块的 ID 列表
const getModuleAndChildrenIds = (moduleId: string): string[] => {
  const result: string[] = [moduleId]

  const findNode = (nodes: any[], targetId: string): any => {
    for (const node of nodes) {
      if (node.key === targetId) return node
      if (node.children && node.children.length > 0) {
        const found = findNode(node.children, targetId)
        if (found) return found
      }
    }
    return null
}

  const collectChildModuleIds = (node: any) => {
    if (!node.children) return
    node.children.forEach((child: any) => {
      if (child.nodeType === 'module') {
        result.push(child.key)
        collectChildModuleIds(child)
      }
    })
  }

  const targetNode = findNode(moduleTreeData.value, moduleId)
  if (targetNode) {
    collectChildModuleIds(targetNode)
  }

  return result
}

// 加载测试用例列表
const loadTestCases = async () => {
  if (!projectId.value) return

    loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      size: pagination.pageSize
    }

    if (searchValue.value) {
      params.search = searchValue.value
    }

    if (selectedModuleKeys.value[0] && selectedModuleKeys.value[0] !== 'all') {
      // 获取当前模块及其所有子模块的 ID
      const moduleIds = getModuleAndChildrenIds(selectedModuleKeys.value[0])
      params.moduleIds = moduleIds.join(',')  // 传递逗号分隔的模块 ID 列表
    }

    // 旧版筛选条件（兼容性）
    if (filters.level) {
      params.priority = filters.level
    }

    if (filters.executionResult) {
      params.status = filters.executionResult
    }

    // 高级筛选条件
    if (advancedFilters.value.length > 0) {
      console.log('应用高级筛选条件:', advancedFilters.value, '逻辑:', filterLogic.value)

      // 处理高级筛选条件
      advancedFilters.value.forEach((condition, index) => {
        const { field, operator, value } = condition
        console.log(`筛选条件 ${index + 1}:`, { field, operator, value })

        // 根据字段和操作符构建查询参数
        switch (field) {
          case 'id':
            if (operator === 'contains' && value) {
              // ID包含多个值，添加到搜索中
              params.search = params.search
                ? `${params.search} ${value}`
                : value
            } else if (operator === 'equals' && value) {
              params.search = params.search
                ? `${params.search} ${value}`
                : value
            }
            break
          case 'name':
            if (operator === 'contains' && value) {
              params.search = params.search
                ? `${params.search} ${value}`
                : value
            } else if (operator === 'equals' && value) {
              params.search = params.search
                ? `${params.search} ${value}`
                : value
            }
            break
          case 'moduleId':
            if (operator === 'belongs_to' && value) {
              const moduleIds = Array.isArray(value) ? value : [value]
              const allModuleIds: string[] = []
              moduleIds.forEach((id: string) => {
                allModuleIds.push(...getModuleAndChildrenIds(id))
              })
              // 如果使用 AND 逻辑，覆盖现有 moduleIds；如果使用 OR 逻辑，合并
              if (filterLogic.value === 'and') {
                params.moduleIds = [...new Set(allModuleIds)].join(',')
              } else {
                // OR 逻辑：合并到现有的moduleIds
                if (params.moduleIds) {
                  const existingIds = params.moduleIds.split(',')
                  params.moduleIds = [...new Set([...existingIds, ...allModuleIds])].join(',')
                } else {
                  params.moduleIds = [...new Set(allModuleIds)].join(',')
                }
              }
            } else if (operator === 'not_belongs_to' && value) {
              // 不属于某个模块的筛选需要后端支持，暂时跳过
              console.warn('not_belongs_to 操作符暂不支持')
            }
            break
          case 'priority':
            if (operator === 'equals' && value) {
              // AND 逻辑：如果已有 priority，需要后端支持多条件；OR 逻辑：取第一个
              if (filterLogic.value === 'and' && params.priority && params.priority !== value) {
                console.warn('AND 逻辑下多个 priority 条件冲突，使用最后一个')
              }
              params.priority = value
            } else if (operator === 'in' && Array.isArray(value) && value.length > 0) {
              // 多个优先级，取第一个（API可能不支持多值）
              params.priority = value[0]
            }
            break
          case 'type':
            if (operator === 'equals' && value) {
              if (filterLogic.value === 'and' && params.type && params.type !== value) {
                console.warn('AND 逻辑下多个 type 条件冲突，使用最后一个')
              }
              params.type = value
            }
            break
          case 'status':
            if (operator === 'equals' && value) {
              if (filterLogic.value === 'and' && params.status && params.status !== value) {
                console.warn('AND 逻辑下多个 status 条件冲突，使用最后一个')
              }
              params.status = value
            }
            break
          case 'isAutomated':
            if (operator === 'equals' && value !== undefined && value !== null) {
              params.is_automated = value === true || value === 'true'
            }
            break
          case 'tags':
            if (operator === 'contains' && value) {
              const tags = Array.isArray(value) ? value : [value]
              params.tags = tags.join(',')
            }
            break
          case 'requirementRef':
            if (operator === 'contains' && value) {
              params.requirement_ref = value
            } else if (operator === 'equals' && value) {
              params.requirement_ref = value
            }
            break
          case 'precondition':
            if (operator === 'contains' && value) {
              params.precondition = value
            }
            break
        }
      })

      console.log('筛选后的查询参数:', params)
    }

    console.log('调用 getTestCases API，参数:', params)
    const response = await testCaseApi.getTestCases(projectId.value, params)
    console.log('API 返回结果:', { total: response.total, itemsCount: response.items?.length })
    testCases.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('Failed to load test cases:', error)
    message.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

// 处理模块/用例选择（支持 Shift + 左键 批量选择）
const handleModuleSelect = (keys: string[], info: any) => {
  moduleContextMenu.visible = false
  const currentKey = info?.node?.key as string | undefined
  const currentNodeType = info?.node?.nodeType as string | undefined

  // 排除虚拟节点（'all'）不参与范围选择
  const isVirtualNode = currentKey === 'all'
  const lastKeyIsVirtual = lastSelectedModuleKey.value === 'all'

  // 如果按住了 Shift 键，且之前有选中的节点，且都不是虚拟节点，则进行范围选择
  if (isShiftKeyPressed.value && lastSelectedModuleKey.value && currentKey && !isVirtualNode && !lastKeyIsVirtual) {
    const flat = flatModuleKeys.value
    const startIndex = flat.indexOf(lastSelectedModuleKey.value)
    const endIndex = flat.indexOf(currentKey)
    if (startIndex !== -1 && endIndex !== -1) {
      const [start, end] =
        startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex]
      const rangeKeys = flat.slice(start, end + 1)
      // 合并到已选中的节点中
      selectedModuleKeys.value = Array.from(
        new Set([...selectedModuleKeys.value, ...rangeKeys])
      )
      // 更新最后选中的节点为当前节点
      lastSelectedModuleKey.value = currentKey
    } else {
      // 如果找不到范围，则只选中当前节点
      selectedModuleKeys.value = currentKey ? [currentKey] : []
      if (currentKey && !isVirtualNode) {
        lastSelectedModuleKey.value = currentKey
      }
    }
  } else {
    // 没有按 Shift，单选模式：只选中当前节点
    selectedModuleKeys.value = currentKey ? [currentKey] : []
    if (currentKey && !isVirtualNode) {
      lastSelectedModuleKey.value = currentKey
    }
  }

  // 只有选择模块或"全部用例"时才加载用例列表
  // 如果选择的是用例节点，不重新加载列表
  if (currentNodeType !== 'case') {
    pagination.current = 1
    loadTestCases()
  }
}

const handleModuleExpand = (keys: string[]) => {
  expandedModuleKeys.value = keys
}

const handleModuleSearch = () => {
  // 实现模块搜索逻辑
}

// 处理搜索
const handleSearch = () => {
  pagination.current = 1
  loadTestCases()
}

// 应用高级筛选
const handleFilterApply = (conditions: any[], logic: string) => {
  console.log('handleFilterApply 被调用:', { conditions, logic })
  advancedFilters.value = conditions
  filterLogic.value = logic as 'and' | 'or'
  console.log('设置筛选条件:', {
    advancedFilters: advancedFilters.value,
    filterLogic: filterLogic.value
  })
  pagination.current = 1
  loadTestCases()
}

// 重置筛选
const handleFilterReset = () => {
  advancedFilters.value = []
  filterLogic.value = 'and'
  filters.level = undefined
  filters.reviewResult = undefined
  filters.executionResult = undefined
  pagination.current = 1
  loadTestCases()
}

// 处理筛选（兼容旧代码）
const handleFilter = () => {
  pagination.current = 1
  loadTestCases()
}

const resetFilters = () => {
  filters.level = undefined
  filters.reviewResult = undefined
  filters.executionResult = undefined
  pagination.current = 1
  loadTestCases()
}

// 处理表格变化
const handleTableChange = (pag: any, filters: any, sorter: any) => {
  if (pag) {
    pagination.current = pag.current
    pagination.pageSize = pag.pageSize
  }
  loadTestCases()
}

// 处理分页变化
const handlePaginationChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
  loadTestCases()
}

// 创建用例
const handleCreateCase = () => {
  editingCaseId.value = ''
  defaultModuleId.value = ''  // 从工具栏创建时不设置默认模块
  editCaseVisible.value = true
}

// 编辑用例
const handleEditCase = (record: TestCase) => {
  editingCaseId.value = record.id
  editCaseVisible.value = true
}

// 查看用例（打开详情页面）
const handleViewCase = (record: TestCase) => {
  viewingCaseId.value = record.id
  detailCaseVisible.value = true
}

// 从详情页面跳转到编辑页面
const handleEditFromDetail = () => {
  detailCaseVisible.value = false
  editingCaseId.value = viewingCaseId.value
  editCaseVisible.value = true
}

// 保存用例
const handleSaveCase = async (caseData: any) => {
  editCaseVisible.value = false
  // 如果详情页面打开着，刷新详情数据
  if (detailCaseVisible.value && viewingCaseId.value === caseData.id) {
    // 详情组件会自动刷新
  }
  await loadTestCases()
  await loadModuleTree()
}

// 删除用例
const handleDeleteCase = async (record: TestCase) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用例"${record.name}"吗？`,
    onOk: async () => {
      try {
        await testCaseApi.deleteTestCase(projectId.value, record.id)
        message.success('删除成功')
        await loadTestCases()
        await loadModuleTree()
  } catch (error) {
    message.error('删除失败')
      }
    }
  })
}

// 复制用例
const handleCopyCase = async (record: TestCase) => {
  try {
    const originalCase = await testCaseApi.getTestCase(projectId.value, record.id)
    // 后端期望 snake_case 字段名
    const newCaseData: any = {
      name: `${originalCase.name} (副本)`,
      type: originalCase.type,
      priority: originalCase.priority,
      precondition: originalCase.precondition,
      steps: originalCase.steps,
      expected_result: originalCase.expectedResult,  // snake_case
      requirement_ref: originalCase.requirementRef,  // snake_case
      module_path: originalCase.modulePath,          // snake_case
      module_id: originalCase.moduleId,              // snake_case
      executor_id: originalCase.executorId,          // snake_case
      tags: originalCase.tags,
      level: originalCase.level,
    }
    // 不复制ID、创建时间、更新时间、创建人、更新人、case_code（让后端自动生成）

    await testCaseApi.createTestCase(projectId.value, newCaseData)
    message.success('复制成功')
    await loadTestCases()
    await loadModuleTree()
  } catch (error) {
    console.error('复制用例失败:', error)
    message.error('复制失败')
  }
}

// 执行用例
const handleExecuteCase = (record: TestCase) => {
  message.info('执行功能开发中...')
}

// 导入
const handleImport = () => {
  importModalVisible.value = true
}

const handleImportSuccess = async (result: any) => {
  message.success(`导入完成：新增 ${result.created} 条，更新 ${result.updated} 条`)
  await loadTestCases()
  await loadModuleTree()
}

// 批量操作
const handleExport = async ({ key }: { key: string }) => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  if (key === 'excel') {
    try {
      // 获取当前选中的模块
      const selectedModule = selectedModuleKeys.value[0]

      // 构建导出参数
      const exportParams: any = {}

      // 如果选中的是模块（不是"全部用例"），则传递模块ID
      if (selectedModule && selectedModule !== 'all') {
        // 获取当前模块及其所有子模块的 ID
        const moduleIds = getModuleAndChildrenIds(selectedModule)
        exportParams.moduleIds = moduleIds.join(',')
      }
      // 如果选中的是"全部用例"，则不传递 moduleIds，导出全部用例

      // 应用当前的筛选条件
      if (filters.level) {
        exportParams.priority = filters.level
      }
      if (filters.executionResult) {
        exportParams.status = filters.executionResult
      }

      // 显示加载提示
      const hide = message.loading('正在导出，请稍候...', 0)

      try {
        // 调用导出API
        const blob = await testCaseApi.exportCases(projectId.value, exportParams)

        // 创建下载链接
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url

        // 生成文件名
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')
        const moduleName = selectedModule && selectedModule !== 'all'
          ? (findModuleById(selectedModule)?.name || '模块')
          : '全部用例'
        link.download = `测试用例_${moduleName}_${timestamp}.xlsx`

        // 触发下载
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        message.success('导出成功')
      } finally {
        hide()
      }
    } catch (error) {
      console.error('导出失败:', error)
      message.error('导出失败，请稍后重试')
    }
  } else if (key === 'xmind') {
    message.info('导出思维导图功能开发中...')
  }
}

const handleBatchEdit = () => {
  if (selectedRowKeys.value.length === 1) {
    const case_ = testCases.value.find(c => c.id === selectedRowKeys.value[0])
    if (case_) {
      handleEditCase(case_)
    }
  } else {
    message.info('请选择单个用例进行编辑')
  }
}

const handleBatchMove = () => {
  message.info('批量移动功能开发中...')
}

const handleBatchCopy = () => {
  message.info('批量复制功能开发中...')
}

const handleBatchDelete = () => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedRowKeys.value.length} 个用例吗？`,
    onOk: async () => {
      try {
        await Promise.all(
          selectedRowKeys.value.map(id =>
            testCaseApi.deleteTestCase(projectId.value, id)
          )
        )
        message.success('批量删除成功')
        selectedRowKeys.value = []
        await loadTestCases()
        await loadModuleTree()
  } catch (error) {
        message.error('批量删除失败')
      }
    }
  })
}

const clearSelection = () => {
  selectedRowKeys.value = []
}

// 模块树右键菜单与拖拽
const hideModuleContextMenu = () => {
  moduleContextMenu.visible = false
}

const handleModuleRightClick = (info: any) => {
  const { event, node } = info
  event.preventDefault()

  // 使用 clientX/clientY 配合 fixed 定位，确保菜单显示在鼠标右侧
  const menuWidth = 150  // 菜单预估宽度
  const menuHeight = 200 // 菜单预估高度

  // 检查是否会超出屏幕边界
  let x = event.clientX
  let y = event.clientY

  // 如果菜单会超出右边界，则显示在鼠标左侧
  if (x + menuWidth > window.innerWidth) {
    x = x - menuWidth
  }

  // 如果菜单会超出下边界，则向上调整
  if (y + menuHeight > window.innerHeight) {
    y = window.innerHeight - menuHeight - 10
  }

  moduleContextMenu.visible = true
  moduleContextMenu.x = x
  moduleContextMenu.y = y
  moduleContextMenu.node = node

  const key = node.key as string
  if (!selectedModuleKeys.value.includes(key)) {
    selectedModuleKeys.value = [key]
    lastSelectedModuleKey.value = key
  }
}

const allowModuleDrop = (options: any) => {
  const dropKey = options.dropNode?.key
  return dropKey !== 'all' && dropKey !== 'unplanned'
}

const findModuleById = (id: string) => {
  return modules.value.find(m => m.id === id)
}

const getNextSortOrder = (parentId?: string) => {
  const siblings = modules.value.filter(m => m.parentId === parentId)
  if (!siblings.length) return 1
  const maxOrder = Math.max(
    ...siblings.map(s => (typeof s.sortOrder === 'number' ? s.sortOrder : 0))
  )
  return maxOrder + 1
}

const handleModuleDrop = async (info: any) => {
  const dragKey = info.dragNode?.key as string
  const dropKey = info.node?.key as string

  if (!projectId.value || !dragKey || !dropKey) return
  if (dragKey === 'all') return
  if (dropKey === 'all') return

  // 判断是否是用例节点（key 以 case_ 开头）
  const isDragCase = dragKey.startsWith('case_')
  const isDropCase = dropKey.startsWith('case_')

  if (isDragCase) {
    // 拖动的是用例，需要移动到目标模块
    const caseId = dragKey.replace('case_', '')
    let targetModuleId: string | null = null

    if (isDropCase) {
      // 放到另一个用例上，获取该用例的模块 ID
      const dropCaseId = dropKey.replace('case_', '')
      const dropCase = testCases.value.find(c => c.id === dropCaseId)
      targetModuleId = dropCase?.moduleId || null
    } else {
      // 放到模块上
      targetModuleId = dropKey
    }

    try {
      // 更新用例的 module_id
      await testCaseApi.updateTestCase(projectId.value, caseId, {
        module_id: targetModuleId
      })
      message.success('用例已移动')

      // 自动展开目标模块
      if (targetModuleId && !expandedModuleKeys.value.includes(targetModuleId)) {
        expandedModuleKeys.value = [...expandedModuleKeys.value, targetModuleId]
      }

      await loadTestCases()
      await loadModuleTree()
    } catch (error) {
      console.error('Failed to move test case:', error)
      message.error('移动用例失败')
    }
  } else {
    // 拖动的是模块
    const dragModule = findModuleById(dragKey)
    if (!dragModule) return

    let newParentId: string | undefined
    if (info.dropToGap) {
      // 落在两个节点之间，保持与目标节点相同的父级
      const dropModule = findModuleById(dropKey)
      newParentId = dropModule?.parentId
    } else {
      // 落在节点上，变为该节点的子模块
      // 如果目标是用例，则获取用例的模块作为新父级
      if (isDropCase) {
        const dropCaseId = dropKey.replace('case_', '')
        const dropCase = testCases.value.find(c => c.id === dropCaseId)
        newParentId = dropCase?.moduleId
      } else {
        newParentId = dropKey
      }
    }

    try {
      await projectApi.updateModule(projectId.value, dragKey, {
        name: dragModule.name,
        parentId: newParentId,
        sortOrder: dragModule.sortOrder ?? 1,
        description: dragModule.description
      })
      message.success('模块已移动')

      // 自动展开新的父模块
      if (newParentId && !expandedModuleKeys.value.includes(newParentId)) {
        expandedModuleKeys.value = [...expandedModuleKeys.value, newParentId]
      }

      // 刷新用例和模块树以更新用例数量
      await loadTestCases()
      await loadModuleTree()
    } catch (error) {
      console.error('Failed to move module:', error)
      message.error('移动模块失败')
    }
  }
}

const handleModuleContextMenuClick = ({ key }: { key: string }) => {
  const node = moduleContextMenu.node
  moduleContextMenu.visible = false
  if (!node) return

  if (key === 'addModule') {
    handleAddModule(node)
  } else if (key === 'addCase') {
    handleAddCase(node)
  } else if (key === 'rename') {
    handleRenameModule(node)
  } else if (key === 'delete') {
    handleDeleteModule(node)
  } else if (key === 'batchDelete') {
    handleBatchDeleteModules()
  } else if (key === 'deleteCase') {
    handleDeleteCaseFromTree(node)
  } else if (key === 'export') {
    handleExportFromTree(node)
  }
}

// 从树节点删除用例
const handleDeleteCaseFromTree = (node: any) => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  // 从 key 中提取用例 ID（格式：case_xxx）
  const nodeKey = node.key as string
  const caseId = nodeKey.replace('case_', '')
  const caseName = node.title || '该用例'

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除用例"${caseName}"吗？`,
    onOk: async () => {
      try {
        await testCaseApi.deleteTestCase(projectId.value!, caseId)
        message.success('删除成功')
        await loadTestCases()
        await loadModuleTree()
      } catch (error) {
        console.error('Failed to delete case:', error)
        message.error('删除失败')
      }
    }
  })
}

const handleAddModule = (node: any) => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  const parentKey = node.key as string
  const isSpecial = parentKey === 'all' || parentKey === 'unplanned'
  const parentId = isSpecial ? undefined : parentKey
  let inputValue = '新模块'

  Modal.confirm({
    title: '新建模块',
    content: createVNode(Input, {
      defaultValue: inputValue,
      onChange: (e: any) => {
        inputValue = e.target.value
      }
    }),
    async onOk() {
      const name = (inputValue || '').trim()
      if (!name) {
        message.warning('模块名称不能为空')
        return Promise.reject()
      }
      try {
        await projectApi.createModule(projectId.value!, {
          name,
          parentId,
          sortOrder: getNextSortOrder(parentId),
          description: ''
        })
  message.success('模块创建成功')
        await loadModuleTree()
      } catch (error) {
        console.error('Failed to create module:', error)
        message.error('模块创建失败')
        return Promise.reject()
      }
    }
  })
}

const handleAddCase = (node: any) => {
  // 右键新增用例：直接打开用例编辑弹窗，自动关联到选中的模块
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  editingCaseId.value = ''

  // 设置默认模块ID（如果不是虚拟节点）
  const nodeKey = node?.key as string
  if (nodeKey && nodeKey !== 'all' && nodeKey !== 'unplanned') {
    defaultModuleId.value = nodeKey
  } else {
    defaultModuleId.value = ''
  }

  editCaseVisible.value = true
}

const handleRenameModule = (node: any) => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  const key = node.key as string
  if (key === 'all' || key === 'unplanned') {
    message.warning('该节点不支持重命名')
    return
  }

  const module = findModuleById(key)
  if (!module) return

  let inputValue = module.name

  Modal.confirm({
    title: '重命名模块',
    content: createVNode(Input, {
      defaultValue: inputValue,
      onChange: (e: any) => {
        inputValue = e.target.value
      }
    }),
    async onOk() {
      const name = (inputValue || '').trim()
      if (!name) {
        message.warning('模块名称不能为空')
        return Promise.reject()
      }
      try {
        await projectApi.updateModule(projectId.value!, key, {
          name,
          parentId: module.parentId,
          sortOrder: module.sortOrder ?? 1,
          description: module.description
        })
        message.success('重命名成功')
        await loadModuleTree()
      } catch (error) {
        console.error('Failed to rename module:', error)
        message.error('重命名失败')
        return Promise.reject()
      }
    }
  })
}

const handleDeleteModule = (node: any) => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  const key = node.key as string
  if (key === 'all' || key === 'unplanned') {
    message.warning('该节点不支持删除')
    return
  }

  Modal.confirm({
    title: '确认删除',
    content: '删除模块将同时影响其下用例，确定要删除该模块吗？',
    async onOk() {
      try {
        await projectApi.deleteModule(projectId.value!, key)
        message.success('删除模块成功')
        await loadModuleTree()
        await loadTestCases()
      } catch (error) {
        console.error('Failed to delete module:', error)
        message.error('删除模块失败')
        return Promise.reject()
      }
    }
  })
}

const handleBatchDeleteModules = () => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }
  const keys = selectedModuleKeys.value.filter(
    k => k !== 'all' && k !== 'unplanned'
  )
  if (keys.length === 0) {
    message.info('请选择要删除的模块')
    return
  }

  Modal.confirm({
    title: '批量删除模块',
    content: `确定要删除选中的 ${keys.length} 个模块吗？`,
    async onOk() {
      try {
        await Promise.all(
          keys.map(id => projectApi.deleteModule(projectId.value!, id))
        )
        message.success('批量删除模块成功')
        selectedModuleKeys.value = ['all']
        await loadModuleTree()
        await loadTestCases()
      } catch (error) {
        console.error('Failed to batch delete modules:', error)
        message.error('批量删除模块失败')
        return Promise.reject()
      }
    }
  })
}

// 从模块树右键菜单导出
const handleExportFromTree = async (node: any) => {
  if (!projectId.value) {
    message.warning('请先选择项目')
    return
  }

  try {
    const nodeKey = node.key as string

    // 构建导出参数
    const exportParams: any = {}

    // 如果选中的是模块（不是"全部用例"），则传递模块ID
    if (nodeKey && nodeKey !== 'all') {
      // 获取当前模块及其所有子模块的 ID
      const moduleIds = getModuleAndChildrenIds(nodeKey)
      exportParams.moduleIds = moduleIds.join(',')
    }
    // 如果选中的是"全部用例"，则不传递 moduleIds，导出全部用例

    // 显示加载提示
    const hide = message.loading('正在导出，请稍候...', 0)

    try {
      // 调用导出API
      const blob = await testCaseApi.exportCases(projectId.value, exportParams)

      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // 生成文件名
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')
      const moduleName = nodeKey && nodeKey !== 'all'
        ? (node.title || findModuleById(nodeKey)?.name || '模块')
        : '全部用例'
      link.download = `测试用例_${moduleName}_${timestamp}.xlsx`

      // 触发下载
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      message.success('导出成功')
    } finally {
      hide()
    }
  } catch (error) {
    console.error('导出失败:', error)
    message.error('导出失败，请稍后重试')
  }
}

// 工具函数
const getLevelColor = (level: string) => {
  const colors: Record<string, string> = {
    P0: 'red',
    P1: 'orange',
    P2: 'blue',
    P3: 'green'
  }
  return colors[level] || 'default'
}

const getReviewResultColor = (result: string) => {
  const colors: Record<string, string> = {
    not_reviewed: 'default',
    passed: 'green',
    rejected: 'red',
    resubmit: 'orange'
  }
  return colors[result] || 'default'
}

const getReviewResultLabel = (result: string) => {
  const labels: Record<string, string> = {
    not_reviewed: '未评审',
    passed: '已通过',
    rejected: '不通过',
    resubmit: '重新提审'
  }
  return labels[result] || result
}

const getExecutionResultColor = (status: string) => {
  const colors: Record<string, string> = {
    not_executed: 'default',
    passed: 'green',
    failed: 'red',
    blocked: 'orange',
    skipped: 'gray'
  }
  return colors[status] || 'default'
}

const getExecutionResultLabel = (status: string) => {
  const labels: Record<string, string> = {
    not_executed: '未执行',
    passed: '成功',
    failed: '失败',
    blocked: '阻塞',
    skipped: '跳过'
  }
  return labels[status] || status
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD')
}

// 格式化日期时间（包含时分秒）
const formatDateTime = (date: string) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 获取显示名称（将用户ID转换为显示名称）
const getDisplayName = (userId: string) => {
  if (!userId) return '-'
  // 如果是当前登录用户，显示当前用户名
  if (userStore.user?.id === userId) {
    return userStore.user.username || userStore.user.email || '当前用户'
  }
  // 其他情况显示简短ID或默认名称
  return userId.length > 8 ? userId.substring(0, 8) + '...' : userId
}

// 根据模块ID获取模块名称
const getModuleName = (moduleId: string | null | undefined): string => {
  if (!moduleId) return ''
  const module = findModuleById(moduleId)
  if (module) {
    return module.name
  }
  return ''
}

// 生命周期
watch(
  () => projectId.value,
  () => {
    if (projectId.value) {
      loadTestCases()
      loadModuleTree()
      loadFilterFields()
    }
  },
  { immediate: true }
)

// 键盘事件处理函数
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Shift') {
    isShiftKeyPressed.value = true
  }
}

const handleKeyUp = (e: KeyboardEvent) => {
  if (e.key === 'Shift') {
    isShiftKeyPressed.value = false
  }
}

onMounted(async () => {
  // 确保项目列表已加载
  if (projects.value.length === 0) {
    await projectStore.fetchProjects()
  }
  // 如果没有当前项目，设置第一个项目为当前项目
  if (!projectStore.currentProject && projects.value.length > 0) {
    projectStore.setCurrentProject(projects.value[0])
  }
  if (projectId.value) {
    loadTestCases()
    loadModuleTree()
    loadFilterFields()
  }
  // 添加全局键盘事件监听器
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  // 移除全局键盘事件监听器
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
})
</script>

<style scoped>
.test-cases-container {
  height: 100%;
  background: #f5f5f5;
  }

.test-cases-layout {
  height: 100%;
}

.module-tree-sider {
  background: #fff;
  border-right: 1px solid #f0f0f0;
    padding: 16px;
  overflow-y: auto;
  }

.module-search {
  margin-bottom: 16px;
}

.count-badge {
  color: #999;
  font-size: 12px;
  }

/* 树节点标题样式 - 单行显示 */
.tree-node-title {
  display: inline-block;
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
  text-align: left;
  }

/* 树容器横向滚动 */
.module-tree-sider :deep(.ant-tree) {
  overflow-x: auto;
  white-space: nowrap;
}

.module-tree-sider :deep(.ant-tree-treenode) {
  white-space: nowrap;
  display: flex !important;
  align-items: center;
}

.module-tree-sider :deep(.ant-tree-node-content-wrapper) {
  display: inline-flex !important;
  align-items: center;
  flex: 1;
  min-width: 0;
  }

/* 用例节点样式 */
.module-tree-sider :deep(.ant-tree-title) {
  display: inline-block;
  text-align: left;
  width: 100%;
  }

/* 右键菜单样式 - Windows 风格 */
.module-context-menu {
  position: fixed;
  z-index: 1000;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  box-shadow: 0 3px 6px -4px rgba(0, 0, 0, 0.12),
              0 6px 16px 0 rgba(0, 0, 0, 0.08),
              0 9px 28px 8px rgba(0, 0, 0, 0.05);
  padding: 4px 0;
  min-width: 140px;
  }

.module-context-menu :deep(.ant-menu) {
  border: none;
  box-shadow: none;
  background: transparent;
  }

.module-context-menu :deep(.ant-menu-item) {
  height: 32px;
  line-height: 32px;
  margin: 0 !important;
  padding: 0 12px !important;
  border-radius: 0;
  }

.module-context-menu :deep(.ant-menu-item:hover) {
  background-color: #f5f5f5;
  }

.module-context-menu :deep(.ant-menu-item-divider) {
  margin: 4px 0;
  background-color: #f0f0f0;
}

.cases-content {
  display: flex;
  flex-direction: column;
  background: #fff;
  margin: 0;
  overflow: hidden;
  height: 100%;
}

/* 固定顶部工具栏 */
.fixed-toolbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  padding: 16px;
  flex-shrink: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
}

.toolbar .ant-btn {
  flex-shrink: 0;
  white-space: nowrap;
}

.toolbar .ant-input-search {
  flex-shrink: 0;
}

.toolbar .ant-select {
  flex-shrink: 0;
}

.toolbar .ant-popover {
  flex-shrink: 0;
}

/* 可滚动表格内容区域 */
.scrollable-table-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}

.filter-panel {
  margin-bottom: 16px;
  }

.table-card {
  margin-bottom: 16px;
  }

/* 表格单行显示，不换行 */
.table-card :deep(.ant-table-cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 用例链接样式 */
.case-link {
  color: #1890ff;
  cursor: pointer;
  }

.case-link:hover {
  text-decoration: underline;
}

.batch-actions {
  display: flex;
  align-items: center;
}

/* 固定底部分页器和批量操作栏 */
.fixed-footer {
  position: sticky;
  bottom: 0;
  z-index: 100;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  padding: 12px 16px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .module-tree-sider {
    width: 200px;
  }
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar > * {
    width: 100%;
  }
}

/* 修复表格固定列重叠问题 */
:deep(.ant-table-cell-fix-right),
:deep(.ant-table-cell-fix-left) {
  background: #fff !important;
  z-index: 10 !important;
}

:deep(.ant-table-thead > tr > th.ant-table-cell-fix-right),
:deep(.ant-table-thead > tr > th.ant-table-cell-fix-left) {
  background: #fafafa !important;
  z-index: 20 !important;
}

:deep(.ant-table-tbody > tr:hover > td.ant-table-cell-fix-right),
:deep(.ant-table-tbody > tr:hover > td.ant-table-cell-fix-left) {
  background: #fafafa !important;
}
</style>
