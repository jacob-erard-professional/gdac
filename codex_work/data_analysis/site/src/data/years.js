import { loadJson } from "./loaders";

export async function loadYearIndex() {
  try {
    const payload = await loadJson("/outputs/analytics/index.json");
    if (Array.isArray(payload?.years)) {
      return payload.years.map(String);
    }
    return [];
  } catch {
    return [];
  }
}
