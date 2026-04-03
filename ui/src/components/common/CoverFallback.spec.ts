/**
 * Component tests for CoverFallback
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CoverFallback from './CoverFallback.vue'

describe('CoverFallback', () => {
  describe('Default Rendering', () => {
    it('renders div with icon using defaults', () => {
      const wrapper = mount(CoverFallback)

      const div = wrapper.find('.no-cover')
      expect(div.exists()).toBe(true)
      expect(div.attributes('style')).toBeFalsy()

      const icon = wrapper.findComponent({ name: 'VIcon' })
      expect(icon.exists()).toBe(true)
      expect(icon.props('icon')).toBe('mdi-book')
      expect(icon.props('size')).toBe(64)
    })
  })

  describe('Custom Props', () => {
    it.each(['mdi-image', 'mdi-file', 'mdi-book-open', 'mdi-library'])(
      'accepts custom icon: %s',
      (iconName) => {
        const wrapper = mount(CoverFallback, {
          props: { icon: iconName }
        })

        expect(wrapper.findComponent({ name: 'VIcon' }).props('icon')).toBe(iconName)
      }
    )

    it.each([32, 120, 256])('accepts custom size: %i', (size) => {
      const wrapper = mount(CoverFallback, {
        props: { size }
      })

      expect(wrapper.findComponent({ name: 'VIcon' }).props('size')).toBe(size)
    })

    it.each(['200px', '150px', '10rem', '50vh', '100%'])('accepts custom height: %s', (height) => {
      const wrapper = mount(CoverFallback, {
        props: { height }
      })

      expect(wrapper.find('.no-cover').attributes('style')).toContain(`height: ${height}`)
    })

    it('does not apply height style when not provided', () => {
      const wrapper = mount(CoverFallback)

      expect(wrapper.find('.no-cover').attributes('style')).toBeFalsy()
    })
  })

  describe('Combined Props', () => {
    it('handles all props together', () => {
      const wrapper = mount(CoverFallback, {
        props: {
          size: 80,
          icon: 'mdi-library',
          height: '250px'
        }
      })

      const icon = wrapper.findComponent({ name: 'VIcon' })
      expect(icon.props('size')).toBe(80)
      expect(icon.props('icon')).toBe('mdi-library')

      expect(wrapper.find('.no-cover').attributes('style')).toContain('height: 250px')
    })

    it('handles partial props with defaults', () => {
      const wrapper = mount(CoverFallback, {
        props: {
          height: '180px'
        }
      })

      const icon = wrapper.findComponent({ name: 'VIcon' })
      expect(icon.props('size')).toBe(64)
      expect(icon.props('icon')).toBe('mdi-book')

      expect(wrapper.find('.no-cover').attributes('style')).toContain('height: 180px')
    })
  })

  describe('Edge Cases', () => {
    it('handles falsy size with default fallback', () => {
      const wrapper = mount(CoverFallback, {
        props: { size: 0 }
      })

      expect(wrapper.findComponent({ name: 'VIcon' }).props('size')).toBe(64)
    })

    it('handles falsy height without applying style', () => {
      const wrapper = mount(CoverFallback, {
        props: { height: '' }
      })

      expect(wrapper.find('.no-cover').attributes('style')).toBeFalsy()
    })

    it('handles undefined props gracefully', () => {
      const wrapper = mount(CoverFallback, {
        props: {
          size: undefined,
          icon: undefined,
          height: undefined
        }
      })

      const icon = wrapper.findComponent({ name: 'VIcon' })
      expect(icon.props('size')).toBe(64)
      expect(icon.props('icon')).toBe('mdi-book')

      expect(wrapper.find('.no-cover').attributes('style')).toBeFalsy()
    })
  })

  describe('Structure', () => {
    it('has correct DOM structure', () => {
      const wrapper = mount(CoverFallback)

      expect(wrapper.findAll('div')).toHaveLength(1)
      expect(wrapper.findAllComponents({ name: 'VIcon' })).toHaveLength(1)

      const div = wrapper.find('.no-cover')
      expect(div.findComponent({ name: 'VIcon' }).exists()).toBe(true)
    })
  })
})
