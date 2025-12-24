<template>
  <div class="test-cases-container" @click="hideModuleContextMenu">
    <!-- 顶部项目选择器（示例项目下拉） -->
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
          <template #title="{ title, count, nodeType, caseCode }">
            <span>
              {{ title }}
              <span v-if="count !== undefined && nodeType !== 'case'" class="count-badge">({{ count }})</span>
              <span v-if="caseCode" class="case-code-badge">{{ caseCode }}</span>
            </span>
          </template>
          <template #icon="{ nodeType, isLeaf }">
            <FolderOutlined v-if="nodeType === 'module'" />
            <FileTextOutlined v-else-if="nodeType === 'case'" style="color: #1890ff" />
            <FileOutlined v-else-if="isLeaf" />
            <FolderOutlined v-else />
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
            </template>
            <!-- 模块节点显示全部操作 -->
            <template v-else-if="contextMenuNodeType === 'module'">
              <a-menu-item key="addModule">新增子模块</a-menu-item>
              <a-menu-item key="addCase">新增用例</a-menu-item>
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
        <!-- 顶部工具栏 -->
        <div class="toolbar">
          <a-space>
            <a-button type="primary" @click="handleCreateCase">
              <template #icon><PlusOutlined /></template>
              新建
            </a-button>
            <a-button @click="handleImport">
              <template #icon><ImportOutlined /></template>
              导入
            </a-button>
          </a-space>
          
          <a-space>
            <a-input-search
              v-model:value="searchValue"
              placeholder="通过ID/名称/标签搜索"
              style="width: 300px"
              @search="handleSearch"
              allow-clear
            />
            <a-select
              v-model:value="viewMode"
              style="width: 120px"
            >
              <a-select-option value="all">全部数据</a-select-option>
              <a-select-option value="my">我的数据</a-select-option>
            </a-select>
            <a-button @click="showFilterPanel = !showFilterPanel">
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
          </a-space>
        </div>

        <!-- 筛选面板 -->
        <a-card v-if="showFilterPanel" size="small" class="filter-panel">
          <a-row :gutter="16">
            <a-col :span="6">
              <a-select
                v-model:value="filters.level"
                placeholder="用例等级"
                style="width: 100%"
                allow-clear
              >
                <a-select-option value="P0">P0</a-select-option>
                <a-select-option value="P1">P1</a-select-option>
                <a-select-option value="P2">P2</a-select-option>
                <a-select-option value="P3">P3</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="6">
              <a-select
                v-model:value="filters.reviewResult"
                placeholder="评审结果"
                style="width: 100%"
                allow-clear
              >
                <a-select-option value="not_reviewed">未评审</a-select-option>
                <a-select-option value="passed">已通过</a-select-option>
                <a-select-option value="rejected">不通过</a-select-option>
                <a-select-option value="resubmit">重新提审</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="6">
              <a-select
                v-model:value="filters.executionResult"
                placeholder="执行结果"
                style="width: 100%"
                allow-clear
              >
                <a-select-option value="not_executed">未执行</a-select-option>
                <a-select-option value="passed">成功</a-select-option>
                <a-select-option value="failed">失败</a-select-option>
                <a-select-option value="blocked">阻塞</a-select-option>
                <a-select-option value="skipped">跳过</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="6">
              <a-space>
                <a-button @click="handleFilter">应用</a-button>
                <a-button @click="resetFilters">重置</a-button>
              </a-space>
            </a-col>
          </a-row>
        </a-card>

        <!-- 表格 -->
        <a-card class="table-card">
          <a-table
            :columns="columns"
            :data-source="testCases"
            :loading="loading"
            :row-selection="rowSelection"
            :pagination="pagination"
            :row-key="record => record.id"
            @change="handleTableChange"
            size="middle"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'id'">
                {{ record.id }}
              </template>
              
              <template v-else-if="column.key === 'name'">
                <a @click="handleViewCase(record)">{{ record.name }}</a>
              </template>
              
              <template v-else-if="column.key === 'level'">
                <a-tag :color="getLevelColor(record.priority)">
                  {{ record.priority }}
                </a-tag>
              </template>
              
              <template v-else-if="column.key === 'reviewResult'">
                <a-tag :color="getReviewResultColor((record as any).reviewResult || 'not_reviewed')">
                  {{ getReviewResultLabel((record as any).reviewResult || 'not_reviewed') }}
                </a-tag>
              </template>
              
              <template v-else-if="column.key === 'executionResult'">
                <a-tag :color="getExecutionResultColor(record.status)">
                  {{ getExecutionResultLabel(record.status) }}
                </a-tag>
              </template>
              
              <template v-else-if="column.key === 'modulePath'">
                {{ record.modulePath || (record.moduleId ? '' : '未规划用例') }}
              </template>
              
              <template v-else-if="column.key === 'tags'">
                <a-space>
                  <a-tag v-for="tag in (record.tags || []).slice(0, 2)" :key="tag" size="small">
                    {{ tag }}
                  </a-tag>
                  <a-tag v-if="(record.tags || []).length > 2" size="small" color="default">
                    +{{ (record.tags || []).length - 2 }}
                  </a-tag>
                </a-space>
              </template>
              
              <template v-else-if="column.key === 'updatedBy'">
                {{ record.updatedBy || record.createdBy || 'Administrator' }}
              </template>
              
              <template v-else-if="column.key === 'updatedAt'">
                {{ formatDate(record.updatedAt) }}
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
        
        <!-- 底部批量操作栏 -->
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
      </a-layout-content>
    </a-layout>

    <!-- 编辑用例对话框 -->
    <a-modal
      v-model:visible="editCaseVisible"
      :title="editingCaseId ? '编辑用例' : '新建用例'"
      width="90%"
      :footer="null"
      :mask-closable="false"
      destroy-on-close
    >
            <TestCaseEdit
        :case-id="editingCaseId"
              :project-id="projectId"
              :default-module-id="defaultModuleId"
              @save="handleSaveCase"
        @cancel="editCaseVisible = false"
      />
    </a-modal>
    
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
  FileTextOutlined
} from '@ant-design/icons-vue'
import TestCaseEdit from '@/components/TestCase/TestCaseEdit.vue'
import ImportCasesModal from '@/components/TestCase/ImportCasesModal.vue'
import { testCaseApi } from '@/api/testCase'
import { projectApi } from '@/api/project'
import { useProjectStore } from '@/stores/project'
import type { TestCase, Project } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 当前项目 ID：优先使用 store，其次使用已有项目列表的第一个
const projects = computed<Project[]>(() => projectStore.projects)
const projectId = computed<string | undefined>(() => {
  if (projectStore.currentProject) {
    return projectStore.currentProject.id
  }
  return projects.value[0]?.id
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

// 右侧表格
const loading = ref(false)
const testCases = ref<TestCase[]>([])
const selectedRowKeys = ref<string[]>([])
const searchValue = ref('')
const viewMode = ref('all')
const viewLayout = ref<'list' | 'grid'>('list')
const showFilterPanel = ref(false)

// 筛选条件
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

// 表格列定义
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 100,
    sorter: true
  },
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    sorter: true
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
    ]
  },
  {
    title: '评审结果',
    dataIndex: 'reviewResult',
    key: 'reviewResult',
    width: 120,
    filters: [
      { text: '未评审', value: 'not_reviewed' },
      { text: '已通过', value: 'passed' },
      { text: '不通过', value: 'rejected' },
      { text: '重新提审', value: 'resubmit' }
    ]
  },
  {
    title: '执行结果',
    dataIndex: 'status',
    key: 'executionResult',
    width: 120,
    filters: [
      { text: '未执行', value: 'not_executed' },
      { text: '成功', value: 'passed' },
      { text: '失败', value: 'failed' },
      { text: '阻塞', value: 'blocked' },
      { text: '跳过', value: 'skipped' }
    ]
  },
  {
    title: '所属模块',
    dataIndex: 'modulePath',
    key: 'modulePath',
    width: 200
  },
  {
    title: '标签',
    dataIndex: 'tags',
    key: 'tags',
    width: 150
  },
  {
    title: '更新人',
    dataIndex: 'updatedBy',
    key: 'updatedBy',
    width: 120
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    width: 150,
    sorter: true
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right' as const
  }
]

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

