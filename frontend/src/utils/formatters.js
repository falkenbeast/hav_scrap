/**
 * Formatting utilities for HAV_SCRAP frontend telemetry display.
 * Explicitly converts UTC timestamps to Asia/Kolkata (IST, UTC+05:30).
 */

export const IST_TIMEZONE = 'Asia/Kolkata';

/**
 * Safely parses any date string (ISO with Z, ISO with +00:00, naive SQLite datetime, or epoch)
 * as a UTC Date instance to prevent local timezone misinterpretation.
 */
export const parseUTC = (dateInput) => {
  if (!dateInput) return null;
  if (dateInput instanceof Date) {
    return isNaN(dateInput.getTime()) ? null : dateInput;
  }
  let s = String(dateInput).trim();
  if (!s || s === '—' || s === '-' || s.toLowerCase() === 'null') return null;

  // If timestamp has no timezone offset (no 'Z' and no '+/-HH:MM'), treat it as UTC
  if (!s.endsWith('Z') && !/[+-]\d{2}(:?\d{2})?$/.test(s)) {
    s = s.replace(' ', 'T') + 'Z';
  }

  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
};

/**
 * Formats a UTC timestamp into standard IST datetime:
 * "YYYY-MM-DD HH:mm:ss IST"
 * Example: "2026-11-05T14:00:00Z" -> "2026-11-05 19:30:00 IST"
 */
export const formatDateTimeIST = (dateInput, { fallback = '—', showSuffix = true } = {}) => {
  const d = parseUTC(dateInput);
  if (!d) return fallback;

  try {
    const formatter = new Intl.DateTimeFormat('en-IN', {
      timeZone: IST_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });

    const parts = formatter.formatToParts(d);
    const m = {};
    for (const p of parts) m[p.type] = p.value;
    const base = `${m.year}-${m.month}-${m.day} ${m.hour}:${m.minute}:${m.second}`;
    return showSuffix ? `${base} IST` : base;
  } catch (err) {
    return fallback;
  }
};

/**
 * Formats a UTC date string into IST calendar date:
 * Example: "2026-11-05T14:00:00Z" -> "Nov 5, 2026"
 */
export const formatDateIST = (dateInput, { fallback = 'Pending' } = {}) => {
  const d = parseUTC(dateInput);
  if (!d) return fallback;

  try {
    return d.toLocaleDateString('en-US', {
      timeZone: IST_TIMEZONE,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return fallback;
  }
};

/**
 * Formats a UTC date string into IST 24-hour time:
 * Example: "2026-11-05T14:00:00Z" -> "19:30:00"
 */
export const formatTimeIST = (dateInput, { fallback = '--:--:--' } = {}) => {
  const d = parseUTC(dateInput);
  if (!d) return fallback;

  try {
    return d.toLocaleTimeString('en-US', {
      timeZone: IST_TIMEZONE,
      hour12: false,
    });
  } catch {
    return fallback;
  }
};

/**
 * Formats activity feed timestamps.
 * If already a relative label (e.g. "10 mins ago", "Recent"), preserves it.
 * Otherwise, formats as IST datetime: "2026-11-05 19:30:33 IST".
 */
export const formatActivityTimestampIST = (timestampStr) => {
  if (!timestampStr) return 'Recent';
  if (
    timestampStr.includes('ago') ||
    timestampStr.toLowerCase() === 'recent' ||
    timestampStr.toLowerCase() === 'just now'
  ) {
    return timestampStr;
  }
  const d = parseUTC(timestampStr);
  if (!d) return timestampStr;
  return formatDateTimeIST(d);
};

export const formatCurrencyLPA = (amount) => {
  if (amount === null || amount === undefined) return 'N/A';
  return `${Number(amount).toFixed(2)} LPA`;
};

// Aliases for seamless backward compatibility
export const formatDate = formatDateIST;
export const formatTime = formatTimeIST;

