/**
 * i18n Configuration
 *
 * Internationalization setup using react-i18next.
 * Supports multiple languages with browser language detection.
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import en from './locales/en.json';
import fr from './locales/fr.json';
import de from './locales/de.json';
import es from './locales/es.json';
import ja from './locales/ja.json';
import zh from './locales/zh.json';
import pt from './locales/pt.json';
import ko from './locales/ko.json';
import it from './locales/it.json';
import ar from './locales/ar.json';

const resources = {
  en: { translation: en },
  fr: { translation: fr },
  de: { translation: de },
  es: { translation: es },
  ja: { translation: ja },
  zh: { translation: zh },
  pt: { translation: pt },
  ko: { translation: ko },
  it: { translation: it },
  ar: { translation: ar },
};

// RTL languages
const RTL_LANGUAGES = ['ar'];

// Check if a language is RTL
export const isRTL = (lang?: string): boolean => {
  const language = lang ?? i18n.language;
  return RTL_LANGUAGES.includes(language);
};

// Apply text direction to the HTML root element
const applyDirection = (lang: string) => {
  const dir = isRTL(lang) ? 'rtl' : 'ltr';
  document.documentElement.dir = dir;
  document.documentElement.lang = lang;
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: import.meta.env.DEV,

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
  });

// Apply direction on initial load and when language changes
i18n.on('initialized', () => {
  applyDirection(i18n.language);
});

i18n.on('languageChanged', (lang: string) => {
  applyDirection(lang);
});

export default i18n;

// Helper to change language programmatically
export const changeLanguage = (lang: string) => {
  i18n.changeLanguage(lang);
  localStorage.setItem('i18nextLng', lang);
};

// Get current language
export const getCurrentLanguage = () => i18n.language;

// Available languages
export const availableLanguages = [
  { code: 'en', name: 'English' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'es', name: 'Español' },
  { code: 'ja', name: '日本語' },
  { code: 'zh', name: '中文' },
  { code: 'pt', name: 'Português' },
  { code: 'ko', name: '한국어' },
  { code: 'it', name: 'Italiano' },
  { code: 'ar', name: 'العربية' },
];
