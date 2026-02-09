import React, { useEffect, useMemo, useState } from "react";
import ChartCard from "./components/ChartCard.jsx";
import EmptyState from "./components/EmptyState.jsx";
import MetricRow from "./components/MetricRow.jsx";
import YearSelector from "./components/YearSelector.jsx";
import { buildPath, loadJson, loadJsonl } from "./data/loaders.js";
import { loadYearIndex } from "./data/years.js";

const ANALYTICS_ROOT = "/outputs/analytics";
const AUX_ROOT = "/outputs/aux";
const SENTIMENT_ROOT = "/sentiment/deep";

function makeBarOption(title, labels, values) {
  const visibleCount = Math.min(20, labels.length);
  const hasScroll = labels.length > visibleCount;
  const endPercent = hasScroll ? (visibleCount / labels.length) * 100 : 100;
  return {
    title: { text: title, left: "center", textStyle: { color: "#2a2a2a" } },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { rotate: 30, interval: 0 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: { type: "value" },
    series: [
      {
        data: values,
        type: "bar",
        barWidth: 24,
        barGap: "50%",
        itemStyle: { color: "#0f6b5d" },
      },
    ],
    grid: { left: "6%", right: "3%", bottom: "24%", top: "16%" },
    dataZoom: hasScroll
      ? [
          {
            type: "inside",
            start: 0,
            end: endPercent,
            zoomLock: true,
            moveOnMouseWheel: true,
            moveOnMouseMove: true,
            preventDefaultMouseMove: true,
          },
        ]
      : [],
  };
}

function makeStackedPercentOption(title, labels, seriesDefs) {
  const visibleCount = Math.min(20, labels.length);
  const hasScroll = labels.length > visibleCount;
  const endPercent = hasScroll ? (visibleCount / labels.length) * 100 : 100;
  return {
    title: { text: title, left: "center", textStyle: { color: "#2a2a2a" } },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { top: 26, textStyle: { color: "#2a2a2a" } },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { rotate: 30, interval: 0 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: { type: "value", max: 1, axisLabel: { formatter: "{value}" } },
    series: seriesDefs.map((series) => ({
      name: series.name,
      type: "bar",
      stack: "total",
      barWidth: 24,
      barGap: "50%",
      itemStyle: { color: series.color },
      data: series.values,
    })),
    grid: { left: "6%", right: "3%", bottom: "24%", top: "22%" },
    dataZoom: hasScroll
      ? [
          {
            type: "inside",
            start: 0,
            end: endPercent,
            zoomLock: true,
            moveOnMouseWheel: true,
            moveOnMouseMove: true,
            preventDefaultMouseMove: true,
          },
        ]
      : [],
  };
}

function makeLineOption(title, labels, values) {
  return {
    title: { text: title, left: "center", textStyle: { color: "#2a2a2a" } },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: labels },
    yAxis: { type: "value" },
    series: [{ data: values, type: "line", smooth: true, lineStyle: { color: "#a13b2d" } }],
    grid: { left: "8%", right: "6%", bottom: "18%", top: "18%" },
  };
}

function makeWordCloudOption(title, words) {
  return {
    title: { text: title, left: "center", textStyle: { color: "#2a2a2a" } },
    tooltip: { show: true },
    series: [
      {
        type: "wordCloud",
        shape: "circle",
        sizeRange: [12, 64],
        rotationRange: [0, 0],
        gridSize: 14,
        drawOutOfBound: false,
        textStyle: {
          color: () => {
            const colors = ["#0f6b5d", "#b1453f", "#8b8e8a", "#d39b2a", "#4a6ea8", "#7b5aa6"];
            return colors[Math.floor(Math.random() * colors.length)];
          },
        },
        data: words,
      },
    ],
    grid: { left: "6%", right: "6%", bottom: "10%", top: "18%" },
  };
}

function topWords(words, limit = 50) {
  return [...words]
    .sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0))
    .slice(0, limit);
}

function normalizeEmotion(label) {
  return String(label || "").replace(/_rate$/, "").toLowerCase();
}

