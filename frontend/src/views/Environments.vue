<template>
  <div class="environments-container">
    <a-page-header
      title="环境管理"
      sub-title="管理测试环境配置"
    >
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建环境
        </a-button>
      </template>
    </a-page-header>

    <!-- 可滚动内容区域 -->
    <div class="scrollable-content">
      <a-card class="environments-content">
        <a-spin :spinning="loading">
          <a-table
            :columns="columns"
            :data-source="environments"
            :pagination="false"
            :row-key="record => record.id"
            :scroll="{ x: 1000, y: 'calc(100vh - 340px)' }"
            @change="handleTableChange"
          >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="env-name-cell">
                <div class="env-icon" :class="{ online: record.isOnline }">
                  <DesktopOutlined />
                </div>
                <span class="env-name">{{ record.name }}</span>
              </div>
            </template>

            <template v-else-if="column.key === 'tags'">
              <a-space v-if="record.tags" wrap :size="4">
                <a-tag v-for="tag in (record.tags || '').split(',').filter(t => t.trim())" :key="tag.trim()" size="small">
                  {{ tag.trim() }}
                </a-tag>
              </a-space>
              <span v-else>-</span>
            </template>

            <template v-else-if="column.key === 'remoteWorkDir'">
              <span v-if="record.remoteWorkDir" :title="record.remoteWorkDir" style="color: #8c8c8c; font-family: monospace">
                <FolderOutlined /> {{ record.remoteWorkDir }}
              </span>
              <span v-else style="color: #999">-</span>
            </template>

            <template v-else-if="column.key === 'isOnline'">
              <div class="status-indicator">
                <span class="status-dot" :class="{ 
                  online: record.isOnline && !record.isBusy,
                  busy: record.isOnline && record.isBusy,
                  offline: !record.isOnline 
                }"></span>
                <span class="status-text">
                  {{ record.isOnline ? (record.isBusy ? '忙碌中' : '在线') : '离线' }}
                </span>
              </div>
            </template>

            <template v-else-if="column.key === 'maxConcurrentTasks'">
              <a-tag color="blue">
                <template #icon><DashboardOutlined /></template>
                {{ record.maxConcurrentTasks || 1 }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-switch
                :checked="record.status"
                @change="handleStatusChange(record.id, $event)"
              />
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click="editEnvironment(record)">
                  编辑
                </a-button>
                <a-button type="link" size="small" danger @click="deleteEnvironment(record.id)">
                  删除
                </a-button>
                <a-dropdown>
                  <a-button type="link" size="small">
                    更多
                  </a-button>
                  <template #overlay>
                    <a-menu @click="handleMoreMenuClick($event, record)">
                      <a-menu-item key="details">详情</a-menu-item>
                      <a-menu-item key="startCommand">启动命令</a-menu-item>
                      <a-menu-item key="executionHistory">执行历史</a-menu-item>
                      <a-menu-item key="workspace">工作空间</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-spin>

      <!-- 固定底部分页器 -->
      <div class="fixed-footer">
        <a-pagination
          v-model:current="pagination.current"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="true"
          :show-quick-jumper="true"
          :show-total="(total) => `共 ${total} 条`"
          @change="handlePaginationChange"
          @show-size-change="handlePaginationChange"
        />
      </div>
    </a-card>
    </div>

    <!-- 启动命令对话框 -->
    <a-modal
      v-model:visible="startCommandModalVisible"
      title="启动命令"
      width="800px"
      :footer="null"
    >
      <div v-if="startCommandData">
        <a-alert
          message="使用以下命令启动Agent"
          description="请在远程节点上执行此命令以连接服务端"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-form-item label="启动命令">
          <a-input
            :value="startCommandData.startCommand"
            readonly
            style="font-family: monospace"
          >
            <template #suffix>
              <a-button
                type="text"
                size="small"
                @click="copyStartCommand"
              >
                <template #icon><CopyOutlined /></template>
                复制
              </a-button>
            </template>
          </a-input>
        </a-form-item>

        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="WebSocket地址">
            {{ startCommandData.websocketUrl }}
          </a-descriptions-item>
          <a-descriptions-item label="Token">
            <a-input
              :value="startCommandData.token"
              readonly
              style="font-family: monospace"
            >
              <template #suffix>
                <a-button
                  type="text"
                  size="small"
                  @click="copyToken"
                >
                  <template #icon><CopyOutlined /></template>
                  复制
                </a-button>
              </template>
            </a-input>
          </a-descriptions-item>
          <a-descriptions-item label="工作目录">
            {{ startCommandData.workDir }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider />

        <a-space>
          <a-button @click="regenerateTokenForCurrent">
            <template #icon><ReloadOutlined /></template>
            重新生成Token
          </a-button>
          <a-button type="primary" @click="copyStartCommand">
            <template #icon><CopyOutlined /></template>
            复制启动命令
          </a-button>
        </a-space>
      </div>
    </a-modal>

    <!-- 节点详情对话框 -->
    <a-modal
      v-model:visible="detailModalVisible"
      title="节点详情"
      width="600px"
      :footer="null"
    >
      <a-descriptions :column="1" bordered v-if="selectedEnvironment">
        <a-descriptions-item label="节点名称">
          {{ selectedEnvironment.name }}
        </a-descriptions-item>
        <a-descriptions-item label="标签">
          <a-space v-if="selectedEnvironment.tags" wrap :size="4">
            <a-tag v-for="tag in (selectedEnvironment.tags || '').split(',').filter(t => t.trim())" :key="tag.trim()">
              {{ tag.trim() }}
            </a-tag>
          </a-space>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="远程工作目录">
          {{ selectedEnvironment.remoteWorkDir || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="在线状态">
          <a-tag :color="selectedEnvironment.isOnline ? 'green' : 'red'">
            {{ selectedEnvironment.isOnline ? '在线' : '离线' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="节点IP">
          {{ selectedEnvironment.nodeIp || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="操作系统">
          <div v-if="selectedEnvironment.osType">
            <div>{{ selectedEnvironment.osType }}</div>
            <div v-if="selectedEnvironment.osVersion" style="font-size: 12px; color: #999; margin-top: 4px">
              {{ selectedEnvironment.osVersion }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="CPU信息">
          <div v-if="selectedEnvironment.cpuInfo">
            <div><strong>型号：</strong>{{ selectedEnvironment.cpuInfo.model || '-' }}</div>
            <div style="margin-top: 4px">
              <strong>核心数：</strong>{{ selectedEnvironment.cpuInfo.cores || '-' }}核
            </div>
            <div style="margin-top: 4px">
              <strong>频率：</strong>{{ selectedEnvironment.cpuInfo.frequency || '-' }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="内存信息">
          <div v-if="selectedEnvironment.memoryInfo">
            <div><strong>总计：</strong>{{ selectedEnvironment.memoryInfo.total || '-' }}</div>
            <div style="margin-top: 4px">
              <strong>已用：</strong>{{ selectedEnvironment.memoryInfo.used || '-' }}
            </div>
            <div style="margin-top: 4px">
              <strong>可用：</strong>{{ selectedEnvironment.memoryInfo.free || '-' }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="磁盘信息">
          <div v-if="selectedEnvironment.diskInfo">
            <div><strong>总计：</strong>{{ selectedEnvironment.diskInfo.total || '-' }}</div>
            <div style="margin-top: 4px">
              <strong>已用：</strong>{{ selectedEnvironment.diskInfo.used || '-' }}
            </div>
            <div style="margin-top: 4px">
              <strong>可用：</strong>{{ selectedEnvironment.diskInfo.free || '-' }}
            </div>
          </div>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="最后心跳时间">
          {{ selectedEnvironment.lastHeartbeat || selectedEnvironment.last_heartbeat ? formatDateTime(selectedEnvironment.lastHeartbeat || selectedEnvironment.last_heartbeat) : '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="描述">
          {{ selectedEnvironment.description || '-' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <!-- 执行历史抽屉 -->
    <a-drawer
      v-model:visible="executionHistoryDrawerVisible"
      title="执行历史"
      :width="1000"
      placement="right"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshExecutionHistory">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>

      <!-- 筛选区域 -->
      <div class="filter-section" style="margin-bottom: 16px">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="executionSearchValue"
              placeholder="搜索用例名称或编号"
              @search="handleExecutionSearch"
              allow-clear
            />
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="executionResultFilter"
              placeholder="执行结果"
              style="width: 100%"
              allow-clear
              @change="handleExecutionFilterChange"
            >
              <a-select-option value="passed">通过</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
              <a-select-option value="blocked">阻塞</a-select-option>
              <a-select-option value="skipped">跳过</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="10">
            <a-range-picker
              v-model:value="executionDateRange"
              style="width: 100%"
              @change="handleExecutionFilterChange"
            />
          </a-col>
        </a-row>
      </div>

      <!-- 执行历史列表 -->
      <a-table
        :columns="executionColumns"
        :data-source="executionHistory"
        :loading="executionHistoryLoading"
        :pagination="executionPagination"
        :row-key="record => record.id"
        :scroll="{ x: 1040 }"
        @change="handleExecutionTableChange"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'logId'">
            <span style="font-family: monospace; font-size: 12px;">{{ record.logId || '-' }}</span>
          </template>

          <template v-else-if="column.key === 'suiteName'">
            {{ record.suiteName || '未知测试套' }}
          </template>

          <template v-else-if="column.key === 'result'">
            <a-tag :color="getExecutionResultColor(record.result)">
              {{ getExecutionResultText(record.result) }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'duration'">
            {{ formatExecutionDuration(record.duration) }}
          </template>

          <template v-else-if="column.key === 'executedAt'">
            {{ formatDateTime(record.executedAt) }}
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="viewExecutionLogs(record)">
                日志
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-drawer>

    <!-- 执行日志对话框 -->
    <a-modal
      v-model:visible="executionLogModalVisible"
      title="执行日志"
      width="900px"
      :footer="null"
    >
      <a-spin :spinning="executionLogLoading">
        <pre class="execution-log">{{ executionLog }}</pre>
      </a-spin>
    </a-modal>

    <!-- 工作空间对话框 -->
    <a-modal
      v-model:visible="workspaceModalVisible"
      title="工作空间"
      width="1000px"
      :footer="null"
    >
      <div v-if="currentWorkspaceEnvironment">
        <a-alert
          :message="`节点: ${currentWorkspaceEnvironment.name}`"
          :description="`工作目录: ${currentWorkspaceEnvironment.remoteWorkDir || '-'}`"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />

        <div class="workspace-toolbar" style="margin-bottom: 16px">
          <a-space>
            <a-button @click="refreshWorkspace">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
            <a-button @click="uploadFile" :disabled="!currentWorkspaceEnvironment.isOnline">
              <template #icon><UploadOutlined /></template>
              上传文件
            </a-button>
            <a-button @click="createFolder" :disabled="!currentWorkspaceEnvironment.isOnline">
              <template #icon><FolderAddOutlined /></template>
              新建文件夹
            </a-button>
            <a-input-search
              v-model:value="workspaceSearchValue"
              placeholder="搜索文件或文件夹"
              style="width: 200px"
              @search="handleWorkspaceSearch"
              allow-clear
            />
          </a-space>
        </div>

        <a-spin :spinning="workspaceLoading">
          <a-table
            :columns="workspaceColumns"
            :data-source="workspaceFiles"
            :pagination="false"
            :row-key="record => record.path"
            :scroll="{ x: 730 }"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <a-space>
                  <component
                    :is="record.type === 'directory' ? FolderOutlined : FileOutlined"
                    :style="{ color: record.type === 'directory' ? '#faad14' : '#1890ff' }"
                  />
                  <a
                    v-if="record.type === 'directory'"
                    @click="enterDirectory(record)"
                    style="cursor: pointer"
                  >
                    {{ record.name }}
                  </a>
                  <span v-else>{{ record.name }}</span>
                </a-space>
              </template>

              <template v-else-if="column.key === 'size'">
                {{ record.type === 'directory' ? '-' : formatFileSize(record.size) }}
              </template>

              <template v-else-if="column.key === 'modified'">
                {{ formatDateTime(record.modified) }}
              </template>

              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button
                    v-if="record.type === 'file'"
                    type="link"
                    size="small"
                    @click="viewFile(record)"
                  >
                    查看
                  </a-button>
                  <a-button
                    v-if="record.type === 'file'"
                    type="link"
                    size="small"
                    @click="downloadFile(record)"
                  >
                    下载
                  </a-button>
                  <a-button
                    type="link"
                    size="small"
                    danger
                    @click="deleteFile(record)"
                    :disabled="!currentWorkspaceEnvironment.isOnline"
                  >
                    删除
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-spin>
      </div>
    </a-modal>

    <!-- 文件查看对话框 -->
    <a-modal
      v-model:visible="fileViewModalVisible"
      :title="`查看文件: ${currentFile?.name || ''}`"
      width="900px"
      :footer="null"
    >
      <a-spin :spinning="fileViewLoading">
        <pre class="file-content" v-if="fileContent">{{ fileContent }}</pre>
        <a-empty v-else description="无法加载文件内容" />
      </a-spin>
    </a-modal>

    <!-- 创建/编辑环境对话框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingEnvironment ? '编辑环境' : '新建环境'"
      width="700px"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item name="name" label="节点名称" :rules="[{ required: true, message: '请输入节点名称' }]">
          <a-input
            v-model:value="formData.name"
            placeholder="请输入节点名称，如：测试节点-01"
          />
        </a-form-item>

        <a-form-item name="tags" label="标签">
          <a-input
            v-model:value="formData.tags"
            placeholder="请输入标签，多个标签用逗号分隔，如：linux,ubuntu,test"
          />
        </a-form-item>

        <a-form-item name="remoteWorkDir" label="远程工作目录" :rules="[{ required: true, message: '请输入远程工作目录' }]">
          <a-input
            v-model:value="formData.remoteWorkDir"
            placeholder="请输入远程工作目录，如：/home/agent/workspace"
          />
        </a-form-item>

        <a-form-item name="reconnectDelay" label="Agent重连延迟时间（秒）" :rules="[{ required: true, message: '请输入重连延迟时间' }]">
          <a-input-number
            v-model:value="formData.reconnectDelay"
            :min="1"
            :max="3600"
            placeholder="请输入重连延迟时间（秒），默认30秒"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            当Agent与云端断开连接后，等待多少秒后开始重连。建议值：30-300秒
          </div>
        </a-form-item>

        <a-form-item name="maxConcurrentTasks" label="最大并发任务数量" :rules="[{ required: true, message: '请输入最大并发任务数量' }]">
          <a-input-number
            v-model:value="formData.maxConcurrentTasks"
            :min="1"
            :max="100"
            placeholder="请输入最大并发任务数量，默认为1"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            超过此数量的任务将自动排队等待执行
          </div>
        </a-form-item>

        <a-form-item name="description" label="描述">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入节点描述（可选）"
            :rows="3"
          />
        </a-form-item>

        <a-form-item name="status" label="启用状态">
          <a-switch v-model:checked="formData.status" />
          <span style="margin-left: 8px; color: #999">
            {{ formData.status ? '已启用' : '已禁用' }}
          </span>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  CopyOutlined,
  UploadOutlined,
  FolderAddOutlined,
  FolderOutlined,
  FileOutlined,
  DesktopOutlined,
  WifiOutlined,
  GlobalOutlined,
  DashboardOutlined,
  LaptopOutlined,
  CodeOutlined,
  HddOutlined
} from '@ant-design/icons-vue'
import { environmentApi } from '@/api/environment'
import { testSuiteApi } from '@/api/testSuite'
import { useProjectStore } from '@/stores/project'
import type { Environment, TestExecution } from '@/types'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const detailModalVisible = ref(false)
const startCommandModalVisible = ref(false)
const editingEnvironment = ref<Environment | null>(null)
const selectedEnvironment = ref<Environment | null>(null)
const currentEnvironmentForCommand = ref<Environment | null>(null)
const startCommandData = ref<{
  startCommand: string
  websocketUrl: string
  token: string
  workDir: string
} | null>(null)

// 执行历史相关
const executionHistoryDrawerVisible = ref(false)
const executionHistoryLoading = ref(false)
const executionLogLoading = ref(false)
const currentEnvironmentId = ref<string>('')
const executionHistory = ref<Array<{
  id: string
  suiteId: string
  suiteName: string
  result: string
  executorId: string
  executorName: string
  executedAt: string
  duration: string | null
  executionId: string | null
  logId: string | null
  caseCount: number
}>>([])
const executionLog = ref('')
const executionLogModalVisible = ref(false)
const executionSearchValue = ref('')
const executionResultFilter = ref<string>()
const executionDateRange = ref<[Dayjs, Dayjs] | null>(null)

// 工作空间相关
const workspaceModalVisible = ref(false)
const workspaceLoading = ref(false)
const currentWorkspaceEnvironment = ref<Environment | null>(null)
const workspaceFiles = ref<any[]>([])
const workspaceSearchValue = ref('')
const currentPath = ref<string>('')
const fileViewModalVisible = ref(false)
const fileViewLoading = ref(false)
const currentFile = ref<any>(null)
const fileContent = ref<string>('')

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id || '')

const environments = ref<Environment[]>([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const formRef = ref()
const formData = reactive<{
  name: string
  tags: string
  remoteWorkDir: string
  reconnectDelay: number | string
  maxConcurrentTasks: number
  description: string
  status: boolean
}>({
  name: '',
  tags: '',
  remoteWorkDir: '',
  reconnectDelay: 30,  // 默认30秒
  maxConcurrentTasks: 1,  // 默认1个任务
  description: '',
  status: true
})

const rules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' }
  ]
}

const columns = [
  {
    title: '节点名称',
    key: 'name',
    dataIndex: 'name',
    width: 120,
    fixed: 'left' as const
  },
  {
    title: '标签',
    key: 'tags',
    dataIndex: 'tags',
    width: 120
  },
  {
    title: '远程工作目录',
    key: 'remoteWorkDir',
    dataIndex: 'remoteWorkDir',
    width: 200,
    ellipsis: true
  },
  {
    title: '在线状态',
    key: 'isOnline',
    dataIndex: 'isOnline',
    width: 90,
    align: 'center' as const
  },
  {
    title: '最大并发任务',
    key: 'maxConcurrentTasks',
    dataIndex: 'maxConcurrentTasks',
    width: 120,
    align: 'center' as const
  },
  {
    title: '启用状态',
    key: 'status',
    dataIndex: 'status',
    width: 90,
    align: 'center' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

const loadEnvironments = async () => {
  loading.value = true
  try {
    const response = await environmentApi.getEnvironments({
      page: pagination.current,
      size: pagination.pageSize,
    })
    console.log('Environments API 响应:', response)
    // 处理API响应格式
    if (response && typeof response === 'object' && 'items' in response) {
      const items = response.items || []
      // 确保字段名正确映射（后端可能返回snake_case，前端需要camelCase）
      environments.value = items.map((env: any) => ({
        ...env,
        remoteWorkDir: env.remoteWorkDir || env.remote_work_dir || '',
        nodeIp: env.nodeIp || env.node_ip || '',
        osType: env.osType || env.os_type || '',
        osVersion: env.osVersion || env.os_version || '',
        cpuInfo: env.cpuInfo || env.cpu_info || null,
        memoryInfo: env.memoryInfo || env.memory_info || null,
        diskInfo: env.diskInfo || env.disk_info || null,
        isOnline: env.isOnline !== undefined ? env.isOnline : (env.is_online !== undefined ? env.is_online : false),
        lastHeartbeat: env.lastHeartbeat || env.last_heartbeat || ''
      }))
      pagination.total = response.total || 0
    } else if (Array.isArray(response)) {
      // 兼容旧格式（直接返回数组）
      environments.value = response.map((env: any) => ({
        ...env,
        remoteWorkDir: env.remoteWorkDir || env.remote_work_dir || '',
        nodeIp: env.nodeIp || env.node_ip || '',
        osType: env.osType || env.os_type || '',
        osVersion: env.osVersion || env.os_version || '',
        cpuInfo: env.cpuInfo || env.cpu_info || null,
        memoryInfo: env.memoryInfo || env.memory_info || null,
        diskInfo: env.diskInfo || env.disk_info || null,
        isOnline: env.isOnline !== undefined ? env.isOnline : (env.is_online !== undefined ? env.is_online : false),
        lastHeartbeat: env.lastHeartbeat || env.last_heartbeat || ''
      }))
      pagination.total = response.length
    } else {
      environments.value = []
      pagination.total = 0
    }
    console.log('加载环境列表成功:', { count: environments.value.length, total: pagination.total })
  } catch (error) {
    console.error('Failed to load environments:', error)
    message.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadEnvironments()
}

const handlePaginationChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
  loadEnvironments()
}

const showCreateModal = () => {
  editingEnvironment.value = null
  formData.name = ''
  formData.tags = ''
  formData.remoteWorkDir = ''
  formData.reconnectDelay = 30
  formData.maxConcurrentTasks = 1
  formData.description = ''
  formData.status = true
  modalVisible.value = true
}

const editEnvironment = (environment: Environment) => {
  editingEnvironment.value = environment
  formData.name = environment.name
  formData.tags = environment.tags || ''
  formData.remoteWorkDir = environment.remoteWorkDir || ''
  // 将字符串转换为数字，如果不存在则使用默认值30
  formData.reconnectDelay = environment.reconnectDelay ? parseInt(environment.reconnectDelay, 10) || 30 : 30
  formData.maxConcurrentTasks = environment.maxConcurrentTasks || 1
  formData.description = environment.description || ''
  formData.status = environment.status
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    // 准备提交数据，将reconnectDelay转换为字符串
    const submitData = {
      ...formData,
      reconnectDelay: String(formData.reconnectDelay || 30),
      maxConcurrentTasks: formData.maxConcurrentTasks || 1
    }

    if (editingEnvironment.value) {
      await environmentApi.updateEnvironment(editingEnvironment.value.id, submitData)
      message.success('环境更新成功')
    } else {
      await environmentApi.createEnvironment(submitData)
      message.success('环境创建成功')
    }

    modalVisible.value = false
    await loadEnvironments()
  } catch (error: any) {
    if (error?.errorFields) {
      return
    }
    console.error('Failed to save environment:', error)
    message.error(editingEnvironment.value ? '环境更新失败' : '环境创建失败')
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  modalVisible.value = false
  formRef.value?.resetFields()
}

const handleStatusChange = async (id: string, checked: boolean) => {
  try {
    if (checked) {
      await environmentApi.enableEnvironment(id)
      message.success('环境已启用')
    } else {
      await environmentApi.disableEnvironment(id)
      message.success('环境已禁用')
    }
    await loadEnvironments()
  } catch (error) {
    console.error('Failed to change environment status:', error)
    message.error('状态更新失败')
    await loadEnvironments()
  }
}

const handleMoreMenuClick = ({ key }: { key: string }, record: Environment) => {
  switch (key) {
    case 'details':
      viewDetails(record)
      break
    case 'startCommand':
      viewStartCommand(record)
      break
    case 'executionHistory':
      viewExecutionHistory(record)
      break
    case 'workspace':
      viewWorkspace(record)
      break
  }
}

const viewDetails = (environment: Environment) => {
  selectedEnvironment.value = environment
  detailModalVisible.value = true
}

const viewStartCommand = async (environment: Environment) => {
  currentEnvironmentForCommand.value = environment
  try {
    const data = await environmentApi.getStartCommand(environment.id)
    startCommandData.value = data
    startCommandModalVisible.value = true
  } catch (error) {
    console.error('Failed to load start command:', error)
    message.error('获取启动命令失败')
  }
}

const copyStartCommand = async () => {
  if (startCommandData.value) {
    try {
      await navigator.clipboard.writeText(startCommandData.value.startCommand)
      message.success('启动命令已复制到剪贴板')
    } catch (error) {
      message.error('复制失败，请手动复制')
    }
  }
}

const copyToken = async () => {
  if (startCommandData.value) {
    try {
      await navigator.clipboard.writeText(startCommandData.value.token)
      message.success('Token已复制到剪贴板')
    } catch (error) {
      message.error('复制失败，请手动复制')
    }
  }
}

const regenerateTokenForCurrent = async () => {
  if (!currentEnvironmentForCommand.value) return

  Modal.confirm({
    title: '确认重新生成Token',
    content: '重新生成Token后，旧的Token将失效，需要重新启动Agent。确定要继续吗？',
    onOk: async () => {
      try {
        await environmentApi.regenerateToken(currentEnvironmentForCommand.value!.id)
        message.success('Token已重新生成')
        // 重新加载启动命令
        await viewStartCommand(currentEnvironmentForCommand.value!)
        // 重新加载环境列表
        await loadEnvironments()
      } catch (error) {
        console.error('Failed to regenerate token:', error)
        message.error('重新生成Token失败')
      }
    }
  })
}

const formatDateTime = (dateTime: string | undefined): string => {
  if (!dateTime) return '-'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 工作空间相关函数
const workspaceColumns = [
  {
    title: '名称',
    key: 'name',
    dataIndex: 'name',
    width: 250,
    ellipsis: true
  },
  {
    title: '类型',
    key: 'type',
    dataIndex: 'type',
    width: 80,
    align: 'center' as const
  },
  {
    title: '大小',
    key: 'size',
    dataIndex: 'size',
    width: 90,
    align: 'right' as const
  },
  {
    title: '修改时间',
    key: 'modified',
    dataIndex: 'modified',
    width: 200
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

const viewWorkspace = async (environment: Environment) => {
  currentWorkspaceEnvironment.value = environment
  currentPath.value = '' // 从工作目录根开始
  workspaceModalVisible.value = true
  workspaceSearchValue.value = ''
  await loadWorkspaceFiles()
}

const loadWorkspaceFiles = async () => {
  if (!currentWorkspaceEnvironment.value) {
    return
  }

  workspaceLoading.value = true
  try {
    // 检查环境是否在线
    if (!currentWorkspaceEnvironment.value.isOnline) {
      message.warning('节点离线，无法访问工作空间')
      workspaceFiles.value = []
      return
    }

    // 通过API获取文件列表
    const files = await environmentApi.listWorkspaceFiles(
      currentWorkspaceEnvironment.value.id,
      currentPath.value
    )
    workspaceFiles.value = files
  } catch (error: any) {
    console.error('Failed to load workspace files:', error)
    message.error(error.response?.data?.detail || '加载工作空间文件失败')
    workspaceFiles.value = []
  } finally {
    workspaceLoading.value = false
  }
}

const refreshWorkspace = () => {
  loadWorkspaceFiles()
}

const handleWorkspaceSearch = () => {
  // TODO: 实现搜索功能
  loadWorkspaceFiles()
}

const uploadFile = () => {
  message.info('上传文件功能开发中')
}

const createFolderName = ref('')
const createFolderModalVisible = ref(false)

const createFolder = () => {
  if (!currentWorkspaceEnvironment.value) return
  createFolderName.value = ''
  createFolderModalVisible.value = true
}

const handleCreateFolder = async () => {
  if (!currentWorkspaceEnvironment.value || !createFolderName.value.trim()) {
    message.warning('请输入文件夹名称')
    return
  }

  try {
    const folderName = createFolderName.value.trim()
    const newPath = currentPath.value
      ? `${currentPath.value}/${folderName}`
      : folderName
    await environmentApi.createWorkspaceDirectory(
      currentWorkspaceEnvironment.value.id,
      newPath
    )
    message.success('文件夹创建成功')
    createFolderModalVisible.value = false
    createFolderName.value = ''
    await loadWorkspaceFiles()
  } catch (error: any) {
    console.error('Failed to create folder:', error)
    message.error(error.response?.data?.detail || '创建文件夹失败')
  }
}

const enterDirectory = (dir: any) => {
  currentPath.value = dir.path
  loadWorkspaceFiles()
}

const viewFile = async (file: any) => {
  if (!currentWorkspaceEnvironment.value) return

  currentFile.value = file
  fileViewModalVisible.value = true
  fileViewLoading.value = true
  fileContent.value = ''

  try {
    const data = await environmentApi.readWorkspaceFile(
      currentWorkspaceEnvironment.value.id,
      file.path
    )

    if (data.encoding === 'base64') {
      // 如果是base64编码，显示提示信息
      fileContent.value = '[二进制文件，无法直接显示]'
    } else {
      fileContent.value = data.content
    }
  } catch (error: any) {
    console.error('Failed to load file content:', error)
    message.error(error.response?.data?.detail || '加载文件内容失败')
    fileContent.value = ''
  } finally {
    fileViewLoading.value = false
  }
}

const downloadFile = async (file: any) => {
  if (!currentWorkspaceEnvironment.value) return

  try {
    const data = await environmentApi.readWorkspaceFile(
      currentWorkspaceEnvironment.value.id,
      file.path
    )

    // 创建下载链接
    let blob: Blob
    if (data.encoding === 'base64') {
      // base64解码
      const binaryString = atob(data.content)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      blob = new Blob([bytes])
    } else {
      blob = new Blob([data.content], { type: 'text/plain;charset=utf-8' })
    }

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    message.success('文件下载成功')
  } catch (error: any) {
    console.error('Failed to download file:', error)
    message.error(error.response?.data?.detail || '下载文件失败')
  }
}

const deleteFile = (file: any) => {
  if (!currentWorkspaceEnvironment.value) return

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除${file.type === 'directory' ? '文件夹' : '文件'} "${file.name}" 吗？`,
    okType: 'danger',
    onOk: async () => {
      try {
        await environmentApi.deleteWorkspaceFile(
          currentWorkspaceEnvironment.value!.id,
          file.path
        )
        message.success('删除成功')
        await loadWorkspaceFiles()
      } catch (error: any) {
        console.error('Failed to delete file:', error)
        message.error(error.response?.data?.detail || '删除失败')
      }
    }
  })
}

const formatFileSize = (bytes: number): string => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

// 执行历史相关函数
const executionColumns = [
  {
    title: 'ID',
    key: 'logId',
    dataIndex: 'logId',
    width: 280,
    ellipsis: true
  },
  {
    title: '测试任务名称',
    key: 'suiteName',
    dataIndex: 'suiteName',
    width: 200,
    ellipsis: true
  },
  {
    title: '执行结果',
    key: 'result',
    dataIndex: 'result',
    width: 90,
    align: 'center' as const
  },
  {
    title: '执行人',
    key: 'executorName',
    dataIndex: 'executorName',
    width: 100
  },
  {
    title: '执行时间',
    key: 'executedAt',
    dataIndex: 'executedAt',
    width: 200
  },
  {
    title: '执行耗时',
    key: 'duration',
    dataIndex: 'duration',
    width: 90,
    align: 'center' as const
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    align: 'center' as const,
    fixed: 'right' as const
  }
]

const executionPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

const viewExecutionHistory = (environment: Environment) => {
  currentEnvironmentId.value = environment.id
  executionHistoryDrawerVisible.value = true
  executionSearchValue.value = ''
  executionResultFilter.value = undefined
  executionDateRange.value = null
  executionPagination.current = 1
  loadExecutionHistory()
}

const loadExecutionHistory = async () => {
  if (!currentEnvironmentId.value) {
    return
  }

  executionHistoryLoading.value = true
  try {
    const params: any = {
      skip: (executionPagination.current - 1) * executionPagination.pageSize,
      limit: executionPagination.pageSize
    }

    if (executionSearchValue.value) {
      params.search = executionSearchValue.value
    }

    if (executionResultFilter.value) {
      params.result = executionResultFilter.value
    }

    if (executionDateRange.value) {
      params.startDate = executionDateRange.value[0].format('YYYY-MM-DD')
      params.endDate = executionDateRange.value[1].format('YYYY-MM-DD')
    }

    const response = await environmentApi.getSuiteExecutions(currentEnvironmentId.value, params)
    executionHistory.value = response.items || []
    executionPagination.total = response.total || 0
  } catch (error) {
    console.error('Failed to load execution history:', error)
    message.error('加载执行历史失败')
  } finally {
    executionHistoryLoading.value = false
  }
}

const refreshExecutionHistory = () => {
  loadExecutionHistory()
}

const handleExecutionSearch = () => {
  executionPagination.current = 1
  loadExecutionHistory()
}

const handleExecutionFilterChange = () => {
  executionPagination.current = 1
  loadExecutionHistory()
}

const handleExecutionTableChange = (pag: any) => {
  if (pag) {
    executionPagination.current = pag.current
    executionPagination.pageSize = pag.pageSize
  }
  loadExecutionHistory()
}

const getExecutionResultColor = (result: string): string => {
  const colorMap: Record<string, string> = {
    passed: 'green',      // 成功 - 绿色
    success: 'green',     // 成功 - 绿色（别名）
    failed: 'red',        // 失败 - 红色
    error: 'red',         // 错误 - 红色
    cancelled: 'orange',  // 取消 - 橙色
    blocked: 'orange',    // 阻塞 - 橙色
    skipped: 'default',   // 跳过 - 默认灰色
    unknown: 'default'     // 未知 - 默认灰色
  }
  return colorMap[result] || 'default'
}

const getExecutionResultText = (result: string): string => {
  const textMap: Record<string, string> = {
    passed: '成功',
    success: '成功',
    failed: '失败',
    error: '失败',
    cancelled: '取消',
    blocked: '阻塞',
    skipped: '跳过',
    unknown: '未知'
  }
  return textMap[result] || result
}

const formatExecutionDuration = (duration: string | number | undefined | null): string => {
  if (!duration) return '-'
  // 如果duration是字符串，尝试解析（可能是"0:01:23"格式或秒数字符串）
  let seconds: number
  if (typeof duration === 'string') {
    // 尝试解析时间格式（如"0:01:23"）
    const parts = duration.split(':')
    if (parts.length === 3) {
      seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseFloat(parts[2])
    } else {
      // 尝试解析为秒数
      seconds = parseFloat(duration)
    }
  } else {
    seconds = duration
  }

  if (isNaN(seconds) || seconds <= 0) return '-'

  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}分钟`
  } else {
    return `${(seconds / 3600).toFixed(1)}小时`
  }
}

const viewExecutionLogs = async (record: any) => {
  executionLogLoading.value = true
  executionLogModalVisible.value = true
  try {
    // 优先使用logId获取日志，确保每条记录显示对应的日志
    if (record.logId) {
      // 通过logId精确查询日志记录
      const response = await testSuiteApi.getSuiteLogs(record.suiteId, {
        logId: record.logId,
        skip: 0,
        limit: 1
      })
      const logs = response.items || []
      console.log(logs)
      // 验证返回的日志ID是否匹配（防止查询错误）
      if (logs.length > 0 && logs[0].id === record.logId) {
        // 直接取该日志记录的message
        executionLog.value = logs[0].message || '暂无日志'
      } else {
        console.warn(`日志ID不匹配: 期望 ${record.logId}, 实际 ${logs[0]?.id || '无'}`)
        executionLog.value = '暂无日志'
      }
    } else if (record.executionId) {
      // 如果没有logId，使用executionId获取日志（每个execution_id只有一条记录）
      const response = await testSuiteApi.getSuiteLogs(record.suiteId, {
        executionId: record.executionId,
        skip: 0,
        limit: 10000  // 增加到10000，避免日志记录被截断
      })
      const logs = response.items || []
      if (logs.length > 0) {
        // 每个execution_id只有一条记录，直接取第一条的message
        // message字段已经包含了所有日志消息（用换行符分隔）
        executionLog.value = logs[0].message || '暂无日志'
      } else {
        executionLog.value = '暂无日志'
      }
    } else {
      // 如果没有logId和executionId，尝试从suiteId获取最新日志
      const response = await testSuiteApi.getSuiteLogs(record.suiteId, {
        skip: 0,
        limit: 1
      })
      const logs = response.items || []
      if (logs.length > 0) {
        // 只取最新的一条记录的message
        executionLog.value = logs[0].message || '暂无日志'
      } else {
        executionLog.value = '暂无日志'
      }
    }
  } catch (error) {
    console.error('Failed to load execution logs:', error)
    message.error('加载执行日志失败')
    executionLog.value = '加载日志失败'
  } finally {
    executionLogLoading.value = false
  }
}

const deleteEnvironment = (id: string) => {
  const environment = environments.value.find(e => e.id === id)
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境"${environment?.name}"吗？此操作不可恢复。`,
    okType: 'danger',
    onOk: async () => {
      try {
        await environmentApi.deleteEnvironment(id)
        message.success('环境已删除')
        await loadEnvironments()
      } catch (error) {
        console.error('Failed to delete environment:', error)
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.environments-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  overflow: hidden;
}

/* 可滚动内容区域 */
.scrollable-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.environments-content {
  margin: 0;
}

/* 固定底部分页器 */
.fixed-footer {
  position: sticky;
  bottom: 0;
  z-index: 100;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  padding: 16px;
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.env-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.env-icon {
  width: 32px;
  height: 32px;
  background: #f5f5f5;
  color: #bfbfbf;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.3s;
}

.env-icon.online {
  background: #f6ffed;
  color: #52c41a;
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.2);
}

.env-name {
  font-weight: 500;
  font-size: 14px;
}

/* 状态呼吸灯 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #d9d9d9;
  position: relative;
}

.status-dot.online {
  background-color: #52c41a;
  box-shadow: 0 0 0 2px rgba(82, 196, 26, 0.2);
}

.status-dot.online::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: inherit;
  transform: translate(-50%, -50%);
  animation: ripple 1.5s infinite;
}

.status-dot.busy {
  background-color: #faad14;
}

.status-dot.offline {
  background-color: #ff4d4f;
}

@keyframes ripple {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(3);
    opacity: 0;
  }
}

.execution-log {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.filter-section {
  margin-bottom: 16px;
}

.workspace-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-content {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environments-content {
    margin-top: 12px;
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

