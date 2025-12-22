export interface User {
  id: string
  username: string
  email: string
  fullName?: string
  phone?: string
  department?: string
  status: boolean
  createdAt: string
  updatedAt: string
}

export interface LoginRequest {
  username: string
  password: string
  remember?: boolean
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  user: User
}

export interface Project {
  id: string
  name: string
  description?: string
  ownerId: string
  status: string
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface Module {
  id: string
  projectId: string
  name: string
  parentId?: string
  level: number
  sortOrder: number
  description?: string
  createdAt: string
  updatedAt: string
}

export interface TestCaseStep {
  step: number
  action: string
  expected: string
}

export interface TestCase {
  id: string
  projectId: string
  moduleId?: string
  caseCode: string
  name: string
  type: 'functional' | 'interface' | 'ui' | 'performance' | 'security'
  priority: 'P0' | 'P1' | 'P2' | 'P3' | 'high' | 'medium' | 'low'
  precondition?: string
  steps: TestCaseStep[]
  expectedResult?: string
  requirementRef?: string
  modulePath?: string
  level?: string
  executorId?: string
  tags: string[]
  status: 'not_executed' | 'passed' | 'failed' | 'blocked' | 'skipped'
  createdAt: string
  updatedAt: string
  createdBy: string
  updatedBy?: string
}

export interface CaseAttachment {
  id: number
  caseId: string
  fileName: string
  filePath: string
  fileSize: number
  fileType: string
  uploadTime: string
  uploadedBy: string
}

export interface TestPlan {
  id: string
  projectId: string
  planNumber: string
  name: string
  description?: string
  ownerId: string
  planType: string
  startDate?: string
  endDate?: string
  cronExpression?: string
  environmentConfig: Record<string, any>
  status: 'not_started' | 'running' | 'completed' | 'paused' | 'overdue'
  environmentId?: string
  createdAt: string
  updatedAt: string
}

export interface TestExecution {
  id: string
  planId?: string
  caseId: string
  executorId: string
  environmentId?: string
  result: 'passed' | 'failed' | 'blocked' | 'skipped'
  duration?: number
  notes?: string
  errorMessage?: string
  executionLog?: string
  executedAt: string
  createdAt: string
}

export interface TestReport {
  id: string
  projectId?: string
  planId?: string
  reportType: string
  reportName: string
  startDate?: string
  endDate?: string
  reportData: Record<string, any>
  summary?: string
  createdBy: string
  createdAt: string
}

export interface Environment {
  id: string
  name: string
  apiUrl?: string
  webUrl?: string
  databaseConfig: Record<string, any>
  envVariables: Record<string, any>
  description?: string
  status: boolean
  createdAt: string
  updatedAt: string
}

export interface Notification {
  id: number
  userId: string
  type: string
  title: string
  content?: string
  isRead: boolean
  relatedId?: string
  createdAt: string
}

export interface ApiResponse<T = any> {
  status: 'success' | 'error' | 'warning'
  message: string
  data?: T
  code: number
  timestamp: string
  requestId?: string
}

export interface PaginationResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
  hasNext: boolean
  hasPrev: boolean
}

export interface TreeNode {
  key: string
  title: string
  type: 'project' | 'module' | 'case'
  children?: TreeNode[]
  level?: string
  tags?: string[]
  caseCode?: string
}

export interface DropInfo {
  dragNode: TreeNode
  node: TreeNode
  dropPosition: -1 | 0 | 1
}

export interface DashboardStats {
  totalCases: number
  passRate: number
  automatedCoverage: number
  totalExecutions: number
  recentExecutions: TestExecution[]
  executionTrend: Array<{
    date: string
    count: number
    passCount: number
  }>
  planProgress: Array<{
    planName: string
    progress: number
    status: string
  }>
  moduleCoverage: Array<{
    moduleName: string
    totalCases: number
    executedCases: number
    passRate: number
  }>
}

export interface Report {
  id: string
  name: string
  reportNumber: string
  type: 'summary' | 'detailed' | 'trend' | 'coverage'
  status: 'generating' | 'completed' | 'failed'
  format: 'pdf' | 'excel' | 'html'
  fileSize: number
  createdAt: string
  creatorId: string
  creatorName: string
  downloadUrl?: string
  previewUrl?: string
  projectId?: string
  notes?: string
  completedAt?: string
  progress?: number
  currentStep?: string
  errorMessage?: string
  errorDetails?: string
  startDate?: string
  endDate?: string
  includeContent?: string[]
  filters?: {
    projectIds?: string[]
    planIds?: string[]
    moduleIds?: string[]
  }
  summary?: string
  totalCases?: number
  executedCases?: number
  passedCases?: number
  failedCases?: number
  totalPlans?: number
  totalProjects?: number
  totalExecutionTime?: number
}