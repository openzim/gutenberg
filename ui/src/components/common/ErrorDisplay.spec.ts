/**
 * Component tests for ErrorDisplay
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ErrorDisplay from './ErrorDisplay.vue'
import { useMainStore } from '@/stores/main'

describe('ErrorDisplay', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('Rendering', () => {
    it('displays error message with VAlert properties', async () => {
      const wrapper = mount(ErrorDisplay)
      const store = useMainStore()
      store.errorMessage = 'Failed to load data'

      await wrapper.vm.$nextTick()
      expect(wrapper.text()).toContain('Error')
      expect(wrapper.text()).toContain('Failed to load data')

      const alert = wrapper.findComponent({ name: 'VAlert' })
      expect(alert.exists()).toBe(true)
      expect(alert.props('type')).toBe('error')
      expect(alert.props('variant')).toBe('tonal')
      expect(alert.props('prominent')).toBe(true)
      expect(alert.props('closable')).toBe(true)
    })

    it('renders inside v-container', async () => {
      const wrapper = mount(ErrorDisplay)
      const store = useMainStore()
      store.errorMessage = 'Test error'

      await wrapper.vm.$nextTick()
      expect(wrapper.findComponent({ name: 'VContainer' }).exists()).toBe(true)
    })
  })

  describe('Accessibility', () => {
    it('has correct ARIA attributes', async () => {
      const wrapper = mount(ErrorDisplay)
      const store = useMainStore()
      store.errorMessage = 'Test error'

      await wrapper.vm.$nextTick()
      const alert = wrapper.findComponent({ name: 'VAlert' })
      expect(alert.attributes('role')).toBe('alert')
      expect(alert.attributes('aria-live')).toBe('assertive')
      expect(alert.attributes('aria-atomic')).toBe('true')
    })
  })

  describe('Interaction', () => {
    it('calls clearError when close button is clicked', async () => {
      const wrapper = mount(ErrorDisplay)
      const store = useMainStore()
      store.errorMessage = 'Test error'

      await wrapper.vm.$nextTick()
      const clearErrorSpy = vi.spyOn(store, 'clearError')

      const alert = wrapper.findComponent({ name: 'VAlert' })
      await alert.vm.$emit('click:close')

      expect(clearErrorSpy).toHaveBeenCalledOnce()
    })
  })

  describe('Error Message Variations', () => {
    it.each([
      ['simple error', 'Error'],
      [
        'long error',
        'This is a very long error message that contains multiple sentences and detailed information about what went wrong during the operation.'
      ],
      ['path with special chars', 'Error: Failed to load "data.json" from /path/to/file'],
      ['HTML-like chars', 'Error: Value must be < 100 & > 0']
    ])('displays %s: %s', async (_description, message) => {
      const wrapper = mount(ErrorDisplay)
      const store = useMainStore()
      store.errorMessage = message

      await wrapper.vm.$nextTick()
      expect(wrapper.text()).toContain(message)
    })
  })

  describe('Store Integration', () => {
    it('reacts to store error message changes', async () => {
      const wrapper = mount(ErrorDisplay)
      const store = useMainStore()

      store.errorMessage = 'First error'
      await wrapper.vm.$nextTick()
      expect(wrapper.text()).toContain('First error')

      store.errorMessage = 'Second error'
      await wrapper.vm.$nextTick()
      expect(wrapper.text()).toContain('Second error')
      expect(wrapper.text()).not.toContain('First error')
    })
  })
})
