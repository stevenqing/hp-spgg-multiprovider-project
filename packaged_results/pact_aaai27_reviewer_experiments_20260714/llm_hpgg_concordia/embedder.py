"""Small deterministic embedder for Concordia smoke runs."""

from __future__ import annotations

import hashlib
import math
import re

import numpy as np


class HashingEmbedder:
    """Callable bag-of-words hashing embedder with deterministic output."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def __call__(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=float)
        for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(float(np.dot(vector, vector)))
        if norm > 0:
            vector /= norm
        return vector
