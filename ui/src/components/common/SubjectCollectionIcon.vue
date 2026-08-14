<script setup lang="ts">
import {
  mdiAccountGroup,
  mdiAtom,
  mdiBank,
  mdiBookEducation,
  mdiBookshelf,
  mdiBriefcase,
  mdiBullhorn,
  mdiCalculatorVariant,
  mdiChartLine,
  mdiCodeBraces,
  mdiCog,
  mdiDatabase,
  mdiDna,
  mdiEarth,
  mdiFlask,
  mdiGavel,
  mdiHandshake,
  mdiHeadLightbulb,
  mdiHeartPulse,
  mdiHospitalBox,
  mdiLibrary,
  mdiLock,
  mdiMicroscope,
  mdiMusic,
  mdiNewspaperVariant,
  mdiPalette,
  mdiPencilRuler,
  mdiRobot,
  mdiScaleBalance,
  mdiSchool,
  mdiSigma,
  mdiSitemap,
  mdiStethoscope,
  mdiTheater,
  mdiTrophyVariant,
  mdiTranslate
} from '@mdi/js'

const props = defineProps<{
  subject: string | null
  fallback?: string
}>()

const SUBJECT_ICONS: Record<string, string> = {
  'Business - Accounting': mdiCalculatorVariant,
  'Business - Entrepreneurship': mdiHeadLightbulb,
  'Business - Finance': mdiBank,
  'Business - Human Resources': mdiAccountGroup,
  'Business - Management': mdiSitemap,
  'Business - Marketing': mdiBullhorn,
  'Computer Science - Artificial Intelligence': mdiRobot,
  'Computer Science - Cryptography': mdiLock,
  'Computer Science - Databases': mdiDatabase,
  'Computer Science - Information Systems': mdiSitemap,
  'Computer Science - Programming Languages': mdiCodeBraces,
  'Education - Curriculum & Instruction': mdiBookEducation,
  'Education - Distance Education': mdiSchool,
  'Education - Early Childhood': mdiAccountGroup,
  'Education - Elementary Education': mdiPencilRuler,
  'Education - Higher Education': mdiLibrary,
  'Education - Secondary Education': mdiSchool,
  'Engineering & Technology - Chemical Engineering': mdiFlask,
  'Engineering & Technology - Civil Engineering': mdiPencilRuler,
  'Engineering & Technology - Electrical Engineering': mdiAtom,
  'Engineering & Technology - Materials Science': mdiCog,
  'Engineering & Technology - Mechanical Engineering': mdiCog,
  'Humanities - Arts': mdiPalette,
  'Humanities - History': mdiLibrary,
  'Humanities - Languages': mdiTranslate,
  'Humanities - Linguistics': mdiTranslate,
  'Humanities - Literature, Rhetoric, and Poetry': mdiBookshelf,
  'Humanities - Music': mdiMusic,
  'Humanities - Philosophy': mdiHeadLightbulb,
  'Humanities - Religion': mdiLibrary,
  'Journalism, Media Studies & Communications - Intercultural Communication': mdiHandshake,
  'Journalism, Media Studies & Communications - New Media Journalism': mdiNewspaperVariant,
  'Journalism, Media Studies & Communications - Organizational Communication': mdiAccountGroup,
  'Journalism, Media Studies & Communications - Print Journalism': mdiNewspaperVariant,
  'Journalism, Media Studies & Communications - Speech Communication': mdiBullhorn,
  'Journalism, Media Studies & Communications - Technical Writing': mdiPencilRuler,
  'Law - Administrative Law': mdiScaleBalance,
  'Law - Civil Law': mdiScaleBalance,
  'Law - Constitutional Law': mdiGavel,
  'Law - Contract Law': mdiHandshake,
  'Law - Criminal Law': mdiGavel,
  'Law - Procedural Law': mdiGavel,
  'Law - Property Law': mdiScaleBalance,
  'Mathematics - Algebra': mdiCalculatorVariant,
  'Mathematics - Analysis': mdiChartLine,
  'Mathematics - Applied': mdiCalculatorVariant,
  'Mathematics - Calculus': mdiChartLine,
  'Mathematics - Geometry and Trigonometry': mdiSigma,
  'Mathematics - Proof': mdiSigma,
  'Mathematics - Pure': mdiSigma,
  'Mathematics - Statistics': mdiChartLine,
  'Medicine - Anatomy': mdiHeartPulse,
  'Medicine - Clinical Physiology': mdiStethoscope,
  'Medicine - Nursing': mdiHospitalBox,
  'Medicine - Nutrition': mdiHeartPulse,
  'Medicine - Pharmacology': mdiHospitalBox,
  'Medicine - Public Health': mdiAccountGroup,
  'Medicine - Veterinary Medicine': mdiStethoscope,
  'Natural Sciences - Biology': mdiDna,
  'Natural Sciences - Chemistry': mdiFlask,
  'Natural Sciences - Earth Sciences': mdiEarth,
  'Natural Sciences - Physics': mdiAtom,
  'Natural Sciences - Space Sciences': mdiAtom,
  'Social Sciences - Anthropology': mdiAccountGroup,
  'Social Sciences - Archeology': mdiLibrary,
  'Social Sciences - Area Studies': mdiEarth,
  'Social Sciences - Cultural & Ethnic Studies': mdiAccountGroup,
  'Social Sciences - Economics': mdiChartLine,
  'Social Sciences - Gender & Sexuality Studies': mdiAccountGroup,
  'Social Sciences - Geography': mdiEarth,
  'Social Sciences - Library Science and Museum Studies': mdiLibrary,
  'Social Sciences - Political Science': mdiAccountGroup,
  'Social Sciences - Psychology': mdiHeadLightbulb,
  'Social Sciences - Sociology': mdiAccountGroup,
  Business: mdiBriefcase,
  'Computer Science': mdiCodeBraces,
  Education: mdiSchool,
  'Engineering & Technology': mdiCog,
  Humanities: mdiTheater,
  'Journalism, Media Studies & Communications': mdiNewspaperVariant,
  Law: mdiScaleBalance,
  Mathematics: mdiCalculatorVariant,
  Medicine: mdiStethoscope,
  'Natural Sciences': mdiMicroscope,
  'Social Sciences': mdiAccountGroup,
  'Student Success': mdiTrophyVariant
}

function getSubjectCollectionIcon(subject: string | null): string {
  return (subject && SUBJECT_ICONS[subject]) || props.fallback || mdiBookshelf
}
</script>

<template>
  <svg class="subject-icon" viewBox="0 0 24 24">
    <path :d="getSubjectCollectionIcon(subject)" />
  </svg>
</template>

<style scoped>
.subject-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: currentColor;
}
</style>
