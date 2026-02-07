export async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path} (${response.status})`);
  }
  return response.json();
}

export async function loadCsv(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path} (${response.status})`);
  }
  const text = await response.text();
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const headers = lines[0].split(",").map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const values = line.split(",");
    const row = {};
    headers.forEach((h, idx) => {
      row[h] = values[idx];
    });
    return row;
  });
}

export async function loadJsonl(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path} (${response.status})`);
  }
  const text = await response.text();
  const lines = text.split(/\r?\n/).filter(Boolean);
  const records = [];
  for (const line of lines) {
    try {
      const payload = JSON.parse(line);
      const batch = payload.records || [];
      records.push(...batch);
    } catch (err) {
      continue;
    }
  }
  return records;
}

export function buildPath(root, year, file) {
  return `${root}/${year}/${file}`;
}
