<template>
  <div class="test-case-tree">
    <a-tree
      :tree-data="treeData"
      :load-data="onLoadData"
      :selected-keys="selectedKeys"
      :expanded-keys="expandedKeys"
      :draggable="true"
      :show-icon="true"
      block-node
      @select="onSelect"
      @expand="onExpand"
      @right-click="onRightClick"
      @drop="onDrop"
    >
      <template #switcherIcon="{ expanded }">
        <component :is="expanded ? DownOutlined : RightOutlined" />
      </template>
      
      <template #icon="{ dataRef }">
        <component :is="getNodeIcon(dataRef)" />
      </template>
      
      <template #title="{ dataRef }">
        <div class="tree-node-title">
          <span class="node-name">{{ dataRef.title }}</span>
          <div class="node-tags" v-if="dataRef.tags && dataRef.tags.length">
            <a-tag
              v-for="tag in dataRef.tags.slice(0, 2)"
              :key="tag"
              size="small"
              :color="getPriorityColor(dataRef.level)"
            >
              {{ tag }}
            </a-tag>
            <a-tag v-if="dataRef.tags.length > 2" size="small" color="default">
              +{{ dataRef.tags.length - 2 }}
            </a-tag>
          </div>
        </div>
      </template>
    </a-tree>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { DownOutlined, RightOutlined, FolderOutlined, FileTextOutlined } from '@ant-design/icons-vue'
import { testCaseApi } from '@/api/testCase'
import type { TreeNode } from '@/types'

interface Props {
  projectId: string
  selectedKeys?: string[]
  expandedKeys?: string[]
  searchValue?: string
}

interface Emits {
  (e: 'select', node: TreeNode): void
  (e: 'right-click', node: TreeNode, event: MouseEvent): void
  (e: 'drop', info: any): void
  (e: 'refresh'): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedKeys: () => [],
  expandedKeys: () => [],
  searchValue: ''
})

const emit = defineEmits<Emits>()

const treeData = ref<TreeNode[]>([])
const loading = ref(false)

const getNodeIcon = (node: TreeNode) => {
  if (node.type === 'project' || node.type === 'module') {
    return FolderOutlined
  }
  return FileTextOutlined
}

const getPriorityColor = (level?: string) => {
  switch (level) {
    case 'P0':
      return 'red'
    case 'P1':
      return 'orange'
    case 'P2':
      return 'blue'
    case 'P3':
      return 'green'
    default:
      return 'default'
  }
}

const onSelect = (selectedKeys: string[], info: any) => {
  if (info.node) {
    emit('select', info.node)
  }
}

const onExpand = (expandedKeys: string[]) => {
  emit('refresh')
}

const onRightClick = ({ event, node }: any) => {
  emit('right-click', node, event)
}

const onDrop = (info: any) => {
  emit('drop', info)
}

const onLoadData = async (treeNode: any) => {
  if (treeNode.dataRef.children) {
    return Promise.resolve()
  }

  try {
    if (treeNode.dataRef.type === 'module') {
      // 加载模块下的子模块和用例
      const response = await testCaseApi.getCaseTree(props.projectId)
      // 这里需要根据实际API响应处理数据
      console.log('load module children', treeNode.dataRef.key)
    }
  } catch (error) {
    console.error('Failed to load tree data:', error)
  }

  return Promise.resolve()
}

const fetchTreeData = async () => {
  if (!props.projectId) return

  loading.value = true
  try {
    const response = await testCaseApi.getCaseTree(props.projectId)
    
    // 处理搜索过滤
    let processedData = response
    
    if (props.searchValue) {
      processedData = filterTreeData(response, props.searchValue)
    }
    
    treeData.value = processedData
  } catch (error) {
    console.error('Failed to fetch tree data:', error)
  } finally {
    loading.value = false
  }
}

const filterTreeData = (data: TreeNode[], searchValue: string): TreeNode[] => {
  const filtered: TreeNode[] = []
  
  const search = (nodes: TreeNode[]): TreeNode[] => {
    return nodes
      .map(node => {
        const isMatch = node.title.toLowerCase().includes(searchValue.toLowerCase()) ||
                       (node.caseCode && node.caseCode.toLowerCase().includes(searchValue.toLowerCase()))
        
        let children: TreeNode[] = []
        if (node.children) {
          children = search(node.children)
        }
        
        if (isMatch || children.length > 0) {
          return {
            ...node,
            children: node.type === 'module' || node.type === 'project' ? children : undefined
          }
        }
        
        return null
      })
      .filter((node): node is TreeNode => node !== null)
  }
  
  return search(data)
}

// 监听props变化
watch(
  () => props.projectId,
  () => {
    if (props.projectId) {
      fetchTreeData()
    }
  },
  { immediate: true }
)

watch(
  () => props.searchValue,
  () => {
    if (props.projectId) {
      fetchTreeData()
    }
  }
)

// 暴露方法给父组件
defineExpose({
  refresh: fetchTreeData
})
</script>

<style scoped>
.test-case-tree {
  height: calc(100vh - 200px);
  overflow: auto;
}

.tree-node-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.node-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-tags {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

:deep(.ant-tree-node-content-wrapper) {
  width: 100%;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

:deep(.ant-tree-node-content-wrapper:hover) {
  background-color: #f5f5f5;
}

:deep(.ant-tree-node-selected .ant-tree-node-content-wrapper) {
  background-color: #e6f7ff;
}

:deep(.ant-tree-switcher) {
  width: 16px;
}

:deep(.ant-tree-node-content-wrapper .ant-tree-title) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
</style>