import {
  companyKeys, searchKeys, tenantKeys, dashboardKeys, company360Keys,
  employeeKeys, contactKeys, activityKeys, taskKeys, opportunityKeys,
  pipelineKeys, adminKeys, decisionKeys,
} from '../queryKeys'

describe('queryKeys', () => {
  describe('companyKeys', () => {
    it('all returns companies', () => {
      expect(companyKeys.all).toEqual(['companies'])
    })
    it('lists returns companies list', () => {
      expect(companyKeys.lists()).toEqual(['companies', 'list'])
    })
    it('list includes filters', () => {
      expect(companyKeys.list({ status: 'active' })).toEqual(['companies', 'list', { status: 'active' }])
    })
    it('details returns companies detail', () => {
      expect(companyKeys.details()).toEqual(['companies', 'detail'])
    })
    it('detail includes id', () => {
      expect(companyKeys.detail('c-1')).toEqual(['companies', 'detail', 'c-1'])
    })
  })

  describe('searchKeys', () => {
    it('results includes query and filters', () => {
      expect(searchKeys.results('test', { type: 'company' })).toEqual(['search', 'test', { type: 'company' }])
    })
    it('suggestions includes query and field', () => {
      expect(searchKeys.suggestions('acme', 'name')).toEqual(['search', 'suggest', 'acme', 'name'])
    })
  })

  describe('tenantKeys', () => {
    it('detail includes tenant id', () => {
      expect(tenantKeys.detail('t-1')).toEqual(['tenants', 't-1'])
    })
  })

  describe('dashboardKeys', () => {
    it('stats returns dashboard stats', () => {
      expect(dashboardKeys.stats()).toEqual(['dashboard', 'stats'])
    })
    it('exec returns dashboard executive', () => {
      expect(dashboardKeys.exec()).toEqual(['dashboard', 'executive'])
    })
    it('main returns dashboard main', () => {
      expect(dashboardKeys.main()).toEqual(['dashboard', 'main'])
    })
  })

  describe('company360Keys', () => {
    it('detail includes id', () => {
      expect(company360Keys.detail('c-1')).toEqual(['company360', 'c-1'])
    })
  })

  describe('employeeKeys', () => {
    it('me returns employees me', () => {
      expect(employeeKeys.me()).toEqual(['employees', 'me'])
    })
  })

  describe('contactKeys', () => {
    it('lists returns contacts list', () => {
      expect(contactKeys.lists()).toEqual(['contacts', 'list'])
    })
    it('list includes filters', () => {
      expect(contactKeys.list({ email: 'a@b.com' })).toEqual(['contacts', 'list', { email: 'a@b.com' }])
    })
  })

  describe('activityKeys', () => {
    it('entity returns scoped key', () => {
      expect(activityKeys.entity('company', 'c-1')).toEqual(['activities', 'company', 'c-1'])
    })
  })

  describe('taskKeys', () => {
    it('list without filters returns undefined', () => {
      expect(taskKeys.list()).toEqual(['tasks', 'list', undefined])
    })
  })

  describe('opportunityKeys', () => {
    it('list returns opportunities list', () => {
      expect(opportunityKeys.list()).toEqual(['opportunities', 'list'])
    })
  })

  describe('pipelineKeys', () => {
    it('list returns pipelines list', () => {
      expect(pipelineKeys.list()).toEqual(['pipelines', 'list'])
    })
  })

  describe('adminKeys', () => {
    it('metrics returns admin metrics', () => {
      expect(adminKeys.metrics()).toEqual(['admin', 'metrics'])
    })
    it('health returns admin health', () => {
      expect(adminKeys.health()).toEqual(['admin', 'health'])
    })
    it('dlqStats returns admin dlq stats', () => {
      expect(adminKeys.dlqStats()).toEqual(['admin', 'dlq', 'stats'])
    })
  })

  describe('decisionKeys', () => {
    it('evaluate returns decisions evaluate', () => {
      expect(decisionKeys.evaluate()).toEqual(['decisions', 'evaluate'])
    })
    it('explain includes id', () => {
      expect(decisionKeys.explain('dec-1')).toEqual(['decisions', 'explain', 'dec-1'])
    })
    it('history includes tenantId', () => {
      expect(decisionKeys.history('t-1')).toEqual(['decisions', 'history', 't-1'])
    })
    it('recommendations includes entityId', () => {
      expect(decisionKeys.recommendations('e-1')).toEqual(['decisions', 'recommendations', 'e-1'])
    })
  })
})
