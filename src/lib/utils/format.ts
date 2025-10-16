export function toUTCISOString(d: Date | string): string {
  const date = typeof d === 'string' ? new Date(d) : d;
  return new Date(date.getTime() - date.getTimezoneOffset()*60000).toISOString();
}
