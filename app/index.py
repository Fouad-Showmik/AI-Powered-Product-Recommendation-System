import numpy as np

from app.embeddings import l2_normalize
from app.schemas import Product

RATING_CENTERS = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
RATING_SIGMA = 0.75

#Turn a rating like 4.5 into a small vector so cosine similarity works on it.
def encode_rating(rating: float):
    v = np.exp(-((RATING_CENTERS - rating) **2) / (2 * RATING_SIGMA**2))
    return l2_normalize(v[None, :])[0]

class InMemoryIndex:
    def __init__(self, products: list[Product], name_vecs:np.ndarray, desc_vecs: np.ndarray):
        self.products = products
        self.id_to_row = {p.id: i for i, p in enumerate(products)}
        self.name_m = l2_normalize(name_vecs)  # shape (N, dim)
        self.desc_m = l2_normalize(desc_vecs)
        self.rating_m = np.stack([encode_rating(p.rating) for p in products])  # shape (N, 5)
        self.ratings = np.array([p.rating for p in products], dtype=np.float32)
        self.catagories = np.array([p.category or "" for p in products])

    def __len__(self):
        return len(self.products)

    def row_of(self, product_id: str):
        return self.id_to_row.get(product_id)

    #A text query can be compared with name and description vectors only.
    def score_query(self, q: np.ndarray, w_name: float, w_desc: float):
        name_s = self.name_m @ q # cosine similarity with every product's name
        desc_s = self.desc_m @ q #cosine similarity with every product's description
        combined = (w_name * name_s + w_desc * desc_s) / (w_name + w_desc)
        return combined, name_s, desc_s

    #A tapped product is compared with all products across all three vectors.
    def score_product(self, row: int, w_name: float, w_desc: float, w_rating: float, w_cat: float):
        name_s = self.name_m @ self.name_m[row]
        desc_s = self.desc_m @ self.desc_m[row]
        rating_s = self.rating_m @ self.rating_m[row]
        cat_s = (self.catagories == self.catagories[row]).astype(np.float32)
        total = w_name + w_desc + w_rating + w_cat
        combined = (w_name * name_s + w_desc * desc_s + w_rating * rating_s + w_cat * cat_s) / total
        return combined, name_s, desc_s, rating_s