import { describe, expect, it, vi } from 'vitest'
import { casePayload } from './casePayload'

const calls = vi.hoisted(() => ({ post: vi.fn(), put: vi.fn() }))
vi.mock('@/utils/api', () => ({ apiClient: calls }))
import { testCaseApi } from '@/api/testCase'

describe('editable case request schema', () => {
  it('keeps false automation and null module values when converting field names', () => {
    expect(casePayload({ name: 'Case', isAutomated: false, moduleId: null, requirementRef: 'REQ-1' })).toEqual({
      name: 'Case', is_automated: false, module_id: null, requirement_ref: 'REQ-1'
    })
  })

  it('uses the same mapping for create and update requests', async () => {
    const fields = { isAutomated: true, moduleId: 'module', requirementRef: 'REQ-2' }
    await testCaseApi.createTestCase('project', fields)
    await testCaseApi.updateTestCase('project', 'case', fields)
    const body = { project_id: 'project', is_automated: true, module_id: 'module', requirement_ref: 'REQ-2' }
    expect(calls.post).toHaveBeenCalledWith('/test-cases', body)
    expect(calls.put).toHaveBeenCalledWith('/test-cases/case', body)
  })
})
