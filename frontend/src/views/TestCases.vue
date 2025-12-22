<template>
  <div class="test-cases-container">
    <a-layout class="test-cases-layout">
      <!-- 左侧用例树 -->
      <a-layout-sider width="300" class="case-tree-sider">
        <div class="tree-header">
          <h3>用例结构</h3>
          <a-space>
            <a-button type="text" size="small" @click="refreshTree">
              <template #icon><ReloadOutlined /></template>
            </a-button>
            <a-dropdown>
              <a-button type="text" size="small">
                <template #icon><PlusOutlined /></template>
              </a-button>
              <template #overlay>
                <a-menu @click="handleTreeAction">
                  <a-menu-item key="add-module">新建模块</a-menu-item>
                  <a-menu-item key="add-case">新建用例</a-menu-item>
                  <a-menu-item key="import-cases">导入用例</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </div>
        
        <a-input-search
          v-model:value="treeSearchValue"
          placeholder="搜索用例或模块"
          class="tree-search"
          @search="handleTreeSearch"
        />
        
        <TestCaseTree
          :project-id="projectId"
          :selected-keys="selectedKeys"
          :expanded-keys="expandedKeys"
          :search-value="treeSearchValue"
          @select="handleTreeSelect"
          @right-click="handleRightClick"
          @drop="handleTreeDrop"
          @refresh="fetchCaseTree"
        />
      </a-layout-sider>
      
      <!-- 右侧用例详情/编辑区 -->
      <a-layout-content class="case-detail-content">
        <div v-if="!selectedCaseId" class="empty-state">
          <a-empty description="请从左侧选择或创建测试用例" />
          <a-button type="primary" @click="createNewCase">
            <template #icon><PlusOutlined /></template>
            新建用例
          </a-button>
        </div>
        
        <div v-else class="case-detail">
          <a-spin :spinning="loading">
            <TestCaseDetail
              v-if="!isEditing"
              :case-id="selectedCaseId"
              :read-only="true"
              @edit="startEditing"
              @delete="handleDeleteCase"
              @copy="handleCopyCase"
              @execute="handleExecuteCase"
            />
            
            <TestCaseEdit
              v-else
              :case-id="selectedCaseId"
              :project-id="projectId"
              @save="handleSaveCase"
              @cancel="cancelEditing"
            />
          </a-spin>
        </div>
      </a-layout-content>
    </a-layout>
    
    <!-- 右键菜单 -->
    <a-dropdown
      v-model:visible="contextMenuVisible"
      :trigger="['contextMenu']"
      :style="{ position: 'fixed', zIndex: 1000 }"
      @visible-change="handleContextMenuVisible"
    >
      <div></div>
      <template #overlay>
        <a-menu @click="handleContextMenuClick">
          <a-menu-item key="add-module">新建模块</a-menu-item>
          <a-menu-item key="add-case">新建用例</a-menu-item>
          <a-menu-item key="edit" v-if="contextMenuTarget?.type === 'case'">编辑</a-menu-item>
          <a-menu-item key="copy" v-if="contextMenuTarget?.type === 'case'">复制</a-menu-item>
          <a-menu-item key="delete" v-if="contextMenuTarget?.type === 'case'">删除</a-menu-item>
          <a-menu-divider />
          <a-menu-item key="refresh">刷新</a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
    
    <!-- 导入用例对话框 -->
    <ImportCasesModal
      v-model:visible="importModalVisible"
      :project-id="projectId"
      @success="handleImportSuccess"
    />
    
    <!-- 新建模块对话框 -->
    <CreateModuleModal
      v-model:visible="createModuleModalVisible"
      :project-id="projectId"
      :parent-module-id="createModuleParentId"
      @success="handleModuleCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import TestCaseTree from '@/components/TestCaseTree/TestCaseTree.vue'
import TestCaseDetail from '@/components/TestCase/TestCaseDetail.vue'
import TestCaseEdit from '@/components/TestCase/TestCaseEdit.vue'
import ImportCasesModal from '@/components/TestCase/ImportCasesModal.vue'
import CreateModuleModal from '@/components/TestCase/CreateModuleModal.vue'
import { useProjectStore } from '@/stores/project'
import type { TreeNode } from '@/types'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId as string)

const loading = ref(false)
const selectedCaseId = ref<string | null>(null)
const isEditing = ref(false)
const treeSearchValue = ref('')
const selectedKeys = ref<string[]>([])
const expandedKeys = ref<string[]>([])
const contextMenuVisible = ref(false)
const contextMenuTarget = ref<TreeNode | null>(null)
const importModalVisible = ref(false)
const createModuleModalVisible = ref(false)
const createModuleParentId = ref<string | null>(null)

const fetchCaseTree = async () => {
  // 这里实现获取用例树的逻辑
  console.log('fetchCaseTree', projectId.value)
}

const handleTreeSelect = (node: TreeNode) => {
  if (node.type === 'case') {
    selectedCaseId.value = node.key
    selectedKeys.value = [node.key]
    isEditing.value = false
  }
}

const handleTreeSearch = (value: string) => {
  treeSearchValue.value = value
}

const handleRightClick = (node: TreeNode, event: MouseEvent) => {
  contextMenuTarget.value = node
  contextMenuVisible.value = true
}

const handleContextMenuVisible = (visible: boolean) => {
  contextMenuVisible.value = visible
}

