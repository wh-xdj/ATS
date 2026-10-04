import type { TestCase } from '@/types'

/** Translate editable camelCase fields to the backend's request schema. */
export const casePayload = (data: Partial<TestCase>): Record<string, unknown> => {
  const fields: Record<string, string> = {
    caseCode: 'case_code', moduleId: 'module_id', executorId: 'executor_id',
    requirementRef: 'requirement_ref',
    modulePath: 'module_path', isAutomated: 'is_automated'
  }
  return Object.fromEntries(
    Object.entries(data).map(([key, value]) => [fields[key] || key, value])
  )
}
