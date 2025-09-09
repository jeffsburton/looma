# Client-side Logging (util.js)

This project includes a small, opt-in console logging facility you can use anywhere in the frontend.
It’s off by default and becomes a no-op when disabled, so it’s safe to leave calls in production.

Location: `frontend/src/lib/util.js`

Exports:
- `createClientLogger(namespace?: string)` → namespaced logger with methods: `log`, `info`, `debug`, `warn`, `error`, `group`, `groupEnd`.
- `clientLog` → a default logger with namespace `app`.
- `enableClientLog()` / `disableClientLog()` / `setClientLogEnabled(boolean)` / `isClientLogEnabled()`.

All logs are prefixed with a timestamp and optional `[namespace]` when enabled. When disabled, calls are no-ops.

---

## How to enable or disable logging

Choose any of the following:

1) From the browser Console (quickest):
- `loomaLogEnable()` → enable
- `loomaLogDisable()` → disable
- `loomaIsLogEnabled()` → check status

These helpers are exposed on `window` for convenience.

2) Persist between reloads via localStorage:
- Enable: `localStorage.setItem('looma:clientLogEnabled', '1')`
- Disable: `localStorage.setItem('looma:clientLogEnabled', '0')`

3) Build-time default via Vite env:
- In your `.env` (or `.env.local`): `VITE_CLIENT_LOG=true`
  - This sets the initial default to enabled. You can still toggle at runtime with the helpers above.

4) One-off default via a global flag (read once on page load):
- Before your app bootstraps, set: `window.__CLIENT_LOG__ = true`

Note: Precedence on first load is: localStorage → `window.__CLIENT_LOG__` → `import.meta.env.VITE_CLIENT_LOG` → default `false`.
At runtime, the source doesn’t matter—use `enableClientLog()` / `disableClientLog()` to toggle.

---

## Basic usage in code

Import helpers from the utility module:

```ts
import { createClientLogger, clientLog, enableClientLog, disableClientLog } from '@/lib/util';

// Create a namespaced logger for your module/component
const log = createClientLogger('MessagesTab');

// Use it like console.*
log.info('Mounted');
log.debug('Payload received', payload);
log.warn('Retrying request', { attempt });
log.error('Unexpected error', err);

// Grouping
log.group('Render cycle');
log.debug('props', props);
log.debug('state', state);
log.groupEnd();

// Optional: toggle at runtime (e.g., in a debug UI)
enableClientLog();
// ... later
disableClientLog();
```

You can also use the default `clientLog` for quick app-wide messages:

```ts
import { clientLog } from '@/lib/util';
clientLog.info('App started');
```

---

## Example in a Vue component

```vue
<script setup>
import { onMounted } from 'vue';
import { createClientLogger } from '@/lib/util';

const log = createClientLogger('TeamsView');

onMounted(() => {
  log.info('TeamsView mounted');
});
</script>
```

---

## Checking and controlling status programmatically

```ts
import { isClientLogEnabled, setClientLogEnabled } from '@/lib/util';

if (!isClientLogEnabled()) {
  setClientLogEnabled(true);
}
```

---

## Behavior and performance notes
- When disabled, all logging methods are fast no-ops (they don’t call `console.*`).
- When enabled, messages are prefixed with `[HH:MM:SS.mmm]` and `[Namespace]`.
- Works in all modern browsers that support `console`.

---

## Troubleshooting
- “I still don’t see logs”: Make sure you’ve enabled logging (see methods above) and that your browser’s devtools is open.
- “I want logs only for one page load”: Use `loomaLogEnable()` in the console without writing to localStorage. On refresh, it will revert unless localStorage is set.
- “I want it always on locally”: Add `VITE_CLIENT_LOG=true` to your local `.env` or set localStorage once.

---

## API reference (quick)
- `createClientLogger(namespace?: string)` → `{ log, info, debug, warn, error, group, groupEnd }`
- `clientLog` → default logger (`namespace = 'app'`)
- `enableClientLog()` / `disableClientLog()`
- `setClientLogEnabled(enabled: boolean)`
- `isClientLogEnabled(): boolean`
