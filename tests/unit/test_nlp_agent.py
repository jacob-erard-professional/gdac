import unittest

from src.analysis.nlp_agent import NLPAggregator, classify_emotion


class NLPAgentTests(unittest.TestCase):
    def test_classify_known_emotions(self) -> None:
        self.assertEqual(classify_emotion("I am so excited for this ad!"), "Excitement")
        self.assertEqual(classify_emotion("I am proud of this team and campaign"), "Pride")
        self.assertEqual(classify_emotion("This was disgusting and awful"), "Disgust")

    def test_neutral_or_ambiguous_returns_none(self) -> None:
        self.assertIsNone(classify_emotion("The game is on tonight."))
        self.assertIsNone(classify_emotion("I am happy and surprised"))

    def test_aggregator_outputs(self) -> None:
        rows = [
            {
                "normalized_text": "so excited for #SuperBowl ad @BrandA",
                "brand_ad_name": "AdA",
                "raw_hashtags": "[{'tag':'SuperBowl'}]",
                "raw_mentions": "[{'username':'BrandA'}]",
            },
            {
                "normalized_text": "proud of #Super_Bowl campaign @BrandA",
                "brand_ad_name": "AdA",
                "raw_hashtags": "[{'tag':'Super_Bowl'}]",
                "raw_mentions": "[{'username':'BrandA'}]",
            },
        ]
        nlp = NLPAggregator(top_n=50, similarity_threshold=0.3, sample_limit=5)
        nlp.update(rows)
        out = nlp.finalize()
        self.assertGreaterEqual(len(out.emotion_by_ad_rows), 1)
        self.assertGreaterEqual(len(out.hashtag_similarity_rows), 1)

