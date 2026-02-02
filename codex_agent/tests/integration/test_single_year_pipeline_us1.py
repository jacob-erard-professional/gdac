import json
import tempfile
import unittest
from pathlib import Path

from src.orchestrator.run_pipeline import run_year


class SingleYearPipelineTests(unittest.TestCase):
    def test_single_year_run_outputs_csv_input(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(f"{td}/config").mkdir(parents=True)
            Path(f"{td}/config/pipeline.yaml").write_text(
                "event: super-bowl\n"
                "output_root: " + td + "/outputs\n"
                "raw_root: " + td + "/data/raw\n"
                "cleaned_root: " + td + "/data/cleaned\n"
                "processed_root: " + td + "/data/processed\n"
                "min_text_length: 1\n"
                "input_format: csv\n"
                "chunk_size: 2\n",
                encoding="utf-8",
            )
            Path("config/keywords.yaml").write_text("super-bowl:\n  - touchdown\n", encoding="utf-8")
            Path("config/kpi_definitions.yaml").write_text("version: 1.0.0\nkpis: []\n", encoding="utf-8")
            Path(f"{td}/data/raw/super-bowl/2025").mkdir(parents=True)
            Path(f"{td}/data/raw/super-bowl/2025/posts.csv").write_text(
                "source_record_id,event_name,created_at,text,brand_ad_name,public_metrics.retweet_count,public_metrics.like_count,public_metrics.reply_count,public_metrics.quote_count,entities.hashtags,entities.mentions\n"
                "1,super-bowl,2025-02-11T14:13:37.000Z,'so excited about this ad #superbowl @ew',AdA,10,20,1,2,\"[{'tag':'SuperBowl'}]\",\"[{'username':'EW'}]\"\n"
                "2,super-bowl,2/11/2025 14:13:37,'proud of this campaign #ads @nfl',AdA!,3,8,0,1,\"[{'tag':'Ads'}]\",\"[{'username':'NFL'}]\"\n",
                encoding="utf-8",
            )
            cfg = Path(f"{td}/config/pipeline.yaml")
            cfg.write_text(
                cfg.read_text(encoding="utf-8")
                + "csv_columns:\n"
                + "  source_record_id: source_record_id\n"
                + "  event_name: event_name\n"
                + "  year: created_at\n"
                + "  text: text\n"
                + "  brand_ad_name: brand_ad_name\n"
                + "  retweet_count: public_metrics.retweet_count\n"
                + "  like_count: public_metrics.like_count\n"
                + "  reply_count: public_metrics.reply_count\n"
                + "  quote_count: public_metrics.quote_count\n"
                + "  hashtags: entities.hashtags\n"
                + "  mentions: entities.mentions\n",
                encoding="utf-8",
            )
            result = run_year("super-bowl", 2025, f"{td}/config/pipeline.yaml")
            self.assertTrue(Path(result["manifest_path"]).exists())
            self.assertTrue(Path(result["artifact_index"]).exists())
            payload = json.loads(Path(result["artifact_index"]).read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(payload), 3)
            hashtag_file = Path(f"{td}/outputs/super-bowl/2025/kpis/hashtag_frequencies.jsonl")
            mention_file = Path(f"{td}/outputs/super-bowl/2025/kpis/mention_frequencies.jsonl")
            lex_emotion_by_ad_file = Path(f"{td}/outputs/super-bowl/2025/kpis/nlp_lexicon/emotion_by_ad.jsonl")
            ml_emotion_by_ad_file = Path(f"{td}/outputs/super-bowl/2025/kpis/nlp_ml/emotion_by_ad.jsonl")
            brand_file = Path(f"{td}/outputs/super-bowl/2025/kpis/brand_popularity.jsonl")
            roi_join_file = Path(f"{td}/outputs/super-bowl/2025/kpis/roi_join_ready.csv")
            self.assertTrue(hashtag_file.exists())
            self.assertTrue(mention_file.exists())
            self.assertTrue(lex_emotion_by_ad_file.exists())
            self.assertTrue(ml_emotion_by_ad_file.exists())
            self.assertTrue(brand_file.exists())
            self.assertTrue(roi_join_file.exists())
            self.assertGreaterEqual(len(hashtag_file.read_text(encoding="utf-8").strip().splitlines()), 1)
            self.assertGreaterEqual(len(mention_file.read_text(encoding="utf-8").strip().splitlines()), 1)
