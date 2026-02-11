/**
 * CLI i18n configuration using i18next
 *
 * Initializes i18next in synchronous mode for use throughout the CLI.
 * Language selection: --lang flag > LANG env variable > 'en' default.
 */

import i18next from 'i18next';
import en from './locales/en.json' with { type: 'json' };
import fr from './locales/fr.json' with { type: 'json' };
import de from './locales/de.json' with { type: 'json' };
import es from './locales/es.json' with { type: 'json' };
import ja from './locales/ja.json' with { type: 'json' };
import zh from './locales/zh.json' with { type: 'json' };
import pt from './locales/pt.json' with { type: 'json' };
import ko from './locales/ko.json' with { type: 'json' };
import it from './locales/it.json' with { type: 'json' };
import ar from './locales/ar.json' with { type: 'json' };

function detectLanguage(): string {
  // Check --lang CLI flag
  const langFlagIndex = process.argv.indexOf('--lang');
  if (langFlagIndex !== -1 && process.argv[langFlagIndex + 1]) {
    return process.argv[langFlagIndex + 1]!;
  }

  // Fall back to LANG environment variable (e.g., "fr_FR.UTF-8" -> "fr")
  const envLang = process.env['LANG'];
  if (envLang) {
    const code = envLang.split('.')[0]?.split('_')[0];
    if (code) return code;
  }

  return 'en';
}

i18next.init({
  lng: detectLanguage(),
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
  resources: {
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
  },
});

export function t(key: string, options?: Record<string, unknown>): string {
  return i18next.t(key, options) as string;
}

export function addLanguage(code: string, translations: Record<string, unknown>): void {
  i18next.addResourceBundle(code, 'translation', translations, true, true);
}

export { i18next };
