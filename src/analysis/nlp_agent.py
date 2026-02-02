import ast
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher


EMOTIONS = [
    "Joy",
    "Excitement",
    "Anger",
    "Disappointment",
    "Surprise",
    "Disgust",
    "Pride",
]


DEFAULT_LEXICON = {
    "Joy": {
        "joy",
        "happy",
        "glad",
        "love",
        "awesome",
        "great",
        "amazing",
        "delighted",
        "fun",
    },
    "Excitement": {
        "excited",
        "hype",
        "hyped",
        "thrilling",
        "epic",
        "fire",
        "lit",
        "letsgo",
        "cantwait",
    },
    "Anger": {
        "angry",
        "mad",
        "hate",
        "annoyed",
        "outrage",
        "pissed",
    },
    "Disappointment": {
        "disappointed",
        "letdown",
        "underwhelming",
        "boring",
        "bad",
        "worst",
        "sucks",
        "suck",
    },
    "Surprise": {
        "surprised",
        "unexpected",
        "shocked",
        "wow",
        "omg",
        "unbelievable",
    },
    "Disgust": {
        "disgusting",
        "gross",
        "cringe",
        "nasty",
        "awful",
        "trash",
    },
    "Pride": {
        "proud",
        "respect",
        "salute",
        "inspiring",
        "legendary",
        "represent",
    },
}


def _parse_entity_list(value: object) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict)]
    except (ValueError, SyntaxError):
        return []
    return []


def _hashtags_from_row(row: dict) -> list[str]:
    extracted: list[str] = []
    for h in _parse_entity_list(row.get("raw_hashtags")):
        tag = str(h.get("tag", "")).strip()
        if tag:
            extracted.append(tag.lower())
    if extracted:
        return extracted
    return [m.lower() for m in re.findall(r"#([A-Za-z0-9_]+)", str(row.get("normalized_text", "")))]


def _tokenize_text(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]", "", token.lower())


def classify_emotion(text: str, lexicon: dict[str, set[str]] | None = None) -> str | None:
    lex = lexicon or DEFAULT_LEXICON
    tokens = [_normalize_token(t) for t in _tokenize_text(text)]
    if not tokens:
        return None

    scores: dict[str, int] = {emotion: 0 for emotion in EMOTIONS}
    for emotion in EMOTIONS:
        words = lex.get(emotion, set())
        scores[emotion] = sum(1 for t in tokens if t in words)

    # Exclamation marks can strengthen excitement only when excitement already appears.
    if "!" in text and scores["Excitement"] > 0:
        scores["Excitement"] += 1

    max_score = max(scores.values())
    if max_score <= 0:
        return None

    winners = [emotion for emotion, score in scores.items() if score == max_score]
    if len(winners) != 1:
        # Avoid ambiguous/neutral assignments.
        return None
    return winners[0]


def _hashtag_tokens(tag: str) -> set[str]:
    tag = tag.strip("#").lower()
    parts = re.split(r"[_\-\s]+", tag)
    tokens: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        camel = re.findall(r"[a-z]+|[0-9]+", p)
        tokens.extend(camel or [p])
    return {t for t in tokens if t}


def _hashtag_similarity(a: str, b: str) -> float:
    at = _hashtag_tokens(a)
    bt = _hashtag_tokens(b)
    if at and bt:
        inter = len(at & bt)
        union = len(at | bt)
        if union > 0:
            jaccard = inter / union
            if jaccard > 0:
                return jaccard
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()


@dataclass(slots=True)
class NLPOutputs:
    emotion_by_ad_rows: list[dict]
    hashtag_similarity_rows: list[dict]
    emotion_examples_rows: list[dict]
    emotion_counts: dict[str, int]
    model_mode: str = "lexicon"


class NLPAggregator:
    def __init__(self, top_n: int = 500, similarity_threshold: float = 0.72, sample_limit: int = 20) -> None:
        self.top_n = top_n
        self.similarity_threshold = similarity_threshold
        self.sample_limit = sample_limit
        self.emotion_counts: Counter = Counter()
        self.ad_emotion_counts: dict[str, Counter] = defaultdict(Counter)
        self.hashtag_counts: Counter = Counter()
        self.samples_by_emotion: dict[str, list[str]] = defaultdict(list)

    def update(self, rows: list[dict]) -> None:
        for row in rows:
            text = str(row.get("normalized_text", ""))
            emotion = classify_emotion(text)
            if emotion:
                ad_name = str(row.get("brand_ad_name", "")).strip() or "UNKNOWN_AD"
                self.emotion_counts[emotion] += 1
                self.ad_emotion_counts[ad_name][emotion] += 1
                if len(self.samples_by_emotion[emotion]) < self.sample_limit:
                    self.samples_by_emotion[emotion].append(text[:280])
            for tag in _hashtags_from_row(row):
                self.hashtag_counts[tag] += 1

    def finalize(self) -> NLPOutputs:
        emotion_by_ad_rows: list[dict] = []
        for ad_name, ctr in self.ad_emotion_counts.items():
            total = sum(ctr.values())
            for emotion in EMOTIONS:
                count = int(ctr.get(emotion, 0))
                if count <= 0:
                    continue
                emotion_by_ad_rows.append(
                    {
                        "brand_ad_name": ad_name,
                        "emotion": emotion,
                        "count": count,
                        "share_within_ad": (count / total) if total else 0.0,
                    }
                )
        emotion_by_ad_rows.sort(key=lambda r: (-r["count"], r["brand_ad_name"], r["emotion"]))

        tags = [t for t, _ in self.hashtag_counts.most_common(self.top_n)]
        hashtag_similarity_rows: list[dict] = []
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                a, b = tags[i], tags[j]
                sim = _hashtag_similarity(a, b)
                if sim >= self.similarity_threshold:
                    hashtag_similarity_rows.append(
                        {
                            "hashtag_a": a,
                            "hashtag_b": b,
                            "similarity": round(sim, 4),
                            "count_a": int(self.hashtag_counts[a]),
                            "count_b": int(self.hashtag_counts[b]),
                        }
                    )
        hashtag_similarity_rows.sort(key=lambda r: (-r["similarity"], -(r["count_a"] + r["count_b"])))

        emotion_examples_rows: list[dict] = []
        for emotion in EMOTIONS:
            for sample in self.samples_by_emotion.get(emotion, []):
                emotion_examples_rows.append({"emotion": emotion, "tweet_text": sample})

        return NLPOutputs(
            emotion_by_ad_rows=emotion_by_ad_rows,
            hashtag_similarity_rows=hashtag_similarity_rows,
            emotion_examples_rows=emotion_examples_rows,
            emotion_counts={k: int(v) for k, v in self.emotion_counts.items()},
            model_mode="lexicon",
        )
