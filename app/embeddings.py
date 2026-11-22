import time

import httpx
import numpy as np


class EmbeddingError(RuntimeError):
    pass


#Scale every vector to length 1, so cosine similarity becomes a plain dot product.
def l2_normalize(m: np.ndarray):
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return (m/np.clip(norms, 1e-12, None)).astype(np.float32)

#Turns texts into vectors using any embeddings API.
class Embedder:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_s: float = 30.0, batch_size: int = 64):
        if not api_key:
            raise EmbeddingError("EMBEDDING_API_KEY is not set")

        self.model = model
        self.batch_size = batch_size
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_s
        )

    def _post(self, batch: list[str]):
        last_error = None
        RETRY_STATUS_CODES = (429, 500, 502, 503, 504)
        for attempt in range(3):
            try:
                resp = self._client.post("/embeddings", json={"model": self.model, "input": batch})
                if resp.status_code in RETRY_STATUS_CODES:
                    last_error = f"status {resp.status_code}"
                    time.sleep(0.5 * 2**attempt)
                    continue
                resp.raise_for_status()
                data = sorted(resp.json()["data"], key=lambda d: d["index"])
                return [d["embedding"] for d in data]
            except httpx.TransportError as exc:
                last_error = exc
                time.sleep(0.5 * 2**attempt)
            except httpx.HTTPStatusError as exc:
                raise EmbeddingError(f"embedding API rejected the request ({exc.response.status_code})") from exc
        raise EmbeddingError(f"embedding request failed: {last_error}")

    #Returning a ready-to-use NumPy array.
    def embed(self, texts: list[str]):
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            vectors.extend(self._post(texts[i : i + self.batch_size]))
        return l2_normalize(np.asarray(vectors, dtype=np.float32))