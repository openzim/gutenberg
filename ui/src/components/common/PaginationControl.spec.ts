/**
 * Unit tests for PaginationControl component
 * Tests pagination navigation control
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PaginationControl from './PaginationControl.vue'

const createWrapper = (props: { currentPage: number; totalPages: number }) =>
  mount(PaginationControl, { props })

describe('PaginationControl', () => {
  it.each([
    { currentPage: 1, totalPages: 0, shouldRender: false },
    { currentPage: 1, totalPages: 1, shouldRender: false },
    { currentPage: 1, totalPages: 2, shouldRender: true },
    { currentPage: 5, totalPages: 10, shouldRender: true }
  ])(
    'renders pagination when totalPages is $totalPages',
    ({ currentPage, totalPages, shouldRender }) => {
      const wrapper = createWrapper({ currentPage, totalPages })

      expect(wrapper.findComponent({ name: 'VPagination' }).exists()).toBe(shouldRender)
    }
  )

  it('passes correct props to v-pagination', () => {
    const wrapper = createWrapper({
      currentPage: 3,
      totalPages: 10
    })

    const pagination = wrapper.findComponent({ name: 'VPagination' })
    expect(pagination.props('modelValue')).toBe(3)
    expect(pagination.props('length')).toBe(10)
  })

  it('emits go-to-page when page changes', async () => {
    const wrapper = createWrapper({
      currentPage: 1,
      totalPages: 5
    })

    const pagination = wrapper.findComponent({ name: 'VPagination' })
    await pagination.vm.$emit('update:modelValue', 3)

    const emittedEvents = wrapper.emitted('go-to-page')
    expect(emittedEvents).toBeDefined()
    expect(emittedEvents![0]).toEqual([3])
  })
})
