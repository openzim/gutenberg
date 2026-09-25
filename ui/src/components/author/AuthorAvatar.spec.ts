/**
 * Component tests for AuthorAvatar
 */

import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import AuthorAvatar from './AuthorAvatar.vue'
import { normalizeImagePath } from '@/utils/format-utils'

vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }))

describe('AuthorAvatar', () => {
  it('renders an account icon placeholder when no portrait is available', () => {
    const wrapper = mount(AuthorAvatar, { props: { name: 'Jane Austen' } })

    const avatar = wrapper.findComponent({ name: 'VAvatar' })
    expect(avatar.exists()).toBe(true)
    expect(avatar.findComponent({ name: 'VImg' }).exists()).toBe(false)
    expect(avatar.findComponent({ name: 'VIcon' }).props('icon')).toBe('mdi-account')
  })

  it('renders the portrait image with the correct source and alt', () => {
    const wrapper = mount(AuthorAvatar, {
      props: { name: 'Jane Austen', portraitPath: './authors/austen-jane.webp' }
    })

    const avatar = wrapper.findComponent({ name: 'VAvatar' })
    const portrait = avatar.findComponent({ name: 'VImg' })
    expect(portrait.exists()).toBe(true)
    expect(portrait.props('src')).toBe(normalizeImagePath('./authors/austen-jane.webp'))
    expect(portrait.props('cover')).toBe(true)
    expect(portrait.props('alt')).toBe('Jane Austen')

    const placeholder = portrait.findComponent({ name: 'VIcon' })
    expect(placeholder.exists()).toBe(true)
    expect(placeholder.props('icon')).toBe('mdi-account')
  })

  it('falls back to the account icon when the portrait fails to load', async () => {
    const wrapper = mount(AuthorAvatar, {
      props: { name: 'Jane Austen', portraitPath: './authors/austen-jane.webp' }
    })

    const avatar = wrapper.findComponent({ name: 'VAvatar' })
    expect(avatar.findComponent({ name: 'VImg' }).exists()).toBe(true)

    await avatar.find('img').trigger('error')
    await nextTick()

    expect(avatar.findComponent({ name: 'VImg' }).exists()).toBe(false)
    expect(avatar.findComponent({ name: 'VIcon' }).props('icon')).toBe('mdi-account')
  })

  it.each([
    { variant: 'compact', avatar: 48, icon: 28 },
    { variant: 'comfortable', avatar: 100, icon: 80 },
    { variant: 'full', avatar: 160, icon: 100 }
  ])('maps variant $variant to the right avatar/icon sizes', ({ variant, avatar, icon }) => {
    const wrapper = mount(AuthorAvatar, {
      props: { name: 'Jane Austen', variant: variant as 'compact' | 'comfortable' | 'full' }
    })

    const vAvatar = wrapper.findComponent({ name: 'VAvatar' })
    expect(vAvatar.props('size')).toBe(avatar)
    expect(vAvatar.props('color')).toBe('rgb(var(--v-theme-authorAvatarBgd))')
    expect(vAvatar.findComponent({ name: 'VIcon' }).props('size')).toBe(icon)
  })
})
