import { listYears } from "./comparisonApiClient";

export async function discoverComparableYears() {
  const payload = await listYears();
  return (payload.years || []).map((y) => String(y.year));
}
