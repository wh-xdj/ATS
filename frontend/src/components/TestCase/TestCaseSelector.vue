<template>
  <a-modal
    v-model:visible="innerVisible"
    title="选择测试用例"
    width="1100px"
    @cancel="handleCancel"
    @ok="handleConfirm"
    okText="确认选择"
    cancelText="取消"
  >
    <div class="test-case-selector">
      <a-row :gutter="16">
        <!-- 左侧：模块树 -->
        <a-col :span="6">
          <a-card size="small" class="module-tree-card" title="用例模块">
            <a-spin :spinning="loadingModules">
              <a-input-search
                v-model:value="moduleSearchValue"
                placeholder="搜索模块"
                style="margin-bottom: 12px"
                allow-clear
              />
              <div class="module-tree-wrapper">
                <a-tree
                  :tree-data="filteredModuleTree"
                  :selected-keys="selectedModuleKeys"
                  :expanded-keys="expandedModuleKeys"
                  :show-icon="true"
                  @select="handleModuleSelect"
                  @expand="handleModuleExpand"
                  block-node
                >
                  <template #icon>
                    <FolderOutlined style="color: #faad14" />
                  </template>
                  <template #title="{ title, caseCount }">
                    <span class="module-title">
                      {{ title }}
                      <span class="case-count">({{ caseCount || 0 }})</span>
                    </span>
                  </template>
                </a-tree>
              </div>
            </a-spin>
          </a-card>
        </a-col>

        <!-- 右侧：用例列表 -->
        <a-col :span="18">
          <!-- 搜索和筛选 -->
          <a-card size="small" class="filter-card">
            <a-row :gutter="12" align="middle">
              <a-col :span="8">
                <a-input-search
                  v-model:value="searchKeyword"
                  placeholder="搜索用例名称"
                  @search="handleSearch"
                  allow-clear
                />
              </a-col>
              <a-col :span="5">
                <a-select
                  v-model:value="priorityFilter"
                  placeholder="优先级"
                  style="width: 100%"
                  allow-clear
                  @change="handleFilterChange"
                >
                  <a-select-option value="P0">P0</a-select-option>
                  <a-select-option value="P1">P1</a-select-option>
                  <a-select-option value="P2">P2</a-select-option>
                  <a-select-option value="P3">P3</a-select-option>
                </a-select>
              </a-col>
              <a-col :span="5">
                <a-button @click="resetFilters">重置</a-button>
              </a-col>
              <a-col :span="6" style="text-align: right">
                <span class="selection-count">
                  已选择 <strong>{{ selectedCaseIds.length }}</strong> 个用例
                </span>
              </a-col>
            </a-row>
          </a-card>

          <!-- 用例列表 -->
          <a-card size="small" class="cases-card">
            <a-spin :spinning="loading">
              <a-table
                ref="tableRef"
                :columns="columns"
                :data-source="filteredCases"
                :loading="loading"
                :pagination="pagination"
                :row-selection="rowSelection"
                :row-key="record => record.id"
                :scroll="{ y: 350 }"
                @change="handleTableChange"
                size="small"
                class="case-selector-table"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'name'">
                    <div class="case-name">
                      <span class="case-title">{{ record.name }}</span>
                      <span v-if="isAlreadySelected(record.id)" class="already-selected-tag">
                        <CheckCircleFilled style="color: #52c41a" /> 已添加
                      </span>
                    </div>
                  </template>

                  <template v-else-if="column.key === 'priority'">
                    <a-tag :color="getPriorityColor(record.priority)">
                      {{ record.priority || '-' }}
                    </a-tag>
                  </template>

                  <template v-else-if="column.key === 'moduleName'">
                    <span class="module-name-cell">{{ getModuleName(record.moduleId) || '-' }}</span>
                  </template>
                </template>
              </a-table>
            </a-spin>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { FolderOutlined, CheckCircleFilled } from '@ant-design/icons-vue'
import { testCaseApi } from '@/api/testCase'
import { projectApi } from '@/api/project'
import type { TestCase } from '@/types'

interface Props {
  visible: boolean
  projectId: string
  selectedCases?: TestCase[]
}

