/* global Buffer, console */
/**
 * Extracts translated language names from CLDR data for use at runtime.
 * Only includes the language codes used in Gutenberg and only for UI locales
 * that have CLDR translations available. This keeps the bundle minimal (~52KB)
 * instead of shipping the full 25MB CLDR package.
 *
 * Run: node scripts/generate-language-names.js
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'

const __dirname = dirname(fileURLToPath(import.meta.url))
const require = createRequire(import.meta.url)

const cldrBase = dirname(require.resolve('cldr-localenames-full/package.json'))

// Language codes used in Gutenberg books
const LANG_CODES = [
  'af', 'ale', 'ang', 'ar', 'arp', 'bg', 'bgs', 'bo', 'br', 'brx',
  'ca', 'ceb', 'cs', 'csb', 'cy', 'da', 'de', 'el', 'en', 'enm',
  'eo', 'es', 'et', 'fa', 'fi', 'fr', 'fur', 'fy', 'ga', 'gl',
  'gla', 'grc', 'hai', 'he', 'hu', 'ia', 'ilo', 'is', 'it', 'iu',
  'ja', 'kha', 'kld', 'ko', 'la', 'lt', 'mi', 'myn', 'nah', 'nai',
  'nap', 'nav', 'nl', 'no', 'oc', 'oji', 'pl', 'pt', 'rmq', 'ro',
  'ru', 'sa', 'sco', 'sl', 'sr', 'sv', 'te', 'tl', 'yi', 'zh'
]

// Map Project Gutenberg catalog codes to CLDR/ISO 639-1 equivalents.
// Gutenberg uses ISO 639-3 codes for these languages, while CLDR uses
// the shorter ISO 639-1 codes for lookup.
const CODE_TO_CLDR = {
  gla: 'gd', // Scottish Gaelic
  nav: 'nv', // Navajo
  oji: 'oj'  // Ojibwa
}

// UI locales derived from locales/*.json filenames
const localesDir = resolve(__dirname, '../../locales')
const UI_LOCALES = readdirSync(localesDir)
  .filter((f) => f.endsWith('.json') && f !== 'qqq.json')
  .map((f) => f.replace('.json', ''))

const result = {}

for (const locale of UI_LOCALES) {
  const filePath = resolve(cldrBase, 'main', locale, 'languages.json')
  if (!existsSync(filePath)) continue

  const data = JSON.parse(readFileSync(filePath, 'utf-8'))
  const cldrKey = Object.keys(data.main)[0]
  const languages = data.main[cldrKey].localeDisplayNames.languages

  const localeData = {}
  for (const code of LANG_CODES) {
    const cldrCode = CODE_TO_CLDR[code] || code
    if (languages[cldrCode]) {
      localeData[code] = languages[cldrCode]
    }
  }

  if (Object.keys(localeData).length > 0) {
    result[locale] = localeData
  }
}

const outPath = resolve(__dirname, '../src/generated/language-names.json')
mkdirSync(dirname(outPath), { recursive: true })
writeFileSync(outPath, JSON.stringify(result) + '\n')

const size = Buffer.byteLength(JSON.stringify(result))
const localeCount = Object.keys(result).length
console.log(`Generated ${outPath}`)
console.log(`  ${localeCount} locales, ${size} bytes (${(size / 1024).toFixed(1)} KB)`)
