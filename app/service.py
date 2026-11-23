import json
from pathlib import Path

import numpy as np

from app.config import Settings
from app.embeddings import Embedder
from app.index import InMemoryIndex
from app.schemas import (
    FieldScores,
    Product,
    RecommendationItem,
    RecommendationResponse,
)


#Read products and their stored embeddings from the catalog file.
def load_catalog(path: str, expected_model: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    # Query vectors must come from the SAME model as the stored product vectors.
    if data["model"] != expected_model:
        raise ValueError(
            f"catalog was built with '{data['model']}' but EMBEDDING_MODEL is '{expected_model}'. "
            "Re-run: python -m scripts.build_catalog"
        )

    products, name_vecs, desc_vecs = [], [], []
    for item in data["products"]:
        name_vecs.append(item.pop("name_embedding"))
        desc_vecs.append(item.pop("description_embedding"))
        products.append(Product(**item))

    ids = [p.id for p in products]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate product ids in catalog")

    return products, np.array(name_vecs, dtype=np.float32), np.array(desc_vecs, dtype=np.float32)

class RecommendationService:
    def __init__(self, index: InMemoryIndex, embedder: Embedder, settings: Settings):
        self.index = index
        self.embedder = embedder
        self.s = settings

    # Flow 1: user types a query

    def search(self, query, top_k=None, threshold=None, min_rating=None):
        top_k = top_k or self.s.default_top_k
        threshold = self.s.default_threshold if threshold is None else threshold

        q = self.embedder.embed([query.strip()]) [0] #the only API call at request time
        combined, name_s, desc_s = self.index.score_query(q, self.s.weight_name, self.s.weight_description)
        return self._rank("query", combined, name_s, desc_s, None, None, top_k, threshold, min_rating)

    #Flow 2: user taps a product
    def similar(self, product_id, top_k=None, threshold=None, min_rating=None):
        row = self.index.row_of(product_id)
        if row is None:
            return None
        top_k = top_k or self.s.default_top_k
        threshold = self.s.default_threshold if threshold is None else threshold

        combined, name_s, desc_s, rating_s = self.index.score_product(
            row, self.s.weight_name, self.s.weight_description, self.s.weight_rating, self.s.weight_catagory
        )
        return self._rank("similar", combined, name_s, desc_s, rating_s, row, top_k, threshold, min_rating)


    def _rank(self, mode, combined, name_s, desc_s, rating_s, exclude_row, top_k, threshold, min_rating):
        keep = combined >= threshold  # keep only scores above the threshold
        if exclude_row is not None:
            keep[exclude_row] =  False # never recommend the tapped product itself
        if min_rating is not None:
            keep &= self.index.ratings >= min_rating  #optional minimum rating

        candidates = np.flatnonzero(keep)

        #best score first; equal scores -> higher rating first; then keep top_k
        order = candidates[np.lexsort((-self.index.ratings[candidates], -combined[candidates]))][:top_k]

        results = [
            RecommendationItem(
                product=self.index.products[i],
                score=round(float(combined[i]), 4),
                field_scores=FieldScores(
                    name=round(float(name_s[i]), 4),
                    description=round(float(desc_s[i]), 4),
                    rating=None if rating_s is None else round(float(rating_s[i]), 4),
                ),
            )
            for i in order
        ]

        return RecommendationResponse(
            mode=mode, threshold=threshold, top_k=top_k, count=len(results), results=results
        )