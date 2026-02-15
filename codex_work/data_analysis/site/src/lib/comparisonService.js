import { getComparisonPayload, getTweetCardEntries } from "./comparisonApiClient";
import { dedupeTweetEntries } from "./tweetCardUtils";
import { STATUS } from "./statusModel";
import { cloudTerms, fullHashtagParentTerms } from "./analyticsParsers";

export async function loadComparison(year) {
  const payload = await getComparisonPayload(year);
  return {
    year,
    clouds: {
      fullHashtagParent: fullHashtagParentTerms(payload),
      regularCelebrity: cloudTerms(payload, "regular_celebrity"),
      fullCelebrity: cloudTerms(payload, "full_celebrity"),
      regularRawBrand: cloudTerms(payload, "regular_raw_brand"),
      fullRawBrand: cloudTerms(payload, "full_raw_brand"),
    },
    statuses: {
      fullHashtagParent: payload.statuses?.full_hashtag_parent || STATUS.MISSING,
      regularCelebrity: payload.statuses?.regular_celebrity || STATUS.MISSING,
      fullCelebrity: payload.statuses?.full_celebrity || STATUS.MISSING,
      regularRawBrand: payload.statuses?.regular_raw_brand || STATUS.MISSING,
      fullRawBrand: payload.statuses?.full_raw_brand || STATUS.MISSING,
    },
  };
}

export async function loadTweetCards(year) {
  const [regular, full] = await Promise.all([
    getTweetCardEntries(year, "regular"),
    getTweetCardEntries(year, "full"),
  ]);
  return {
    regular: dedupeTweetEntries(regular.entries || []),
    full: dedupeTweetEntries(full.entries || []),
  };
}
