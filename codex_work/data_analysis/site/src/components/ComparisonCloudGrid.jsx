import React from "react";
import WordCloudPanel from "./WordCloudPanel";

export default function ComparisonCloudGrid({ clouds, statuses }) {
  return (
    <>
      <div className="cloud-grid">
        <WordCloudPanel title="Full Hashtag + Parent Groups" terms={clouds.fullHashtagParent} status={statuses.fullHashtagParent} />
        <WordCloudPanel title="Regular Celebrity Frequency" terms={clouds.regularCelebrity} status={statuses.regularCelebrity} />
        <WordCloudPanel title="Full Celebrity Frequency" terms={clouds.fullCelebrity} status={statuses.fullCelebrity} />
      </div>

      <div className="raw-brand-row">
        <WordCloudPanel title="Regular Raw Brand Frequency" terms={clouds.regularRawBrand} status={statuses.regularRawBrand} shape="middle" />
        <WordCloudPanel title="Full Raw Brand Frequency" terms={clouds.fullRawBrand} status={statuses.fullRawBrand} shape="middle" />
      </div>
    </>
  );
}
