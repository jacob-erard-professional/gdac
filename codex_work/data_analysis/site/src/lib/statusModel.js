export const STATUS = {
  LOADED: "loaded",
  PARTIAL: "partial",
  MISSING: "missing",
};

export function normalizeStatus(status) {
  if (status === STATUS.LOADED || status === STATUS.PARTIAL || status === STATUS.MISSING) {
    return status;
  }
  return STATUS.MISSING;
}
