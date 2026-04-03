/**
 * Unit tests for BaseFilter component
 * Tests multi-select filter with toggle, clear, and select all functionality
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseFilter from './BaseFilter.vue'

const createWrapper = (props: {
  title: string
  icon: string
  items: string[]
  modelValue: string[]
  emptyMessage?: string
  iconMap?: Record<string, string>
}) =>
  mount(BaseFilter, {
    props,
    global: {
      stubs: {
        EmptyState: { template: '<div class="empty-state">{{ message }}</div>', props: ['message'] }
      }
    }
  })

describe('BaseFilter', () => {
  const defaultProps = {
    title: 'Format',
    icon: 'mdi-file',
    items: ['html', 'epub', 'pdf'],
    modelValue: []
  }

  it('renders filter with title, icon, and chips for all items', () => {
    const wrapper = createWrapper(defaultProps)

    expect(wrapper.text()).toContain('Format')
    expect(wrapper.html()).toContain('mdi-file')
    const chips = wrapper.findAll('.v-chip')
    expect(chips).toHaveLength(3)
    expect(chips[0]!.text()).toContain('HTML')
    expect(chips[1]!.text()).toContain('EPUB')
    expect(chips[2]!.text()).toContain('PDF')
  })

  it('emits update:modelValue when chip is clicked', async () => {
    const wrapper = createWrapper(defaultProps)

    await wrapper.findAll('.v-chip')[0]!.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([['html']])
  })

  it('shows selected chips with primary color', () => {
    const wrapper = createWrapper({
      ...defaultProps,
      modelValue: ['html', 'pdf']
    })

    const chips = wrapper.findAll('.v-chip')
    expect(chips[0]!.classes()).toContain('v-chip--variant-flat')
    expect(chips[1]!.classes()).not.toContain('v-chip--variant-flat')
    expect(chips[2]!.classes()).toContain('v-chip--variant-flat')
  })

  it.each([
    { modelValue: ['html'], hasClear: true, hasAll: true },
    { modelValue: [], hasClear: false, hasAll: true },
    { modelValue: ['html', 'epub', 'pdf'], hasClear: true, hasAll: false }
  ])('shows correct buttons when modelValue is $modelValue', ({ modelValue, hasClear, hasAll }) => {
    const wrapper = createWrapper({ ...defaultProps, modelValue })

    const clearBtn = wrapper.findAll('.v-btn').find((btn) => btn.text().includes('Clear'))
    const allBtn = wrapper.findAll('.v-btn').find((btn) => btn.text().includes('All'))

    expect(!!clearBtn).toBe(hasClear)
    expect(!!allBtn).toBe(hasAll)
  })

  it('emits clear all when Clear button clicked', async () => {
    const wrapper = createWrapper({
      ...defaultProps,
      modelValue: ['html', 'pdf']
    })

    const clearBtn = wrapper.findAll('.v-btn').find((btn) => btn.text().includes('Clear'))
    await clearBtn!.trigger('click')

    expect(wrapper.emitted('update:modelValue')![0]).toEqual([[]])
  })

  it('emits select all when All button clicked', async () => {
    const wrapper = createWrapper(defaultProps)

    const allBtn = wrapper.findAll('.v-btn').find((btn) => btn.text().includes('All'))
    await allBtn!.trigger('click')

    expect(wrapper.emitted('update:modelValue')![0]).toEqual([['html', 'epub', 'pdf']])
  })

  it('renders icons for items when iconMap provided', () => {
    const wrapper = createWrapper({
      ...defaultProps,
      iconMap: { html: 'mdi-language-html5', epub: 'mdi-book' }
    })

    expect(wrapper.html()).toContain('mdi-language-html5')
    expect(wrapper.html()).toContain('mdi-book')
  })

  it('shows empty state when no items', () => {
    const wrapper = createWrapper({
      ...defaultProps,
      items: [],
      emptyMessage: 'No formats available'
    })

    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.empty-state').text()).toBe('No formats available')
  })

  it('handles keyboard navigation', async () => {
    const wrapper = createWrapper(defaultProps)

    await wrapper.findAll('.v-chip')[0]!.trigger('keydown.enter')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([['html']])
  })
})
