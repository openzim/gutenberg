/**
 * Component tests for BackToTopButton
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import BackToTopButton from './BackToTopButton.vue'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'common.backToTop': 'Back to top'
      }
      return translations[key] || key
    }
  })
}))

function setScrollY(value: number) {
  Object.defineProperty(window, 'scrollY', { value, writable: true, configurable: true })
  window.dispatchEvent(new Event('scroll'))
}

describe('BackToTopButton', () => {
  beforeEach(() => {
    setScrollY(0)
  })

  afterEach(() => {
    setScrollY(0)
  })

  describe('Visibility', () => {
    it('is hidden before any scrolling', () => {
      const wrapper = mount(BackToTopButton)

      const button = wrapper.find('.back-to-top')
      expect(button.classes()).not.toContain('back-to-top--visible')
      expect(button.attributes('aria-hidden')).toBe('true')
      expect(button.attributes('tabindex')).toBe('-1')
    })

    it('becomes visible once scrolled past the threshold', async () => {
      const wrapper = mount(BackToTopButton)

      setScrollY(500)
      await wrapper.vm.$nextTick()

      const button = wrapper.find('.back-to-top')
      expect(button.classes()).toContain('back-to-top--visible')
      expect(button.attributes('aria-hidden')).toBe('false')
      expect(button.attributes('tabindex')).toBe('0')
    })

    it('hides again when scrolling back near the top', async () => {
      const wrapper = mount(BackToTopButton)

      setScrollY(500)
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.back-to-top').classes()).toContain('back-to-top--visible')

      setScrollY(0)
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.back-to-top').classes()).not.toContain('back-to-top--visible')
    })
  })

  describe('Interaction', () => {
    it('scrolls to top when clicked', async () => {
      const scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
      const wrapper = mount(BackToTopButton)

      await wrapper.find('.back-to-top').trigger('click')

      expect(scrollToSpy).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
      scrollToSpy.mockRestore()
    })

    it('has an accessible label', () => {
      const wrapper = mount(BackToTopButton)

      expect(wrapper.find('.back-to-top').attributes('aria-label')).toBe('Back to top')
    })

    it('renders a visible svg icon with a path', () => {
      const wrapper = mount(BackToTopButton)

      const svg = wrapper.find('svg.back-to-top-icon')
      expect(svg.exists()).toBe(true)
      expect(svg.find('path').attributes('d')).toBeTruthy()
    })
  })

  describe('Cleanup', () => {
    it('removes the scroll listener on unmount', () => {
      const removeSpy = vi.spyOn(window, 'removeEventListener')
      const wrapper = mount(BackToTopButton)

      wrapper.unmount()

      expect(removeSpy).toHaveBeenCalledWith('scroll', expect.any(Function))
      removeSpy.mockRestore()
    })
  })
})
