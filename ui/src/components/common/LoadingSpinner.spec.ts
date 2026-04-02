/**
 * Component tests for LoadingSpinner
 * Tests loading indicator with customizable message
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from './LoadingSpinner.vue'

describe('LoadingSpinner', () => {
  describe('Rendering', () => {
    it('renders progress circular with message and styling', () => {
      const wrapper = mount(LoadingSpinner, {
        props: { message: 'Loading books...' }
      })

      const progressCircular = wrapper.findComponent({ name: 'VProgressCircular' })
      expect(progressCircular.exists()).toBe(true)
      expect(progressCircular.props('indeterminate')).toBe(true)
      expect(progressCircular.props('color')).toBe('primary')
      expect(progressCircular.props('size')).toBe('64')

      expect(wrapper.text()).toContain('Loading books...')
    })

    it.each(['Please wait', 'Loading data...', 'Fetching content'])(
      'renders message "%s"',
      (message) => {
        const wrapper = mount(LoadingSpinner, {
          props: { message }
        })
        expect(wrapper.text()).toContain(message)
      }
    )
  })

  describe('Structure', () => {
    it('has centered container with styled message', () => {
      const wrapper = mount(LoadingSpinner, {
        props: { message: 'Loading' }
      })

      const container = wrapper.find('.text-center')
      expect(container.exists()).toBe(true)

      const message = wrapper.find('p')
      expect(message.exists()).toBe(true)
      expect(message.classes()).toContain('mt-4')
      expect(message.classes()).toContain('text-body-1')
    })
  })
})