const handleContextMenuClick = ({ key }: { key: string }) => {
  switch (key) {
    case 'add-module':
      createModuleParentId.value = contextMenuTarget.value?.type === 'module' 
        ? contextMenuTarget.value.key 
        : null
      createModuleModalVisible.value = true
      break
    case 'add-case':
      selectedKeys.value = contextMenuTarget.value?.key ? [contextMenuTarget.value.key] : []
      createNewCase()
      break
    case 'edit':
      if (contextMenuTarget.value?.type === 'case') {
        selectedCaseId.value = contextMenuTarget.value.key
        startEditing()
      }
      break
    case 'copy':
      handleCopyCase()
      break
    case 'delete':
      handleDeleteCase()
      break
    case 'refresh':
      fetchCaseTree()
      break
  }
  contextMenuVisible.value = false
}

const handleTreeDrop = (info: any) => {
  console.log('tree drop', info)
}

const handleTreeAction = ({ key }: { key: string }) => {
  switch (key) {
    case 'add-module':
      createModuleModalVisible.value = true
      break
    case 'add-case':
      createNewCase()
      break
    case 'import-cases':
      importModalVisible.value = true
      break
  }
}

const createNewCase = () => {
  selectedCaseId.value = null
  isEditing.value = true
}

const startEditing = () => {
  isEditing.value = true
}

const cancelEditing = () => {
  isEditing.value = false
  if (!selectedCaseId.value) {
    selectedCaseId.value = null
  }
}

const handleSaveCase = async (caseData: any) => {
  try {
    loading.value = true
    // 这里调用保存用例的API
    console.log('save case', caseData)
    message.success('用例保存成功')
    isEditing.value = false
    await fetchCaseTree()
  } catch (error) {
    message.error('保存失败')
  } finally {
    loading.value = false
  }
}

const handleDeleteCase = async () => {
  if (!selectedCaseId.value) return
  
  try {
    loading.value = true
    // 这里调用删除用例的API
    console.log('delete case', selectedCaseId.value)
    message.success('用例删除成功')
    selectedCaseId.value = null
    await fetchCaseTree()
  } catch (error) {
    message.error('删除失败')
  } finally {
    loading.value = false
  }
}

const handleCopyCase = async () => {
  if (!selectedCaseId.value) return
  
  try {
    loading.value = true
    // 这里调用复制用例的API
    console.log('copy case', selectedCaseId.value)
    message.success('用例复制成功')
    await fetchCaseTree()
  } catch (error) {
    message.error('复制失败')
  } finally {
    loading.value = false
  }
}

const handleExecuteCase = async () => {
  if (!selectedCaseId.value) return
  
  try {
    loading.value = true
    // 这里调用执行用例的API
    console.log('execute case', selectedCaseId.value)
    message.success('用例执行已启动')
  } catch (error) {
    message.error('执行失败')
  } finally {
    loading.value = false
  }
}

const handleImportSuccess = (result: any) => {
  message.success(`导入完成：新增 ${result.created} 条，更新 ${result.updated} 条`)
  fetchCaseTree()
}

const handleModuleCreated = () => {
  message.success('模块创建成功')
  fetchCaseTree()
}

const refreshTree = () => {
  fetchCaseTree()
}

// 监听项目ID变化
watch(
  () => route.params.projectId,
  (newId) => {
    if (newId) {
      selectedCaseId.value = null
      isEditing.value = false
      selectedKeys.value = []
      expandedKeys.value = []
      fetchCaseTree()
    }
  },
  { immediate: true }
)

onMounted(() => {
  fetchCaseTree()
})
</script>

<style scoped>
.test-cases-container {
  height: 100%;
}

.test-cases-layout {
  height: 100%;
}

.case-tree-sider {
  background: #fff;
  border-right: 1px solid #f0f0f0;
  padding: 16px;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.tree-search {
  margin-bottom: 16px;
}

.case-detail-content {
  background: #fff;
  margin: 0;
  padding: 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.case-detail {
  height: 100%;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .cases-content {
    padding: 16px;
  }
  
  .case-tree-sider {
    width: 200px;
  }
}

@media (max-width: 992px) {
  .cases-content {
    padding: 12px;
  }
  
  .case-tree-sider {
    width: 180px;
  }
  
  .case-list-main {
    padding: 16px;
  }
  
  .filter-card .ant-row {
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .cases-content {
    padding: 8px;
  }
  
  .case-tree-sider {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.3s;
    width: 240px;
  }
  
  .case-tree-sider.show {
    transform: translateX(0);
  }
  
  .case-list-main {
    padding: 12px;
  }
  
  .filter-card {
    margin-bottom: 12px;
  }
  
  .filter-card .ant-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .filter-card .ant-col {
    width: 100% !important;
    max-width: 100% !important;
    margin-bottom: 8px;
  }
  
  .filter-card .ant-input-search,
  .filter-card .ant-select {
    width: 100% !important;
  }
  
  .case-actions {
    gap: 8px;
  }
}

@media (max-width: 576px) {
  .cases-content {
    padding: 6px;
  }
  
  .case-list-main {
    padding: 8px;
  }
  
  .page-header {
    margin-bottom: 12px;
    padding: 12px;
  }
  
  .page-header h2 {
    font-size: 18px;
  }
  
  .case-actions {
    flex-direction: column;
    gap: 6px;
    align-items: stretch;
  }
  
  .case-actions .ant-btn {
    width: 100%;
  }
  
  .filter-card .ant-col {
    margin-bottom: 6px;
  }
  
  .table-toolbar {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .table-toolbar .ant-input-search {
    width: 100% !important;
  }
}
</style>