const EMOTION_COLORS = {
  anger: "#b1453f",
  angry: "#b1453f",
  sadness: "#3b6ea8",
  sad: "#3b6ea8",
  joy: "#d39b2a",
  happiness: "#d39b2a",
  excitement: "#0f6b5d",
  fear: "#7b5aa6",
  surprise: "#d66b3a",
  disgust: "#4f8a5b",
  neutral: "#8b8e8a",
  disappointment: "#7a5a3a",
  pride: "#2f7f7f",
  love: "#d24f7a",
};

function colorForEmotion(label, fallback) {
  const key = normalizeEmotion(label);
  return EMOTION_COLORS[key] || fallback;
}

function useData(year) {
  const [state, setState] = useState({ status: "idle", data: {}, errors: {} });

  useEffect(() => {
    if (!year) return;
    let mounted = true;
    const load = async () => {
      setState({ status: "loading", data: {}, errors: {} });
      const results = {};
      const errors = {};
      const targets = [
        { key: "hashtags", path: buildPath(ANALYTICS_ROOT, year, "hashtags_frequency.json") },
        { key: "mentions", path: buildPath(ANALYTICS_ROOT, year, "mentions_frequency.json") },
        { key: "parentSummary", path: buildPath(ANALYTICS_ROOT, year, "parent_company_sentiment_summary.json") },
        { key: "parentTimes", path: buildPath(ANALYTICS_ROOT, year, "parent_company_sentiment_timeslices.json") },
        { key: "deepSummary", path: buildPath(ANALYTICS_ROOT, year, "parent_company_deep_sentiment_summary.json") },
        { key: "deepTimes", path: buildPath(ANALYTICS_ROOT, year, "parent_company_deep_sentiment_timeslices.json") },
        { key: "brandGroups", path: buildPath(ANALYTICS_ROOT, year, "brand_groups.json") },
        { key: "parentGroups", path: buildPath(ANALYTICS_ROOT, year, "parent_company_groups.json") },
        { key: "parentBreakdown", path: buildPath(AUX_ROOT, year, "parent_company_emotion_breakdown.json") },
        { key: "brandBreakdown", path: buildPath(AUX_ROOT, year, "brand_emotion_breakdown.json") },
        { key: "deepMap", path: buildPath(AUX_ROOT, year, "deep_sentiment_company_map.jsonl") },
        { key: "deepSentiment", path: buildPath(SENTIMENT_ROOT, year, "deep_sentiment.json") },
      ];

      await Promise.all(
        targets.map(async ({ key, path }) => {
          try {
            if (key === "deepMap") {
              results[key] = await loadJsonl(path);
            } else {
              results[key] = await loadJson(path);
            }
          } catch (error) {
            errors[key] = error.message;
          }
        })
      );

      if (mounted) {
        setState({ status: "ready", data: results, errors });
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [year]);

  return state;
}

export default function App() {
  const [year, setYear] = useState("2024");
  const [yearOptions, setYearOptions] = useState([]);
  const [view, setView] = useState("dashboard");
  const [selectedCompany, setSelectedCompany] = useState("");
  const [companyInput, setCompanyInput] = useState("");
  const [slideIndex, setSlideIndex] = useState(0);
  const [selectedEmotion, setSelectedEmotion] = useState("all");
  const { status, data, errors } = useData(year);

  useEffect(() => {
    loadYearIndex().then(setYearOptions);
  }, []);

  useEffect(() => {
    const parents = data.deepSummary?.parents || [];
    const names = parents.map((p) => p.parent_company).filter((name) => name && name !== "unmatched");
    if (!names.length) return;
    if (!selectedCompany || !names.includes(selectedCompany)) {
      setSelectedCompany(names[0]);
      setCompanyInput(names[0]);
    }
  }, [data.deepSummary, selectedCompany]);

  useEffect(() => {
    setSlideIndex(0);
    setSelectedEmotion("all");
  }, [selectedCompany]);

  const companyOptions = useMemo(() => {
    const parents = data.deepSummary?.parents || [];
    return parents.map((p) => p.parent_company).filter((name) => name && name !== "unmatched");
  }, [data.deepSummary]);

  const hashtagChart = useMemo(() => {
    if (!data.hashtags?.hashtags) return null;
    return makeBarOption(
      "Top Hashtags",
      data.hashtags.hashtags.map((h) => h.hashtag),
      data.hashtags.hashtags.map((h) => h.count)
    );
  }, [data.hashtags]);

  const mentionChart = useMemo(() => {
    if (!data.mentions?.mentions) return null;
    return makeBarOption(
      "Top Mentions",
      data.mentions.mentions.map((m) => m.mention),
      data.mentions.mentions.map((m) => m.count)
    );
  }, [data.mentions]);

  const parentFrequencyChart = useMemo(() => {
    const parents = data.parentGroups?.parent_companies;
    if (!Array.isArray(parents)) return null;
    const rows = parents.filter((p) => (p?.parent_company ?? "unmatched") !== "unmatched");
    if (!rows.length) return null;
    const counts = rows.map((p) => {
      if (typeof p.total_count === "number") return p.total_count;
      const brands = Array.isArray(p.brands) ? p.brands : [];
      return brands.reduce((sum, b) => sum + (Number(b.total_count) || 0), 0);
    });
    return makeBarOption(
      "Parent Company Frequency",
      rows.map((p) => p.parent_company),
      counts
    );
  }, [data.parentGroups]);

  const brandFrequencyChart = useMemo(() => {
    const brands = data.brandGroups?.brands;
    if (!Array.isArray(brands)) return null;
    const rows = brands.filter((b) => (b?.brand ?? "unmatched") !== "unmatched");
    if (!rows.length) return null;
    return makeBarOption(
      "Brand Frequency",
      rows.map((b) => b.brand),
      rows.map((b) => Number(b.total_count) || 0)
    );
  }, [data.brandGroups]);

  const parentSentimentChart = useMemo(() => {
    if (!data.parentSummary?.parents) return null;
    const rows = data.parentSummary.parents.filter((p) => p.parent_company !== "unmatched");
    if (!rows.length) return null;
    return makeStackedPercentOption("Parent Company Sentiment (Share)", rows.map((p) => p.parent_company), [
      { name: "Negative", color: "#b1453f", values: rows.map((p) => p.negative_rate ?? 0) },
      { name: "Neutral", color: "#8b8e8a", values: rows.map((p) => p.neutral_rate ?? 0) },
      { name: "Positive", color: "#0f6b5d", values: rows.map((p) => p.positive_rate ?? 0) },
    ]);
  }, [data.parentSummary]);

  const parentTimesChart = useMemo(() => {
    if (!data.parentTimes?.time_slices) return null;
    const slices = data.parentTimes.time_slices.slice(0, 30);
    return makeLineOption(
      "Parent Sentiment Over Time",
      slices.map((s) => s.time_slice_start),
      slices.map((s) => s.net_sentiment)
    );
  }, [data.parentTimes]);

  const deepSentimentChart = useMemo(() => {
    if (!data.deepSummary?.parents) return null;
    const rows = data.deepSummary.parents.filter((p) => p.parent_company !== "unmatched");
    if (!rows.length) return null;
    const sample = rows[0] || {};
    const rateKeys = Object.keys(sample).filter((key) => key.endsWith("_rate"));
    if (!rateKeys.length) return null;
    const seriesDefs = rateKeys.map((key, idx) => ({
      name: key.replace(/_rate$/, "").replace(/_/g, " "),
      color: colorForEmotion(key, ["#0f6b5d", "#b1453f", "#8b8e8a", "#d39b2a", "#4a6ea8", "#7b5aa6", "#3f7f74"][idx % 7]),
      values: rows.map((p) => p[key] ?? 0),
    }));
    return makeStackedPercentOption(
      "Deep Emotion Share",
      rows.map((p) => p.parent_company),
      seriesDefs
    );
  }, [data.deepSummary]);

  const deepTimesChart = useMemo(() => {
    if (!data.deepTimes?.time_slices) return null;
    const slices = data.deepTimes.time_slices.slice(0, 30);
    return makeLineOption(
      "Deep Emotion Over Time",
      slices.map((s) => s.time_slice_start),
      slices.map((s) => s.tweet_count)
    );
  }, [data.deepTimes]);

  const deepCompanyPie = useMemo(() => {
    if (!selectedCompany || !data.deepSummary?.parents) return null;
    const row = data.deepSummary.parents.find((p) => p.parent_company === selectedCompany);
    if (!row) return null;
    const rateKeys = Object.keys(row).filter((key) => key.endsWith("_rate"));
    if (!rateKeys.length) return null;
    const rawSeries = rateKeys.map((key, idx) => ({
      name: key.replace(/_rate$/, "").replace(/_/g, " "),
      value: Number(row[key]) || 0,
      itemStyle: {
        color: colorForEmotion(
          key,
          ["#0f6b5d", "#b1453f", "#8b8e8a", "#d39b2a", "#4a6ea8", "#7b5aa6", "#3f7f74"][idx % 7]
        ),
      },
    }));
    const major = rawSeries.filter((item) => item.value >= 0.05);
    const minor = rawSeries.filter((item) => item.value < 0.05);
    const minorTotal = minor.reduce((sum, item) => sum + item.value, 0);
    const seriesData = minorTotal > 0 ? [...major, { name: "others", value: minorTotal, itemStyle: { color: "#b9b2a8" } }] : major;
    return {
      title: { text: "", left: "center" },
      tooltip: { trigger: "item", formatter: "{b}: {d}%" },
      legend: { bottom: 0, textStyle: { color: "#2a2a2a" } },
      series: [
        {
          type: "pie",
          radius: ["30%", "60%"],
          data: seriesData,
          label: { formatter: "{b}" },
        },
      ],
    };
  }, [data.deepSummary, selectedCompany]);

  const deepCompanyTweets = useMemo(() => {
    if (!selectedCompany) return [];
    const mapRecords = Array.isArray(data.deepMap) ? data.deepMap : [];
    const sentimentRecords = data.deepSentiment?.records || [];
    if (!mapRecords.length || !sentimentRecords.length) return [];

    const textById = new Map();
    for (const record of sentimentRecords) {
      const key = String(record.pipeline_row_id || record.tweet_id || "");
      if (!key) continue;
      if (!textById.has(key)) {
        textById.set(key, { text: record.text || "", username: record.username || "" });
      }
    }

    const rows = mapRecords.filter(
      (record) => record.primary_parent_company === selectedCompany && record.sentiment_label
    );
    const byEmotion = {};
    for (const record of rows) {
      const emotion = String(record.sentiment_label || "").toLowerCase();
      if (!emotion) continue;
      const key = String(record.pipeline_row_id || record.tweet_id || "");
      const payload = textById.get(key);
      const text = payload?.text || "";
      if (!text) continue;
      if (!byEmotion[emotion]) byEmotion[emotion] = [];
      byEmotion[emotion].push({
        text,
        username: payload?.username || "",
        confidence: Number(record.confidence) || 0,
        emotion,
      });
    }

    const ordered = Object.keys(byEmotion).sort();
    const slides = [];
    for (const emotion of ordered) {
      const picks = byEmotion[emotion]
        .filter((item) => item.confidence >= 0.9)
        .sort((a, b) => b.confidence - a.confidence)
        .slice();
      slides.push(...picks);
    }
    if (selectedEmotion === "all") {
      return slides;
    }
    return slides.filter((item) => item.emotion === selectedEmotion);
  }, [data.deepMap, data.deepSentiment, selectedCompany, selectedEmotion]);

  const activeSlide = deepCompanyTweets[slideIndex] || null;

  const emotionOptions = useMemo(() => {
    const mapRecords = Array.isArray(data.deepMap) ? data.deepMap : [];
    if (!mapRecords.length || !selectedCompany) return [];
    const emotions = new Set(
      mapRecords
        .filter((record) => record.primary_parent_company === selectedCompany && record.sentiment_label)
        .map((record) => String(record.sentiment_label || "").toLowerCase())
    );
    return ["all", ...Array.from(emotions).sort()];
  }, [data.deepMap, selectedCompany]);

  const hashtagWordCloud = useMemo(() => {
    if (!data.hashtags?.hashtags) return null;
    const words = topWords(
      data.hashtags.hashtags.map((h) => ({ name: h.hashtag, value: h.count })),
      50
    );
    return makeWordCloudOption("Hashtag Cloud", words);
  }, [data.hashtags]);

  const brandWordCloud = useMemo(() => {
    const brands = data.brandGroups?.brands;
    if (!Array.isArray(brands)) return null;
    const rows = brands.filter((b) => (b?.brand ?? "unmatched") !== "unmatched");
    if (!rows.length) return null;
    const words = topWords(
      rows.map((b) => ({ name: b.brand, value: Number(b.total_count) || 0 })),
      50
    );
    return makeWordCloudOption("Brand Group Cloud", words);
  }, [data.brandGroups]);

  const parentWordCloud = useMemo(() => {
    const parents = data.parentGroups?.parent_companies;
    if (!Array.isArray(parents)) return null;
    const rows = parents.filter((p) => (p?.parent_company ?? "unmatched") !== "unmatched");
    if (!rows.length) return null;
    const words = topWords(
      rows.map((p) => {
        if (typeof p.total_count === "number") {
          return { name: p.parent_company, value: p.total_count };
        }
        const brands = Array.isArray(p.brands) ? p.brands : [];
        const total = brands.reduce((sum, b) => sum + (Number(b.total_count) || 0), 0);
        return { name: p.parent_company, value: total };
      }),
      50
    );
    return makeWordCloudOption("Parent Company Cloud", words);
  }, [data.parentGroups]);

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Super Bowl Twitter Analysis</p>
          <h1>Campaign Pulse Dashboard</h1>
          <p className="lead">
            Explore hashtags, ad sentiment, and parent-company impact across game
            timelines. Powered by deterministic pipeline outputs.
          </p>
          <div className="view-toggle">
            <button
              type="button"
              className={view === "dashboard" ? "active" : ""}
              onClick={() => setView("dashboard")}
            >
              Dashboard
            </button>
            <button
              type="button"
              className={view === "wordclouds" ? "active" : ""}
              onClick={() => setView("wordclouds")}
            >
              Word Clouds
            </button>
          </div>
        </div>
        <YearSelector year={year} years={yearOptions} onChange={setYear} />
      </header>

      {status === "loading" ? <p className="loading">Loading data...</p> : null}

      {view === "dashboard" ? (
      <section className="grid wide">
        {hashtagChart ? (
          <ChartCard title="Hashtags" subtitle="Drag to scroll" option={hashtagChart} />
        ) : (
          <EmptyState title="Hashtags" detail={errors.hashtags || "Not available."} />
        )}

        {mentionChart ? (
          <ChartCard title="Mentions" subtitle="Drag to scroll" option={mentionChart} />
        ) : (
          <EmptyState title="Mentions" detail={errors.mentions || "Not available."} />
        )}

        {parentSentimentChart ? (
          <ChartCard
            title="Parent Company Sentiment"
            subtitle="Stacked sentiment share (drag to scroll)"
            option={parentSentimentChart}
          />
        ) : (
          <EmptyState title="Parent Company Sentiment" detail={errors.parentSummary || "Not available."} />
        )}

        {parentFrequencyChart ? (
          <ChartCard
            title="Parent Company Frequency"
            subtitle="Tweet counts by parent (drag to scroll)"
            option={parentFrequencyChart}
          />
        ) : (
          <EmptyState title="Parent Company Frequency" detail={errors.parentGroups || "Not available."} />
        )}

        {brandFrequencyChart ? (
          <ChartCard
            title="Brand Frequency"
            subtitle="Tweet counts by brand (drag to scroll)"
            option={brandFrequencyChart}
          />
        ) : (
          <EmptyState title="Brand Frequency" detail={errors.brandGroups || "Not available."} />
        )}

        {parentTimesChart ? (
          <ChartCard
            title="Sentiment Timeline"
            subtitle="Time-sliced sentiment (first 30 slices)"
            option={parentTimesChart}
          />
        ) : (
          <EmptyState title="Sentiment Timeline" detail={errors.parentTimes || "Not available."} />
        )}

        {deepSentimentChart ? (
          <ChartCard
            title="Deep Emotion Summary"
            subtitle="Stacked emotion share (drag to scroll)"
            option={deepSentimentChart}
          />
        ) : (
          <EmptyState title="Deep Emotion Summary" detail={errors.deepSummary || "Not available."} />
        )}

        <section className="card">
          <div className="card-header">
            <div>
              <h3>Deep Emotion Explorer</h3>
              <p className="muted">Search a parent company to view emotion breakdowns.</p>
            </div>
          </div>
          <div className="company-search">
            <input
              list="company-options"
              value={companyInput}
              placeholder="Search parent company..."
              onChange={(event) => setCompanyInput(event.target.value)}
              onBlur={() => setSelectedCompany(companyInput)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  setSelectedCompany(companyInput);
                }
              }}
            />
            <datalist id="company-options">
              {companyOptions.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </div>
        </section>

        {deepCompanyPie ? (
          <ChartCard
            title="Deep Emotion Breakdown"
            subtitle={`Selected: ${selectedCompany}`}
            option={deepCompanyPie}
          />
        ) : (
          <EmptyState title="Deep Emotion Breakdown" detail={errors.deepSummary || errors.deepSentiment || "Not available."} />
        )}

        <section className="card">
          <div className="card-header">
            <div>
              <h3>Representative Tweets</h3>
              <p className="muted">Highest-confidence tweets for the selected company (≥ 0.90).</p>
            </div>
            <div className="tweet-nav">
              <button
                type="button"
                onClick={() => setSlideIndex((idx) => Math.max(idx - 1, 0))}
                disabled={slideIndex <= 0}
              >
                Prev
              </button>
              <span className="tweet-count">
                {deepCompanyTweets.length ? `${slideIndex + 1} / ${deepCompanyTweets.length}` : "0 / 0"}
              </span>
              <button
                type="button"
                onClick={() => setSlideIndex((idx) => Math.min(idx + 1, deepCompanyTweets.length - 1))}
                disabled={slideIndex >= deepCompanyTweets.length - 1}
              >
                Next
              </button>
            </div>
          </div>
          <div className="tweet-filter">
            <label htmlFor="emotion-filter">Emotion</label>
            <select
              id="emotion-filter"
              value={selectedEmotion}
              onChange={(event) => {
                setSelectedEmotion(event.target.value);
                setSlideIndex(0);
              }}
            >
              {emotionOptions.map((emotion) => (
                <option key={emotion} value={emotion}>
                  {emotion === "all" ? "All" : emotion}
                </option>
              ))}
            </select>
          </div>
          {activeSlide ? (
            <div className="tweet-card">
              <div className="tweet-header">
                <span className="tweet-handle">
                  {activeSlide.username ? `@${activeSlide.username}` : "@unknown"}
                </span>
                <span className="tweet-emotion">{activeSlide.emotion}</span>
              </div>
              <p className="tweet-text">{activeSlide.text}</p>
              <div className="tweet-meta">confidence {activeSlide.confidence.toFixed(2)}</div>
            </div>
          ) : (
            <EmptyState title="Representative Tweets" detail={errors.deepSentiment || "Not available."} />
          )}
        </section>

        {deepTimesChart ? (
          <ChartCard
            title="Deep Emotion Timeline"
            subtitle="Tweet volume per time slice"
            option={deepTimesChart}
          />
        ) : (
          <EmptyState title="Deep Emotion Timeline" detail={errors.deepTimes || "Not available."} />
        )}
      </section>
      ) : (
      <section className="grid wide">
        {hashtagWordCloud ? (
          <ChartCard title="Hashtag Word Cloud" subtitle="Hashtag frequency" option={hashtagWordCloud} />
        ) : (
          <EmptyState title="Hashtag Word Cloud" detail={errors.hashtags || "Not available."} />
        )}

        {brandWordCloud ? (
          <ChartCard title="Brand Group Word Cloud" subtitle="Brand group frequency" option={brandWordCloud} />
        ) : (
          <EmptyState title="Brand Group Word Cloud" detail={errors.brandGroups || "Not available."} />
        )}

        {parentWordCloud ? (
          <ChartCard title="Parent Company Word Cloud" subtitle="Parent company frequency" option={parentWordCloud} />
        ) : (
          <EmptyState title="Parent Company Word Cloud" detail={errors.parentGroups || "Not available."} />
        )}
      </section>
      )}

      <section className="card metrics">
        <h3>Auxiliary Breakdown Files</h3>
        <MetricRow label="Parent Emotion Breakdown" value={errors.parentBreakdown ? "Missing" : "Loaded"} />
        <MetricRow label="Brand Emotion Breakdown" value={errors.brandBreakdown ? "Missing" : "Loaded"} />
        <p className="muted">
          These files live under <code>outputs/aux/{year}/</code>. Generate them with
          the emotion breakdown script.
        </p>
      </section>
    </div>
  );
}
