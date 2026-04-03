/**
 * Unit tests for SortControl component
 * Tests sort selection and order toggle functionality
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SortControl from './SortControl.vue'
import type { SortOption, SortOrder } from '@/types'

const createWrapper = (props: { sortBy: SortOption; sortOrder: SortOrder }) =>
  mount(SortControl, { props })

describe('SortControl', () => {
  it('displays current sort option in select', () => {
    const wrapper = createWrapper({
      sortBy: 'title',
      sortOrder: 'asc'
    })

    const select = wrapper.findComponent({ name: 'VSelect' })
    expect(select.props('modelValue')).toBe('title')
  })

  it('emits update:sortBy when sort option changes', async () => {
    const wrapper = createWrapper({
      sortBy: 'popularity',
      sortOrder: 'desc'
    })

    const select = wrapper.findComponent({ name: 'VSelect' })
    await select.vm.$emit('update:modelValue', 'title')

    const emitted = wrapper.emitted('update:sortBy')
    expect(emitted).toBeDefined()
    expect(emitted![0]).toEqual(['title'])
  })

  it.each([
    { sortOrder: 'asc' as SortOrder, buttonText: 'Ascending', emits: 'desc' },
    { sortOrder: 'desc' as SortOrder, buttonText: 'Descending', emits: 'asc' }
  ])(
    'displays $buttonText button and toggles to $emits',
    async ({ sortOrder, buttonText, emits }) => {
      const wrapper = createWrapper({
        sortBy: 'popularity',
        sortOrder
      })

      expect(wrapper.text()).toContain(buttonText)

      const button = wrapper.find('.v-btn')
      await button.trigger('click')

      expect(wrapper.emitted('update:sortOrder')![0]).toEqual([emits])
    }
  )

  it.each([
    { sortBy: 'popularity' as SortOption, icon: 'mdi-star' },
    { sortBy: 'title' as SortOption, icon: 'mdi-format-title' }
  ])('displays $icon for $sortBy', ({ sortBy, icon }) => {
    const wrapper = createWrapper({
      sortBy,
      sortOrder: 'asc'
    })

    expect(wrapper.html()).toContain(icon)
  })
})
