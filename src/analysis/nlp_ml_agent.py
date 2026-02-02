from collections import Counter, defaultdict

from src.analysis.nlp_agent import EMOTIONS, NLPAggregator, NLPOutputs, classify_emotion


class EmotionMLAgent:
    """
    ML-first emotion agent with automatic lexicon fallback.

    - Trains a lightweight text classifier with pseudo-labels derived from seed
      lexicon rules.
    - Uses NLTK tokenization/stemming + PyTorch EmbeddingBag classifier when the
      libraries are available.
    - Falls back to deterministic lexicon grouping when ML libs are unavailable or
      training data is insufficient.
    """

    def __init__(
        self,
        *,
        top_n: int = 500,
        similarity_threshold: float = 0.72,
        sample_limit: int = 20,
        min_confidence: float = 0.45,
        min_margin: float = 0.10,
        min_training_rows: int = 200,
        max_training_rows: int = 200_000,
        epochs: int = 5,
        batch_size: int = 512,
        embedding_dim: int = 64,
    ) -> None:
        self.min_confidence = min_confidence
        self.min_margin = min_margin
        self.min_training_rows = min_training_rows
        self.max_training_rows = max_training_rows
        self.epochs = epochs
        self.batch_size = batch_size
        self.embedding_dim = embedding_dim

        self.fallback = NLPAggregator(
            top_n=top_n, similarity_threshold=similarity_threshold, sample_limit=sample_limit
        )
        self.rows: list[dict] = []
        self.mode = "lexicon"

    def update(self, rows: list[dict]) -> None:
        self.fallback.update(rows)
        remaining = self.max_training_rows - len(self.rows)
        if remaining > 0:
            self.rows.extend(rows[:remaining])

    def finalize(self) -> NLPOutputs:
        base = self.fallback.finalize()
        imports = self._try_imports()
        if imports is None:
            base.model_mode = "ml_fallback_lexicon"
            return base

        torch, nn, optim, TweetTokenizer, PorterStemmer = imports
        train_rows = self.rows
        if len(train_rows) < self.min_training_rows:
            base.model_mode = "ml_fallback_lexicon"
            return base

        tokenizer = TweetTokenizer(preserve_case=False, strip_handles=False, reduce_len=True)
        stemmer = PorterStemmer()

        # Build pseudo-labeled corpus from non-neutral rows.
        labels_map = {emotion: idx for idx, emotion in enumerate(EMOTIONS)}
        pseudo: list[tuple[list[str], int]] = []
        infer_tokens: list[list[str]] = []
        infer_ad_names: list[str] = []
        infer_texts: list[str] = []

        for row in train_rows:
            text = str(row.get("normalized_text", ""))
            if not text:
                continue
            tokens = self._tokens(text, tokenizer, stemmer)
            if not tokens:
                continue
            infer_tokens.append(tokens)
            infer_ad_names.append(str(row.get("brand_ad_name", "")).strip() or "UNKNOWN_AD")
            infer_texts.append(text[:280])

            emotion = classify_emotion(text)
            if emotion is None:
                continue
            pseudo.append((tokens, labels_map[emotion]))

        if len(pseudo) < self.min_training_rows:
            base.model_mode = "ml_fallback_lexicon"
            return base

        vocab = self._build_vocab([toks for toks, _ in pseudo], min_count=2)
        if len(vocab) < 20:
            base.model_mode = "ml_fallback_lexicon"
            return base

        train_sequences = [self._to_ids(tokens, vocab) for tokens, _ in pseudo]
        train_labels = [label for _, label in pseudo]
        if not train_sequences:
            return base

        model = self._EmotionNet(len(vocab), self.embedding_dim, len(EMOTIONS), nn)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.01)

        model.train()
        for _ in range(self.epochs):
            for start in range(0, len(train_sequences), self.batch_size):
                xs = train_sequences[start : start + self.batch_size]
                ys = train_labels[start : start + self.batch_size]
                text_tensor, offsets = self._pack_sequences(xs, torch)
                y_tensor = torch.tensor(ys, dtype=torch.long)
                optimizer.zero_grad()
                logits = model(text_tensor, offsets)
                loss = criterion(logits, y_tensor)
                loss.backward()
                optimizer.step()

        # Infer over rows and retain confident non-neutral predictions only.
        model.eval()
        ad_emotion: dict[str, Counter] = defaultdict(Counter)
        examples: dict[str, list[str]] = defaultdict(list)
        counts: Counter = Counter()

        with torch.no_grad():
            for tokens, ad_name, text in zip(infer_tokens, infer_ad_names, infer_texts):
                ids = self._to_ids(tokens, vocab)
                if not ids:
                    continue
                text_tensor, offsets = self._pack_sequences([ids], torch)
                logits = model(text_tensor, offsets)
                probs = torch.softmax(logits, dim=1)[0]
                top_prob, top_idx = torch.max(probs, dim=0)
                sorted_probs, _ = torch.sort(probs, descending=True)
                margin = float(sorted_probs[0] - (sorted_probs[1] if len(sorted_probs) > 1 else 0.0))
                if float(top_prob) < self.min_confidence or margin < self.min_margin:
                    continue
                emotion = EMOTIONS[int(top_idx)]
                counts[emotion] += 1
                ad_emotion[ad_name][emotion] += 1
                if len(examples[emotion]) < self.fallback.sample_limit:
                    examples[emotion].append(text)

        if sum(counts.values()) == 0:
            base.model_mode = "ml_fallback_lexicon"
            return base

        emotion_by_ad_rows: list[dict] = []
        for ad_name, ctr in ad_emotion.items():
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

        emotion_examples_rows = [
            {"emotion": emotion, "tweet_text": sample}
            for emotion in EMOTIONS
            for sample in examples.get(emotion, [])
        ]

        self.mode = "ml_torch_nltk"
        return NLPOutputs(
            emotion_by_ad_rows=emotion_by_ad_rows,
            hashtag_similarity_rows=base.hashtag_similarity_rows,
            emotion_examples_rows=emotion_examples_rows,
            emotion_counts={k: int(v) for k, v in counts.items()},
            model_mode=self.mode,
        )

    @staticmethod
    def _try_imports():
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from nltk.stem import PorterStemmer
            from nltk.tokenize import TweetTokenizer
        except Exception:
            return None
        return torch, nn, optim, TweetTokenizer, PorterStemmer

    @staticmethod
    def _tokens(text: str, tokenizer, stemmer) -> list[str]:
        out: list[str] = []
        for tok in tokenizer.tokenize(text):
            cleaned = "".join(ch for ch in tok.lower() if ch.isalnum() or ch in {"#", "@"})
            if not cleaned:
                continue
            out.append(stemmer.stem(cleaned))
        return out

    @staticmethod
    def _build_vocab(token_lists: list[list[str]], min_count: int = 2) -> dict[str, int]:
        counts = Counter()
        for toks in token_lists:
            counts.update(toks)
        vocab = {"<unk>": 0}
        for token, count in counts.items():
            if count >= min_count:
                vocab[token] = len(vocab)
        return vocab

    @staticmethod
    def _to_ids(tokens: list[str], vocab: dict[str, int]) -> list[int]:
        unk = vocab["<unk>"]
        return [vocab.get(tok, unk) for tok in tokens]

    @staticmethod
    def _pack_sequences(seqs: list[list[int]], torch):
        offsets = [0]
        flat: list[int] = []
        for s in seqs:
            flat.extend(s)
            offsets.append(len(flat))
        text_tensor = torch.tensor(flat if flat else [0], dtype=torch.long)
        offsets_tensor = torch.tensor(offsets[:-1], dtype=torch.long)
        return text_tensor, offsets_tensor

    class _EmotionNet:
        def __init__(self, vocab_size: int, emb_dim: int, num_classes: int, nn) -> None:
            self.nn = nn
            self.embed = nn.EmbeddingBag(vocab_size, emb_dim, mode="mean")
            self.head = nn.Linear(emb_dim, num_classes)
            self._model = nn.Sequential()

        def parameters(self):
            return list(self.embed.parameters()) + list(self.head.parameters())

        def train(self):
            self.embed.train()
            self.head.train()

        def eval(self):
            self.embed.eval()
            self.head.eval()

        def __call__(self, text_tensor, offsets):
            x = self.embed(text_tensor, offsets)
            return self.head(x)
