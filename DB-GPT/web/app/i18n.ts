import en from '@/locales/en';
import zh from '@/locales/zh';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { localizeUiText } from '@/lib/ui-zh';

export type I18nKeys = keyof typeof en;
interface Resources {
  translation: Record<I18nKeys, string>;
}

i18n.use({
  type: 'postProcessor',
  name: 'chinese-ui',
  process(value: string, _key: unknown, _options: unknown, translator: { language?: string }) {
    return translator.language?.startsWith('zh') ? localizeUiText(value) : value;
  },
}).use(initReactI18next).init({
  resources: {
    en: {
      translation: en,
    },
    zh: {
      translation: zh,
    },
  },
  lng: 'zh',
  fallbackLng: 'zh',
  postProcess: ['chinese-ui'],
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;

declare module 'i18next' {
  interface CustomTypeOptions {
    resources: Resources;
  }
}
