import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import { defineConfig } from "vite";

const YEAR_RE = /^\d{4}$/;

function sendJson(res, code, payload) {
  res.statusCode = code;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(payload));
}

function normalizeText(text) {
  return String(text || "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];
    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(field);
      if (row.some((x) => x.length > 0)) rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    if (row.some((x) => x.length > 0)) rows.push(row);
  }
  if (!rows.length) return [];
  const headers = rows[0].map((h) => String(h || "").trim());
  return rows.slice(1).map((r) => {
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = (r[idx] ?? "").trim();
    });
    return obj;
  });
}

function addTerm(map, term, count = 1) {
  const key = String(term || "").trim();
  if (!key) return;
  const numeric = Number(count);
  const add = Number.isFinite(numeric) && numeric > 0 ? numeric : 1;
  map.set(key, (map.get(key) || 0) + add);
}

function mapToWordCloud(map, scope, cloudType, year) {
  return Array.from(map.entries())
    .map(([term, count]) => ({ term, count, scope, cloud_type: cloudType, year }))
    .sort((a, b) => b.count - a.count || a.term.localeCompare(b.term));
}

async function readIfExists(p) {
  try {
    return await fsp.readFile(p, "utf-8");
  } catch {
    return null;
  }
}

async function pickRawCsv(dirPath, { scope, purpose } = {}) {
  try {
    const entries = await fsp.readdir(dirPath);
    const csvs = entries
      .filter((x) => x.toLowerCase().endsWith(".csv"))
      .sort((a, b) => a.localeCompare(b));
    if (!csvs.length) return null;

    const has = (name) => csvs.find((x) => x.toLowerCase() === name.toLowerCase());

    // Prefer explicit source files so full-scope reads are stable and correct.
    if (purpose === "raw_brand") {
      const preferred = has("tweets.csv") || (scope === "full" ? has("final.csv") : null);
      if (preferred) return path.join(dirPath, preferred);
    }
    if (purpose === "tweets") {
      const preferred = (scope === "full" ? has("final.csv") : null) || has("tweets.csv");
      if (preferred) return path.join(dirPath, preferred);
    }

    return path.join(dirPath, csvs[0]);
  } catch {
    return null;
  }
}

function parseHashtags(payload, map) {
  if (!payload || typeof payload !== "object") return;
  const arr = payload.hashtags || payload.items || [];
  for (const item of arr) {
    addTerm(map, item.hashtag || item.tag || item.term, item.count || item.total_count || 1);
  }
}

function parseParents(payload, map) {
  if (!payload || typeof payload !== "object") return;
  const parents = payload.parent_companies || payload.parents || [];
  for (const item of parents) {
    addTerm(
      map,
      item.parent_company || item.parent || item.company,
      item.total_count || item.count || (Array.isArray(item.brands) ? item.brands.length : 1)
    );
  }
}

function parseCelebrity(csvText, map) {
  const rows = parseCsv(csvText || "");
  if (!rows.length) return;
  for (const row of rows) {
    const keys = Object.keys(row);
    const termKey = keys.find((k) => /celebrity|name|term/i.test(k)) || keys[0];
    const countKey = keys.find((k) => /count|freq|frequency|total/i.test(k)) || keys[1];
    addTerm(map, row[termKey], row[countKey]);
  }
}

function parseRawBrand(csvText, map) {
  const rows = parseCsv(csvText || "");
  for (const row of rows) {
    const key = Object.keys(row).find((k) => k.toLowerCase() === "brand") || "brand";
    const raw = String(row[key] || "").trim();
    if (!raw) continue;
    const normalized = raw
      .replace(/_\d+$/, "")
      .replace(/\s+/g, " ")
      .trim();
    if (!normalized || /^(null|none|nan|n\/a)$/i.test(normalized)) continue;
    addTerm(map, normalized, 1);
  }
}

function parseTweets(csvText, scope, year) {
  const rows = parseCsv(csvText || "");
  const out = [];
  const seen = new Set();
  for (const row of rows) {
    const textKey = Object.keys(row).find((k) => k.toLowerCase() === "text") || "text";
    const idKey = Object.keys(row).find((k) => /tweet_id|id/i.test(k)) || "id";
    const aboutKey = Object.keys(row).find((k) => k.toLowerCase() === "is_about_brand");
    const text = row[textKey] || "";
    const norm = normalizeText(text);
    if (!norm) continue;

    let include = true;
    if (scope === "full") {
      const raw = aboutKey ? String(row[aboutKey]).toLowerCase() : "false";
      include = !(raw === "true" || raw === "1" || raw === "yes");
    }
    if (!include) continue;
    if (seen.has(norm)) continue;
    seen.add(norm);
    out.push({
      tweet_id: String(row[idKey] || "").trim(),
      text: String(text).trim(),
      normalized_text_key: norm,
      scope,
      year,
      ...(aboutKey ? { is_about_brand: String(row[aboutKey]).toLowerCase() === "true" } : {}),
    });
  }
  return out;
}

