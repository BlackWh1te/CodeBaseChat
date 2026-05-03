"""Simple TF-IDF search over indexed chunks."""

import json
import math
import re
from pathlib import Path
from collections import Counter


def tokenize(text: str) -> list[str]:
    """Lowercase, strip non-alphanum, split on whitespace."""
    return re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())


def compute_idf(documents: list[list[str]]) -> dict[str, float]:
    """Compute IDF scores."""
    N = len(documents)
    idf = {}
    all_terms = set(term for doc in documents for term in doc)
    for term in all_terms:
        df = sum(1 for doc in documents if term in doc)
        idf[term] = math.log((N + 1) / (df + 1)) + 1
    return idf


def tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """Compute normalized TF-IDF vector."""
    tf = Counter(tokens)
    vec = {term: tf[term] * idf.get(term, 0) for term in tf}
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return vec
    return {term: v / norm for term, v in vec.items()}


def cosine_sim(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    common = set(a) & set(b)
    if not common:
        return 0.0
    return sum(a[t] * b[t] for t in common)


class SearchEngine:
    def __init__(self, index_file: Path):
        self.chunks = []
        self.idf = {}
        self.vectors = []
        self._load(index_file)

    def _load(self, index_file: Path):
        with index_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.chunks.append(json.loads(line))
        docs = [tokenize(c["text"]) for c in self.chunks]
        self.idf = compute_idf(docs)
        self.vectors = [tfidf_vector(d, self.idf) for d in docs]

    def query(self, q: str, top_k: int = 5) -> list[dict]:
        q_tokens = tokenize(q)
        q_vec = tfidf_vector(q_tokens, self.idf)
        scored = []
        for i, vec in enumerate(self.vectors):
            score = cosine_sim(q_vec, vec)
            if score > 0:
                scored.append((score, i))
        scored.sort(reverse=True)
        results = []
        for score, idx in scored[:top_k]:
            result = dict(self.chunks[idx])
            result["score"] = round(score, 4)
            results.append(result)
        return results
