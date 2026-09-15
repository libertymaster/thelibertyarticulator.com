export type Validator = (value: unknown) => boolean;

export function parsePayload<T>(raw: unknown, validate: Validator): T {
  if (!validate(raw)) throw new Error('Research data did not match the expected schema.');
  return raw as T;
}
export function safeHref(value: string): string | undefined {
  if (value.startsWith('#')) return value;
  if (value.startsWith('/') && !value.startsWith('//') && !value.includes('\\')) return value;
  try {
    const url = new URL(value);
    if (url.protocol === 'http:' || url.protocol === 'https:') return url.href;
  } catch { /* Invalid URLs are not rendered as links. */ }
  return undefined;
}
export function yearLabel(year: number): string {
  return year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
}
export function rangeError(from: string, to: string): string {
  const parse = (s: string) => s === '' ? null : Number(s);
  const a = parse(from), b = parse(to);
  if ([a, b].some(v => v !== null && (!Number.isInteger(v) || v === 0 || Math.abs(v) > 10000))) {
    return 'Use whole years from -10000 to -1 (BCE) or 1 to 10000 (CE); there is no year zero.';
  }
  return a !== null && b !== null && a > b ? 'The start year must not follow the end year.' : '';
}
