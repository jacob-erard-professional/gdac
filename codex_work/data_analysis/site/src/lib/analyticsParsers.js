function addCount(map, term, count) {
  const key = String(term || "").trim();
  if (!key) return;
  const n = Number(count);
  map.set(key, (map.get(key) || 0) + (Number.isFinite(n) && n > 0 ? n : 1));
}

export function fullHashtagParentTerms(payload) {
  const map = new Map();
  const fullTerms = payload?.word_clouds?.full_hashtag_parent || [];
  for (const row of fullTerms) addCount(map, row.term, row.count);
  return Array.from(map.entries()).map(([term, count]) => ({ term, count }));
}

export function cloudTerms(payload, key) {
  return (payload?.word_clouds?.[key] || []).map((x) => ({ term: x.term, count: x.count }));
}
