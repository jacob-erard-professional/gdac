import React, { useEffect, useMemo, useRef, useState } from "react";
import EmptyState from "./EmptyState";

function sizeForRank(index) {
  if (index < 3) return 34;
  if (index < 8) return 26;
  if (index < 16) return 20;
  return 15;
}

function sizeForFrequency(count, minCount, maxCount) {
  const minSize = 14;
  const maxSize = 42;
  if (maxCount <= minCount) return 24;
  const t = (count - minCount) / (maxCount - minCount);
  return Math.round(minSize + (maxSize - minSize) * t);
}

function hashString(input) {
  let h = 2166136261;
  const s = String(input || "");
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function getMeasureContext() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  return canvas.getContext("2d");
}

function overlaps(a, b, padding = 3) {
  return !(
    a.right + padding < b.left ||
    a.left > b.right + padding ||
    a.bottom + padding < b.top ||
    a.top > b.bottom + padding
  );
}

function measureWord(ctx, term, fontSize) {
  if (!ctx) {
    return { width: term.length * fontSize * 0.55, height: Math.round(fontSize * 1.2) };
  }
  ctx.font = `700 ${fontSize}px "IBM Plex Sans", "Segoe UI", sans-serif`;
  return {
    width: Math.ceil(ctx.measureText(term).width),
    height: Math.round(fontSize * 1.2),
  };
}

function layoutMiddleWords(terms, minCount, maxCount, width, height) {
  if (!width || !height) return [];
  const cx = width / 2;
  const cy = height / 2;
  const ctx = getMeasureContext();
  const placed = [];

  const ordered = [...terms].sort((a, b) => {
    const countDiff = (Number(b.count) || 0) - (Number(a.count) || 0);
    if (countDiff !== 0) return countDiff;
    return a.term.localeCompare(b.term);
  });

  for (const item of ordered) {
    const term = String(item.term || "").trim();
    if (!term) continue;

    let fontSize = sizeForFrequency(Number(item.count) || 0, minCount, maxCount);
    const seed = hashString(term);
    const angleBase = ((seed % 360) * Math.PI) / 180;
    let added = false;

    for (let shrink = 0; shrink < 4 && !added; shrink += 1) {
      const trySize = Math.max(11, fontSize - shrink * 2);
      const box = measureWord(ctx, term, trySize);
      const halfW = box.width / 2;
      const halfH = box.height / 2;

      for (let i = 0; i < 1800; i += 1) {
        const radius = 1 + i * 1.05;
        const angle = angleBase + i * 0.36;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);

        const candidate = {
          left: x - halfW,
          right: x + halfW,
          top: y - halfH,
          bottom: y + halfH,
        };

        const inside =
          candidate.left >= 4 &&
          candidate.right <= width - 4 &&
          candidate.top >= 4 &&
          candidate.bottom <= height - 4;
        if (!inside) continue;

        if (placed.some((p) => overlaps(candidate, p, 2))) continue;

        placed.push({
          ...candidate,
          term,
          count: item.count,
          fontSize: trySize,
          x,
          y,
        });
        added = true;
        break;
      }
    }
  }

  return placed;
}

function superbowlSpots(total) {
  if (typeof document === "undefined") return [];
  const canvas = document.createElement("canvas");
  canvas.width = 1400;
  canvas.height = 360;
  const ctx = canvas.getContext("2d");
  if (!ctx) return [];

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#000";
  ctx.font = "900 220px Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("SUPERBOWL", canvas.width / 2, canvas.height / 2);

  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const spots = [];
  for (let y = 12; y < canvas.height - 12; y += 10) {
    for (let x = 12; x < canvas.width - 12; x += 10) {
      const alpha = data[(y * canvas.width + x) * 4 + 3];
      if (alpha > 20) {
        spots.push({
          left: `${(x / canvas.width) * 100}%`,
          top: `${(y / canvas.height) * 100}%`,
        });
      }
    }
  }

  if (!spots.length) return [];

  const out = [];
  const step = Math.max(1, Math.floor(spots.length / total));
  let idx = 0;
  while (out.length < total && idx < spots.length) {
    out.push(spots[idx]);
    idx += step;
  }
  while (out.length < total) out.push(spots[out.length % spots.length]);
  return out;
}

export default function WordCloudPanel({ title, terms, status, shape = "default" }) {
  if (!terms.length) {
    return <EmptyState title={title} detail={`Data status: ${status}`} />;
  }

  const isMiddle = shape === "middle";
  const isSuperbowl = shape === "superbowl";
  const cloudRef = useRef(null);
  const [cloudSize, setCloudSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!isMiddle || !cloudRef.current || typeof ResizeObserver === "undefined") return undefined;
    const el = cloudRef.current;
    const update = () => {
      const rect = el.getBoundingClientRect();
      setCloudSize({
        width: Math.max(0, Math.floor(rect.width)),
        height: Math.max(0, Math.floor(rect.height)),
      });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [isMiddle]);

  const shown = (
    isMiddle ? [...terms] : [...terms].sort((a, b) => b.count - a.count)
  ).slice(0, isMiddle ? 120 : 40);
  const counts = shown.map((x) => Number(x.count) || 0);
  const minCount = counts.length ? Math.min(...counts) : 0;
  const maxCount = counts.length ? Math.max(...counts) : 0;
  const middleLayout = useMemo(() => {
    if (!isMiddle) return [];
    return layoutMiddleWords(shown, minCount, maxCount, cloudSize.width, cloudSize.height);
  }, [isMiddle, shown, minCount, maxCount, cloudSize.width, cloudSize.height]);
  const spots = isSuperbowl ? superbowlSpots(shown.length) : [];
  return (
    <section className="panel">
      <div className="panel-head">
        <h3>{title}</h3>
        <span className={`badge badge-${status}`}>{status}</span>
      </div>
      <div
        ref={cloudRef}
        className={`word-cloud ${isSuperbowl ? "word-cloud-superbowl" : ""} ${isMiddle ? "word-cloud-middle" : ""}`}
      >
        {(isMiddle ? middleLayout : shown).map((item, idx) => (
          <span
            key={`${item.term}-${idx}`}
            className={isSuperbowl || isMiddle ? "shape-word" : ""}
            style={{
              fontSize: `${isMiddle ? item.fontSize : sizeForRank(idx)}px`,
              ...(isMiddle ? { left: `${item.x}px`, top: `${item.y}px` } : {}),
              ...(isSuperbowl ? spots[idx] : {}),
            }}
            title={`count=${item.count}`}
          >
            {item.term}
          </span>
        ))}
      </div>
    </section>
  );
}
