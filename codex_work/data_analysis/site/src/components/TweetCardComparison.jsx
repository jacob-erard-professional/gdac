import React, { useEffect, useState } from "react";
import TweetCard from "./TweetCard";
import EmptyState from "./EmptyState";

export default function TweetCardComparison({ regular, full }) {
  const [regIdx, setRegIdx] = useState(0);
  const [fullIdx, setFullIdx] = useState(0);

  useEffect(() => {
    setRegIdx(0);
    setFullIdx(0);
  }, [regular, full]);

  if (!regular.length && !full.length) {
    return <EmptyState title="Example Tweets" detail="No tweet-card rows were available for this year." />;
  }

  return (
    <div className="tweet-grid">
      <TweetCard
        scope="regular"
        tweet={regular[regIdx]}
        index={regIdx}
        total={regular.length}
        onPrev={() => setRegIdx((x) => Math.max(0, x - 1))}
        onNext={() => setRegIdx((x) => Math.min(regular.length - 1, x + 1))}
      />
      <TweetCard
        scope="full"
        tweet={full[fullIdx]}
        index={fullIdx}
        total={full.length}
        onPrev={() => setFullIdx((x) => Math.max(0, x - 1))}
        onNext={() => setFullIdx((x) => Math.min(full.length - 1, x + 1))}
      />
    </div>
  );
}
