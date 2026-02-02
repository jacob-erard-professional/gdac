import unittest

from src.analysis.nlp_ml_agent import EmotionMLAgent


class EmotionMLAgentTests(unittest.TestCase):
    def test_fallback_mode_without_ml_libs(self) -> None:
        agent = EmotionMLAgent(top_n=50, min_training_rows=2)
        agent.update(
            [
                {
                    "normalized_text": "so excited for this ad #SuperBowl @BrandA",
                    "brand_ad_name": "AdA",
                    "raw_hashtags": "[{'tag':'SuperBowl'}]",
                    "raw_mentions": "[{'username':'BrandA'}]",
                },
                {
                    "normalized_text": "proud of this campaign #Ads @BrandA",
                    "brand_ad_name": "AdA",
                    "raw_hashtags": "[{'tag':'Ads'}]",
                    "raw_mentions": "[{'username':'BrandA'}]",
                },
            ]
        )
        out = agent.finalize()
        self.assertIn(out.model_mode, {"lexicon", "ml_torch_nltk", "ml_fallback_lexicon"})
        self.assertGreaterEqual(len(out.emotion_by_ad_rows), 1)
