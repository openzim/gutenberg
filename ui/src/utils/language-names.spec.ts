import { describe, it, expect } from 'vitest'
import { getLanguageName, getAutonym, isRtl, isKnown } from './language-names'

describe('getLanguageName', () => {
  it('returns CLDR-translated name for known locale', () => {
    expect(getLanguageName('de', 'en')).toBe('German')
    expect(getLanguageName('de', 'fr')).toBe('allemand')
  })

  it('falls back to English when locale has no CLDR data', () => {
    expect(getLanguageName('de', 'zzz')).toBe('German')
  })

  it('maps variant codes to CLDR keys', () => {
    expect(getLanguageName('gla', 'en')).toBe('Scottish Gaelic')
    expect(getLanguageName('nav', 'en')).toBe('Navajo')
    expect(getLanguageName('oji', 'en')).toBe('Ojibwa')
  })

  it('returns hardcoded fallback for codes not in CLDR', () => {
    expect(getLanguageName('myn', 'en')).toBe('Mayan')
    expect(getLanguageName('kld', 'en')).toBe('Gamilaraay')
  })

  it('returns the code when nothing is found', () => {
    expect(getLanguageName('xyz', 'en')).toBe('xyz')
  })
})

describe('getAutonym', () => {
  it('returns autonym for known languages', () => {
    expect(getAutonym('fr')).toBe('français')
    expect(getAutonym('de')).toBe('Deutsch')
  })

  it('returns code for unknown languages', () => {
    expect(getAutonym('xyz')).toBe('xyz')
  })
})

describe('isRtl', () => {
  it('returns true for RTL languages', () => {
    expect(isRtl('ar')).toBe(true)
    expect(isRtl('he')).toBe(true)
  })

  it('returns false for LTR languages', () => {
    expect(isRtl('en')).toBe(false)
    expect(isRtl('fr')).toBe(false)
  })
})

describe('isKnown', () => {
  it('returns true for known language codes', () => {
    expect(isKnown('en')).toBe(true)
    expect(isKnown('fr')).toBe(true)
  })

  it('returns true for mapped variant codes', () => {
    expect(isKnown('gla')).toBe(true)
  })

  it('returns true for fallback codes', () => {
    expect(isKnown('myn')).toBe(true)
  })
})
