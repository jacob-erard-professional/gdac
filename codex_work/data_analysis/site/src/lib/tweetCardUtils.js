export function normalizeTextKey(text) {
  return String(text || "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

export function dedupeTweetEntries(entries) {
  const out = [];
  const seen = new Set();
  for (const item of entries || []) {
    const key = item.normalized_text_key || normalizeTextKey(item.text);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push({ ...item, normalized_text_key: key });
  }
  return out;
}
