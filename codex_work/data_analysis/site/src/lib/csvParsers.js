export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const nx = text[i + 1];
    if (ch === '"') {
      if (inQuotes && nx === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      row.push(field);
      field = "";
    } else if ((ch === "\n" || ch === "\r") && !inQuotes) {
      if (ch === "\r" && nx === "\n") i += 1;
      row.push(field);
      if (row.some((x) => x.length > 0)) rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    if (row.some((x) => x.length > 0)) rows.push(row);
  }
  if (!rows.length) return [];
  const headers = rows[0].map((x) => String(x || "").trim());
  return rows.slice(1).map((r) => {
    const out = {};
    headers.forEach((h, idx) => {
      out[h] = String(r[idx] || "").trim();
    });
    return out;
  });
}