interface Emits {
  (e: 'update:visible', visible: boolean): void
  (e: 'confirm', cases: TestCase[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 用于 v-model 绑定的本地可写 computed
const innerVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

// 响应式数据
const loading = ref(false)
const loadingModules = ref(false)
const tableRef = ref()
const searchKeyword = ref('')
const priorityFilter = ref<string>()
const moduleSearchValue = ref('')

// 模块树数据
const modules = ref<any[]>([])
const selectedModuleKeys = ref<string[]>(['all'])
const expandedModuleKeys = ref<string[]>(['all'])

const allCases = ref<TestCase[]>([])
const selectedCaseIds = ref<string[]>([])

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50'],
  showTotal: (total: number) => `共 ${total} 条`
})

// 表格列定义
const columns = [
  {
    title: '用例名称',
    dataIndex: 'name',
    key: 'name',
    width: 280,
    ellipsis: true
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    width: 80,
    align: 'center' as const
  },
  {
    title: '所属模块',
    dataIndex: 'moduleName',
    key: 'moduleName',
    width: 150,
    ellipsis: true
  }
]

// 已存在的用例ID列表（传入的已选用例）
const existingCaseIds = computed(() => 
  (props.selectedCases || []).map(c => c.id)
)

// 判断用例是否已被添加到计划中
const isAlreadySelected = (caseId: string) => {
  return existingCaseIds.value.includes(caseId)
}

// 构建模块树
const moduleTreeData = computed(() => {
  const treeData: any[] = [
    {
      title: '全部用例',
      key: 'all',
      caseCount: allCases.value.length,
      isLeaf: false
    }
  ]

  // 构建模块Map
  const moduleMap = new Map<string, any>()
  modules.value.forEach(m => {
    moduleMap.set(m.id, {
      title: m.name,
      key: m.id,
      parentId: m.parentId,
      caseCount: 0,
      children: []
    })
  })

  // 计算每个模块的用例数
  allCases.value.forEach(c => {
    const moduleId = c.moduleId
    if (moduleId && moduleMap.has(moduleId)) {
      moduleMap.get(moduleId).caseCount++
    }
  })

  // 构建树结构
  const rootModules: any[] = []
  moduleMap.forEach(module => {
    if (module.parentId && moduleMap.has(module.parentId)) {
      moduleMap.get(module.parentId).children.push(module)
    } else {
      rootModules.push(module)
    }
  })

  treeData.push(...rootModules)
  return treeData
})

// 过滤后的模块树
const filteredModuleTree = computed(() => {
  if (!moduleSearchValue.value) return moduleTreeData.value
  
  const keyword = moduleSearchValue.value.toLowerCase()
  const filterTree = (nodes: any[]): any[] => {
    return nodes.filter(node => {
      if (node.title.toLowerCase().includes(keyword)) return true
      if (node.children && node.children.length > 0) {
        node.children = filterTree(node.children)
        return node.children.length > 0
      }
      return false
    })
  }
  
  return filterTree(JSON.parse(JSON.stringify(moduleTreeData.value)))
})

// 根据模块筛选用例
const filteredCases = computed(() => {
  let filtered = [...allCases.value]

  // 模块筛选
  const selectedKey = selectedModuleKeys.value[0]
  if (selectedKey && selectedKey !== 'all') {
    // 获取选中模块及其子模块的所有ID
    const moduleIds = getModuleAndChildrenIds(selectedKey)
    filtered = filtered.filter(c => moduleIds.includes(c.moduleId || ''))
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(caseItem => 
      caseItem.name?.toLowerCase().includes(keyword)
    )
  }

  // 优先级筛选
  if (priorityFilter.value) {
    filtered = filtered.filter(caseItem => caseItem.priority === priorityFilter.value)
  }

  return filtered
})

// 获取模块及其所有子模块的ID
const getModuleAndChildrenIds = (moduleId: string): string[] => {
  const ids = [moduleId]
  const findChildren = (parentId: string) => {
    modules.value.forEach(m => {
      if (m.parentId === parentId) {
        ids.push(m.id)
        findChildren(m.id)
      }
    })
  }
  findChildren(moduleId)
  return ids
}

// 获取模块名称
const getModuleName = (moduleId: string | undefined): string => {
  if (!moduleId) return '-'
  const module = modules.value.find(m => m.id === moduleId)
  return module?.name || '-'
}

// 当前选择的用例（仅新选择的，不包括已存在的）
const newSelectedCases = computed(() => 
  allCases.value.filter(caseItem => 
    selectedCaseIds.value.includes(caseItem.id) && !existingCaseIds.value.includes(caseItem.id)
  )
)

const rowSelection = computed(() => ({
  selectedRowKeys: selectedCaseIds.value,
  onChange: (selectedRowKeys: string[]) => {
    selectedCaseIds.value = selectedRowKeys
  },
  getCheckboxProps: (record: TestCase) => ({
    // 已添加的用例不可取消选择
    disabled: isAlreadySelected(record.id),
    checked: selectedCaseIds.value.includes(record.id)
  })
}))

// 方法
const loadModules = async () => {
  if (!props.projectId) return
  
  loadingModules.value = true
  try {
    const response = await projectApi.getModules(props.projectId)
    modules.value = response.modules || response || []
    
    // 展开所有模块
    expandedModuleKeys.value = ['all', ...modules.value.map((m: any) => m.id)]
  } catch (error) {
    console.error('Failed to load modules:', error)
  } finally {
    loadingModules.value = false
  }
}

const loadTestCases = async () => {
  if (!props.projectId) return

  loading.value = true
  try {
    const response = await testCaseApi.getTestCases(props.projectId, {
      page: 1,
      size: 9999 // 获取所有用例
    })

    allCases.value = response.items || []
    pagination.total = allCases.value.length

    // 设置已选中的用例（包括已存在的）
    if (props.selectedCases && props.selectedCases.length > 0) {
      selectedCaseIds.value = [...props.selectedCases.map(c => c.id)]
    }
  } catch (error) {
    console.error('Failed to load test cases:', error)
    message.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const handleModuleSelect = (keys: string[]) => {
  selectedModuleKeys.value = keys.length > 0 ? keys : ['all']
  pagination.current = 1
}

const handleModuleExpand = (keys: string[]) => {
  expandedModuleKeys.value = keys
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

const handleSearch = () => {
  pagination.current = 1
}

const handleFilterChange = () => {
  pagination.current = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  priorityFilter.value = undefined
  selectedModuleKeys.value = ['all']
  pagination.current = 1
}

const handleConfirm = () => {
  // 只返回新选择的用例（不包括已存在的）
  emit('confirm', newSelectedCases.value)
}

const handleCancel = () => {
  emit('update:visible', false)
}

// 工具方法
const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    'P0': 'red',
    'P1': 'orange',
    'P2': 'blue',
    'P3': 'green',
    'high': 'red',
    'medium': 'orange',
    'low': 'green'
  }
  return colors[priority] || 'default'
}

// 监听
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    loadModules()
    loadTestCases()
  }
})

// 生命周期
onMounted(() => {
  if (props.visible) {
    loadModules()
    loadTestCases()
  }
})
</script>

<style scoped>
.test-case-selector {
  min-height: 500px;
}

.module-tree-card {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.module-tree-card :deep(.ant-card-body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.module-tree-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.module-title {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.case-count {
  color: #999;
  font-size: 12px;
}

.filter-card {
  margin-bottom: 12px;
}

.cases-card {
  min-height: 400px;
}

.selection-count {
  color: #666;
  font-size: 13px;
}

.selection-count strong {
  color: #1890ff;
  font-size: 15px;
}

.case-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.already-selected-tag {
  font-size: 12px;
  color: #52c41a;
  white-space: nowrap;
}

.module-name-cell {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 表格单行显示样式 */
.case-selector-table :deep(.ant-table-cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.case-selector-table :deep(.ant-table-row-disabled) {
  background-color: #f5f5f5;
}

.case-selector-table :deep(.ant-table-row-disabled td) {
  color: #999;
}
</style>
