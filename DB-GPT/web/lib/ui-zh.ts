import translations from './ui-translations.zh.json';

const copy = translations as Record<string, string>;

/** Translate display copy without changing model IDs, routes, SQL or form values. */
export function localizeUiText(value: string | null | undefined): string {
  if (!value) return value ?? '';
  const normalized = value.replace(/\s+/g, ' ').trim();
  return copy[normalized] ?? value;
}

const DISPLAY_FIELDS = new Set([
  'label', 'title', 'description', 'desc', 'help', 'remark', 'app_describe',
  'scene_describe', 'description_en', 'remark_en', 'name_cn', 'display_name',
  'err_msg', 'message',
]);

/** Localize known, shipped metadata for rendering; preserve every machine value. */
export function localizeUiMetadata<T>(value: T): T {
  function visit(input: unknown, field = ''): unknown {
    if (typeof input === 'string') return DISPLAY_FIELDS.has(field) ? localizeUiText(input) : input;
    if (Array.isArray(input)) return input.map(item => visit(item, field));
    if (input && Object.getPrototypeOf(input) === Object.prototype) {
      return Object.fromEntries(Object.entries(input).map(([key, item]) => [key, visit(item, key)]));
    }
    return input;
  }
  return visit(value) as T;
}
