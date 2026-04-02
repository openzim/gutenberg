/**
 * Component tests for EmptyState
 * Tests empty state alert with different types and messages
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EmptyState from './EmptyState.vue'

describe('EmptyState', () => {
  describe('Rendering', () => {
    it('renders VAlert with message and tonal variant', () => {
      const wrapper = mount(EmptyState, {
        props: { message: 'No items found' }
      })

      const alert = wrapper.findComponent({ name: 'VAlert' })
      expect(alert.exists()).toBe(true)
      expect(alert.props('variant')).toBe('tonal')
      expect(wrapper.text()).toContain('No items found')
    })

    it.each(['No results', 'Empty list', 'Nothing to display'])(
      'renders message "%s"',
      (message) => {
        const wrapper = mount(EmptyState, {
          props: { message }
        })
        expect(wrapper.text()).toContain(message)
      }
    )
  })

  describe('Alert Types', () => {
    it('uses info type by default', () => {
      const wrapper = mount(EmptyState, {
        props: { message: 'Test message' }
      })

      expect(wrapper.findComponent({ name: 'VAlert' }).props('type')).toBe('info')
    })

    it.each(['info', 'warning', 'error', 'success'] as const)('accepts alert type "%s"', (type) => {
      const wrapper = mount(EmptyState, {
        props: { message: 'Test message', type }
      })

      expect(wrapper.findComponent({ name: 'VAlert' }).props('type')).toBe(type)
    })
  })

  describe('Edge Cases', () => {
    it.each([
      {
        message:
          'This is a very long message that explains in detail why there are no items to display.',
        expected:
          'This is a very long message that explains in detail why there are no items to display.'
      },
      { message: 'No <items> & "results" found', expected: 'No <items> & "results" found' }
    ])('handles message: $message', ({ message, expected }) => {
      const wrapper = mount(EmptyState, {
        props: { message }
      })

      expect(wrapper.text()).toContain(expected)
    })
  })
})
