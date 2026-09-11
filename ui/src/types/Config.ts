export interface SourceInfo {
  slug: string
  name: string
  description: string
}

export interface ThemeConfig {
  formatIcons: Record<string, string>
  routeLabels: Record<string, string>
  collectionIconStyle: 'classification' | 'subject'
}

export interface FeatureFlags {
  epubReader: boolean
  pdfReader: boolean
  noscriptFallback: boolean
}

export interface Config {
  title: string
  description: string | null
  source: SourceInfo
  theme: ThemeConfig
  features: FeatureFlags
}
