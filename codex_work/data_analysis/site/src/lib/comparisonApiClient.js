async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(`HTTP ${res.status}: ${msg}`);
  }
  return res.json();
}

function assert(condition, message) {
  if (!condition) throw new Error(`Contract validation failed: ${message}`);
}

function validateYearsPayload(payload) {
  assert(payload && Array.isArray(payload.years), "years payload must include years[]");
}

function validateComparisonPayload(payload) {
  assert(payload && typeof payload === "object", "comparison payload must be an object");
  assert(payload.year, "comparison payload missing year");
  assert(payload.word_clouds && typeof payload.word_clouds === "object", "comparison payload missing word_clouds");
  assert(payload.statuses && typeof payload.statuses === "object", "comparison payload missing statuses");
}

function validateTweetPayload(payload) {
  assert(payload && Array.isArray(payload.entries), "tweet payload must include entries[]");
  assert(typeof payload.total_count === "number", "tweet payload missing total_count");
}

export function listYears() {
  return fetchJson("/api/years").then((payload) => {
    validateYearsPayload(payload);
    return payload;
  });
}

export function getComparisonPayload(year) {
  return fetchJson(`/api/comparison/${year}`).then((payload) => {
    validateComparisonPayload(payload);
    return payload;
  });
}

export function getTweetCardEntries(year, scope) {
  return fetchJson(`/api/comparison/${year}/tweets?scope=${scope}`).then((payload) => {
    validateTweetPayload(payload);
    return payload;
  });
}