// 编辑用例
const editCaseVisible = ref(false)
const editingCaseId = ref<string>('')
const defaultModuleId = ref<string>('')  // 右键创建用例时的默认模块

// 导入对话框
const importModalVisible = ref(false)

// 加载模块树
const loadModuleTree = async () => {
  if (!projectId.value) return
  try {
    const response = await projectApi.getModules(projectId.value)
    modules.value = response
    const treeData = buildModuleTree(response)
    
    // 添加"全部用例"节点
    const allCasesCount = testCases.value.length
    
    moduleTreeData.value = [
      {
        title: '全部用例',
        key: 'all',
        count: allCasesCount,
        isLeaf: true
      },
      ...treeData
    ]
    rebuildFlatModuleKeys()
  } catch (error) {
    console.error('Failed to load module tree:', error)
  }
}

const buildModuleTree = (modules: any[]): any[] => {
  const treeMap = new Map()
  const treeData: any[] = []

  // 第一步：构建模块节点
  modules.forEach(module => {
    const moduleCases = testCases.value.filter(c => c.moduleId === module.id)
    treeMap.set(module.id, {
      title: module.name,
      key: module.id,
      count: moduleCases.length,
      isLeaf: false,
      nodeType: 'module',  // 标识节点类型
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

  // 第三步：将用例添加到对应模块下
  modules.forEach(module => {
    const moduleCases = testCases.value.filter(c => c.moduleId === module.id)
    const moduleNode = treeMap.get(module.id)
    
    moduleCases.forEach(tc => {
      moduleNode.children.push({
        title: tc.name,
        key: `case_${tc.id}`,  // 用例key加前缀区分
        isLeaf: true,
        nodeType: 'case',  // 标识节点类型
        caseId: tc.id,
        caseCode: tc.caseCode,
        priority: tc.priority,
        raw: tc
      })
    })
  })

  return treeData
}

const rebuildFlatModuleKeys = () => {
  const result: string[] = []
  const traverse = (nodes: any[]) => {
    nodes.forEach(node => {
      if (node.key !== 'all' && node.key !== 'unplanned' && node.nodeType === 'module') {
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
    
    if (filters.level) {
      params.priority = filters.level
    }
    
    if (filters.executionResult) {
      params.status = filters.executionResult
    }

    const response = await testCaseApi.getTestCases(projectId.value, params)
    testCases.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('Failed to load test cases:', error)
    message.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

// 处理模块选择（支持 Shift + 左键 批量选择）
const handleModuleSelect = (keys: string[], info: any) => {
  moduleContextMenu.visible = false
  const currentKey = info?.node?.key as string | undefined

  // 排除虚拟节点（'all' 和 'unplanned'）不参与范围选择
  const isVirtualNode = currentKey === 'all' || currentKey === 'unplanned'
  const lastKeyIsVirtual = lastSelectedModuleKey.value === 'all' || lastSelectedModuleKey.value === 'unplanned'

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

  pagination.current = 1
  loadTestCases()
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

// 处理筛选
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

// 查看用例
const handleViewCase = (record: TestCase) => {
  editingCaseId.value = record.id
  editCaseVisible.value = true
}

// 保存用例
const handleSaveCase = async (caseData: any) => {
  editCaseVisible.value = false
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
const handleExport = ({ key }: { key: string }) => {
  if (key === 'excel') {
    message.info('导出Excel功能开发中...')
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
  moduleContextMenu.visible = true
  moduleContextMenu.x = event.pageX
  moduleContextMenu.y = event.pageY
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
  if (dragKey === 'all' || dragKey === 'unplanned') return
  if (dropKey === 'all' || dropKey === 'unplanned') return

  const dragModule = findModuleById(dragKey)
  if (!dragModule) return

  let newParentId: string | undefined
  if (info.dropToGap) {
    // 落在两个节点之间，保持与目标节点相同的父级
    const dropModule = findModuleById(dropKey)
    newParentId = dropModule?.parentId
  } else {
    // 落在节点上，变为该节点的子模块
    newParentId = dropKey
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
    
    await loadModuleTree()
  } catch (error) {
    console.error('Failed to move module:', error)
    message.error('移动模块失败')
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
  return dayjs(date).format('YYYY-MM-DD')
}

// 生命周期
watch(
  () => projectId.value,
  () => {
    if (projectId.value) {
      loadTestCases()
      loadModuleTree()
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

onMounted(() => {
  if (projectId.value) {
    loadTestCases()
    loadModuleTree()
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

  .cases-content {
  background: #fff;
  margin: 0;
  padding: 16px;
  overflow-y: auto;
  }
  
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  }
  
.filter-panel {
  margin-bottom: 16px;
  }
  
.table-card {
  margin-bottom: 16px;
  }
  
.batch-actions {
  position: sticky;
  bottom: 0;
  background: #fff;
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
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
</style>
