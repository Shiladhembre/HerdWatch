export function readStore(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } }
export function writeStore(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { throw new Error('Local storage is full or unavailable. Please free space and try again.'); } }
export function downloadCSV(rows, filename) {
  if (!rows.length) return;
  const keys = Object.keys(rows[0]).filter(k => !rows.some(r => typeof r[k] === 'object'));
  const cell = v => {let value = String(v ?? ''); if (/^[=+@\-\t\r]/.test(value)) value = "'" + value; return '"' + value.replaceAll('"','""') + '"';};
  const blob = new Blob(['\uFEFF'+[keys, ...rows.map(r => keys.map(k => r[k]))].map(row => row.map(cell).join(',')).join('\r\n')], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
