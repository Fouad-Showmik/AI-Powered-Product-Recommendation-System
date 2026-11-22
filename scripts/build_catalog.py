"""Run ONCE (and again whenever products.json or the model changes):

    python -m scripts.build_catalog

Reads data/products.json, embeds each product's name and description,
and writes everything to data/catalog.json.
"""
import json
from pathlib import Path

from app.config import get_settings
from app.embeddings import Embedder


def main() -> None:
    s = get_settings()
    embedder = Embedder(s.embedding_api_key, s.embedding_base_url, s.embedding_model)

    products = json.loads(Path(s.products_path).read_text(encoding="utf-8"))
    name_vecs = embedder.embed([p["name"] for p in products])
    desc_vecs = embedder.embed([p["description"] for p in products])

    for p, n, d in zip(products, name_vecs, desc_vecs):
        p["name_embedding"] = [round(float(x), 6) for x in n]          # rounding keeps the file smaller
        p["description_embedding"] = [round(float(x), 6) for x in d]

    out = Path(s.catalog_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"model": s.embedding_model, "products": products}), encoding="utf-8")
    print(f"Wrote {len(products)} products to {out} using model {s.embedding_model}")


if __name__ == "__main__":
    main()