function comparisonApiPlugin() {
  const repoRoot = path.resolve(__dirname, "..");
  const analyticsRoot = path.join(repoRoot, "outputs", "analytics");
  const rawRoot = path.join(repoRoot, "data", "raw");

  return {
    name: "comparison-api",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!req.url || !req.url.startsWith("/api/")) return next();

        try {
          if (req.url === "/api/years") {
            let years = [];
            try {
              const entries = await fsp.readdir(analyticsRoot, { withFileTypes: true });
              const regularYears = entries
                .filter((d) => d.isDirectory() && YEAR_RE.test(d.name))
                .map((d) => d.name);
              years = regularYears
                .filter((y) => fs.existsSync(path.join(analyticsRoot, `${y}_full`)))
                .sort();
            } catch {
              years = [];
            }
            return sendJson(res, 200, {
              years: years.map((year) => ({
                year,
                regular_path: `outputs/analytics/${year}`,
                full_path: `outputs/analytics/${year}_full`,
              })),
            });
          }

          const comparisonMatch = req.url.match(/^\/api\/comparison\/(\d{4})(?:\?.*)?$/);
          if (comparisonMatch) {
            const year = comparisonMatch[1];
            const regularDir = path.join(analyticsRoot, year);
            const fullDir = path.join(analyticsRoot, `${year}_full`);
            if (!fs.existsSync(regularDir) || !fs.existsSync(fullDir)) {
              return sendJson(res, 404, { error: "Year unavailable for dual-scope comparison" });
            }

            const fullTagPath = path.join(fullDir, "hashtags_frequency.json");
            const fullTagAltPath = path.join(fullDir, "hashtag_frequency.json");
            const fullParentPath = path.join(fullDir, "parent_company_groups.json");
            const regCelebrityPath = path.join(regularDir, "celebrity_freq.csv");
            const fullCelebrityPath = path.join(fullDir, "celebrity_freq.csv");

            const regRawCsvPath = await pickRawCsv(path.join(rawRoot, year), {
              scope: "regular",
              purpose: "raw_brand",
            });
            const fullRawCsvPath = await pickRawCsv(path.join(rawRoot, `${year}_full`), {
              scope: "full",
              purpose: "raw_brand",
            });

            const fullTagRaw = (await readIfExists(fullTagPath)) || (await readIfExists(fullTagAltPath));
            const fullParentRaw = await readIfExists(fullParentPath);
            const regCelebrityRaw = await readIfExists(regCelebrityPath);
            const fullCelebrityRaw = await readIfExists(fullCelebrityPath);
            const regRawCsv = regRawCsvPath ? await readIfExists(regRawCsvPath) : null;
            const fullRawCsv = fullRawCsvPath ? await readIfExists(fullRawCsvPath) : null;

            const fullCloud = new Map();
            parseHashtags(fullTagRaw ? JSON.parse(fullTagRaw) : null, fullCloud);
            parseParents(fullParentRaw ? JSON.parse(fullParentRaw) : null, fullCloud);

            const regCeleb = new Map();
            parseCelebrity(regCelebrityRaw || "", regCeleb);
            const fullCeleb = new Map();
            parseCelebrity(fullCelebrityRaw || "", fullCeleb);

            const regBrand = new Map();
            parseRawBrand(regRawCsv || "", regBrand);
            const fullBrand = new Map();
            parseRawBrand(fullRawCsv || "", fullBrand);

            const payload = {
              year,
              word_clouds: {
                full_hashtag_parent: mapToWordCloud(fullCloud, "full", "full_hashtag_parent", year),
                regular_celebrity: mapToWordCloud(regCeleb, "regular", "celebrity", year),
                full_celebrity: mapToWordCloud(fullCeleb, "full", "celebrity", year),
                regular_raw_brand: mapToWordCloud(regBrand, "regular", "raw_brand", year),
                full_raw_brand: mapToWordCloud(fullBrand, "full", "raw_brand", year),
              },
              statuses: {
                full_hashtag_parent: fullCloud.size ? "loaded" : "missing",
                regular_celebrity: regCeleb.size ? "loaded" : "missing",
                full_celebrity: fullCeleb.size ? "loaded" : "missing",
                regular_raw_brand: regBrand.size ? "loaded" : "missing",
                full_raw_brand: fullBrand.size ? "loaded" : "missing",
              },
            };
            return sendJson(res, 200, payload);
          }

          const tweetsMatch = req.url.match(/^\/api\/comparison\/(\d{4})\/tweets\?scope=(regular|full)$/);
          if (tweetsMatch) {
            const year = tweetsMatch[1];
            const scope = tweetsMatch[2];
            const sourceDir = scope === "regular" ? path.join(rawRoot, year) : path.join(rawRoot, `${year}_full`);
            const sourceCsvPath = await pickRawCsv(sourceDir, { scope, purpose: "tweets" });
            const csvText = sourceCsvPath ? await readIfExists(sourceCsvPath) : "";
            const entries = parseTweets(csvText || "", scope, year);
            return sendJson(res, 200, {
              scope,
              entries,
              total_count: entries.length,
            });
          }

          return sendJson(res, 404, { error: "Unknown API route" });
        } catch (err) {
          return sendJson(res, 500, { error: String(err?.message || err) });
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [comparisonApiPlugin()],
});
