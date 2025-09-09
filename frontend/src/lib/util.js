// --- Client-side utilities ---
// Note: Keep existing helpers and add a small, opt-in logging facility.

export function getLocaleDateFormat() {
  // Get the locale's date format parts
  const formatter = new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });

  const parts = formatter.formatToParts(new Date(2023, 0, 15));

  // Build format string based on the order of parts
  let format = '';
  for (const part of parts) {
    switch (part.type) {
      case 'year':
        format += 'yy';
        break;
      case 'month':
        format += 'mm';
        break;
      case 'day':
        format += 'dd';
        break;
      case 'literal':
        format += part.value;
        break;
    }
  }

  return format;
}

// --- Client console logging facility ---
// Goals:
// - Easy to turn on/off globally via:
//   a) localStorage key: "looma:clientLogEnabled" => "1"/"0" or "true"/"false"
//   b) window.__CLIENT_LOG__ boolean (read once on load)
//   c) Vite env var VITE_CLIENT_LOG ("true"/"1")
//   d) Runtime helpers: enableClientLog()/disableClientLog()/setClientLogEnabled()
// - Minimal overhead: all methods are no-ops when disabled.
// - Namespaced loggers with timestamps.

const CLIENT_LOG_KEY = 'looma:clientLogEnabled';

let _clientLogEnabled = (() => {
  try {
    const v = localStorage.getItem(CLIENT_LOG_KEY);
    if (v === '1' || v === 'true') return true;
    if (v === '0' || v === 'false') return false;
  } catch (_) {
    // ignore storage errors (e.g., privacy mode)
  }
  if (typeof window !== 'undefined' && typeof window.__CLIENT_LOG__ === 'boolean') {
    return window.__CLIENT_LOG__;
  }
  try {
    // Vite env (available at build time)
    const env = (import.meta && import.meta.env && import.meta.env.VITE_CLIENT_LOG) || undefined;
    if (env === '1' || env === 'true') return true;
  } catch (_) {
    // ignore if import.meta is not available
  }
  return false;
})();

export function isClientLogEnabled() {
  return !!_clientLogEnabled;
}

export function setClientLogEnabled(enabled) {
  _clientLogEnabled = !!enabled;
  try {
    localStorage.setItem(CLIENT_LOG_KEY, _clientLogEnabled ? '1' : '0');
  } catch (_) {
    // non-fatal
  }
}

export const enableClientLog = () => setClientLogEnabled(true);
export const disableClientLog = () => setClientLogEnabled(false);

function _ts() {
  try {
    // Show time-of-day with milliseconds
    const d = new Date();
    return d.toISOString().split('T')[1].replace('Z', '');
  } catch (_) {
    return '';
  }
}

function _ns(namespace) {
  return namespace ? `[${namespace}]` : '';
}

export function createClientLogger(namespace = '') {
  const nsPrefix = _ns(namespace);
  const wrap = (fn) => (...args) => {
    if (!_clientLogEnabled) return;
    try {
      fn(`[${_ts()}]`, nsPrefix, ...args);
    } catch (_) {
      // swallow logging errors
    }
  };
  return {
    log: wrap(console.log.bind(console)),
    info: wrap((console.info || console.log).bind(console)),
    debug: wrap((console.debug || console.log).bind(console)),
    warn: wrap((console.warn || console.log).bind(console)),
    error: wrap((console.error || console.log).bind(console)),
    group: (...args) => {
      if (!_clientLogEnabled) return;
      (console.group || console.log).call(console, `[${_ts()}]`, nsPrefix, ...args);
    },
    groupEnd: () => {
      if (!_clientLogEnabled) return;
      (console.groupEnd || (() => {})).call(console);
    },
  };
}

// A default app-level logger for convenience
export const clientLog = createClientLogger('app');

// Optional: expose quick toggles for use in the browser console without imports
if (typeof window !== 'undefined') {
  try {
    window.loomaLogEnable = enableClientLog;
    window.loomaLogDisable = disableClientLog;
    window.loomaIsLogEnabled = isClientLogEnabled;
  } catch (_) {
    // ignore if window is not writable
  }
}