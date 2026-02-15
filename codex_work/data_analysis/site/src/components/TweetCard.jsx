import React from "react";

export default function TweetCard({ scope, tweet, index, total, onPrev, onNext }) {
  return (
    <section className="tweet-card">
      <header>
        <div className="tweet-user">@{scope}_dataset</div>
        <div className="tweet-count">
          {total ? `${index + 1} / ${total}` : "0 / 0"}
        </div>
      </header>
      <p>{tweet?.text || "No tweets available"}</p>
      <footer>
        <button onClick={onPrev} disabled={!total || index <= 0}>
          ←
        </button>
        <button onClick={onNext} disabled={!total || index >= total - 1}>
          →
        </button>
      </footer>
    </section>
  );
}
