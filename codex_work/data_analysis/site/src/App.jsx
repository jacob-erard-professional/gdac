import React, { useEffect, useMemo, useState } from "react";
import ChartCard from "./components/ChartCard.jsx";
import EmptyState from "./components/EmptyState.jsx";
import MetricRow from "./components/MetricRow.jsx";
import YearSelector from "./components/YearSelector.jsx";
import { buildPath, loadJson } from "./data/loaders.js";
import { loadYearIndex } from "./data/years.js";

const ANALYTICS_ROOT = "/outputs/analytics";
const AUX_ROOT = "/outputs/aux";

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
        { key: "adSentiment", path: buildPath(ANALYTICS_ROOT, year, "ad_sentiment_summary.json") },
        { key: "parentSummary", path: buildPath(ANALYTICS_ROOT, year, "parent_company_sentiment_summary.json") },
        { key: "parentTimes", path: buildPath(ANALYTICS_ROOT, year, "parent_company_sentiment_timeslices.json") },
        { key: "deepSummary", path: buildPath(ANALYTICS_ROOT, year, "parent_company_deep_sentiment_summary.json") },
        { key: "deepTimes", path: buildPath(ANALYTICS_ROOT, year, "parent_company_deep_sentiment_timeslices.json") },
        { key: "parentBreakdown", path: buildPath(AUX_ROOT, year, "parent_company_emotion_breakdown.json") },
        { key: "brandBreakdown", path: buildPath(AUX_ROOT, year, "brand_emotion_breakdown.json") },
      ];

      await Promise.all(
        targets.map(async ({ key, path }) => {
          try {
            results[key] = await loadJson(path);
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
  const { status, data, errors } = useData(year);

  useEffect(() => {
    loadYearIndex().then(setYearOptions);
  }, []);

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

  const adSentimentChart = useMemo(() => {
    if (!data.adSentiment?.ads) return null;
    const top = data.adSentiment.ads.slice(0, 12);
    return makeBarOption(
      "Ad Sentiment (Net)",
      top.map((a) => a.ad_tag),
      top.map((a) => a.net_sentiment)
    );
  }, [data.adSentiment]);

  const parentSentimentChart = useMemo(() => {
    if (!data.parentSummary?.parents) return null;
    const top = data.parentSummary.parents.slice(0, 12);
    return makeBarOption(
      "Parent Company Sentiment (Net)",
      top.map((p) => p.parent_company),
      top.map((p) => p.net_sentiment)
    );
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
    const top = data.deepSummary.parents.slice(0, 12);
    const labelKey = Object.keys(top[0] || {}).find((k) => k.endsWith("_rate"));
    if (!labelKey) return null;
    return makeBarOption(
      "Deep Emotion (Top Rate)",
      top.map((p) => p.parent_company),
      top.map((p) => p[labelKey])
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
        </div>
        <YearSelector year={year} years={yearOptions} onChange={setYear} />
      </header>

      {status === "loading" ? <p className="loading">Loading data...</p> : null}

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

        {adSentimentChart ? (
          <ChartCard title="Ad Sentiment" subtitle="Net sentiment by ad" option={adSentimentChart} />
        ) : (
          <EmptyState title="Ad Sentiment" detail={errors.adSentiment || "Not available."} />
        )}

        {parentSentimentChart ? (
          <ChartCard
            title="Parent Company Sentiment"
            subtitle="Net sentiment by parent"
            option={parentSentimentChart}
          />
        ) : (
          <EmptyState title="Parent Company Sentiment" detail={errors.parentSummary || "Not available."} />
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
            subtitle="Highest emotion rate by parent"
            option={deepSentimentChart}
          />
        ) : (
          <EmptyState title="Deep Emotion Summary" detail={errors.deepSummary || "Not available."} />
        )}

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
