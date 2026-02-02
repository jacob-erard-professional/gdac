import unittest

from src.analysis.brand_analytics import BrandAggregator


class BrandAnalyticsTests(unittest.TestCase):
    def test_groups_typos_and_aggregates_metrics(self) -> None:
        agg = BrandAggregator(typo_similarity_threshold=0.8)
        agg.update(
            [
                {
                    "brand_ad_name": "Pop Corners",
                    "retweet_count": "10",
                    "like_count": "100",
                    "reply_count": "2",
                    "quote_count": "3",
                },
                {
                    "brand_ad_name": "PopCorners",
                    "retweet_count": "5",
                    "like_count": "50",
                    "reply_count": "1",
                    "quote_count": "1",
                },
            ]
        )
        rows = agg.finalize(top_n=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["retweet_count"], 15.0)
        self.assertEqual(rows[0]["like_count"], 150.0)
        self.assertGreater(rows[0]["total_interaction"], 160.0)

