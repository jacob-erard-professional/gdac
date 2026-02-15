import React, { useEffect, useMemo, useState } from "react";
import YearSelector from "./components/YearSelector";
import DatasetScopeHeader from "./components/DatasetScopeHeader";
import EmptyState from "./components/EmptyState";
import ComparisonCloudGrid from "./components/ComparisonCloudGrid";
import TweetCardComparison from "./components/TweetCardComparison";
import { discoverComparableYears } from "./lib/yearDiscovery";
import { loadComparison, loadTweetCards } from "./lib/comparisonService";

const EMPTY_CLOUDS = {
  fullHashtagParent: [],
  regularCelebrity: [],
  fullCelebrity: [],
  regularRawBrand: [],
  fullRawBrand: [],
};

const EMPTY_STATUS = {
  fullHashtagParent: "missing",
  regularCelebrity: "missing",
  fullCelebrity: "missing",
  regularRawBrand: "missing",
  fullRawBrand: "missing",
};

export default function App() {
  const [years, setYears] = useState([]);
  const [year, setYear] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [clouds, setClouds] = useState(EMPTY_CLOUDS);
  const [statuses, setStatuses] = useState(EMPTY_STATUS);
  const [tweets, setTweets] = useState({ regular: [], full: [] });

  useEffect(() => {
    async function init() {
      setLoading(true);
      setError("");
      try {
        const found = await discoverComparableYears();
        setYears(found);
        if (found.length) setYear((cur) => cur || found[0]);
      } catch (err) {
        setError(String(err.message || err));
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  useEffect(() => {
    async function refresh() {
      if (!year) return;
      setLoading(true);
      setError("");
      try {
        const [cmp, tw] = await Promise.all([loadComparison(year), loadTweetCards(year)]);
        setClouds(cmp.clouds);
        setStatuses(cmp.statuses);
        setTweets(tw);
      } catch (err) {
        setError(String(err.message || err));
        setClouds(EMPTY_CLOUDS);
        setStatuses(EMPTY_STATUS);
        setTweets({ regular: [], full: [] });
      } finally {
        setLoading(false);
      }
    }
    refresh();
  }, [year]);

  const hasYears = useMemo(() => years.length > 0, [years]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <h1>Dataset Comparison Dashboard</h1>
        <YearSelector years={years} value={year} onChange={setYear} disabled={!hasYears || loading} />
      </header>

      {!hasYears && !loading ? (
        <EmptyState title="No Comparable Years" detail="No years contain both regular and full dataset folders." />
      ) : null}

      {error ? <EmptyState title="Loading Error" detail={error} /> : null}

      {year ? <DatasetScopeHeader year={year} /> : null}

      <ComparisonCloudGrid clouds={clouds} statuses={statuses} />

      <section className="tweet-section">
        <h2>Example Tweets</h2>
        <TweetCardComparison regular={tweets.regular} full={tweets.full} />
      </section>
    </main>
  );
}
