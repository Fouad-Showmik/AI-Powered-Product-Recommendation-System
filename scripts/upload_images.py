"""Upload product images to Cloudinary and write image_url into products.json.

    python -m scripts.upload_images            # uploads only products without an image_url
    python -m scripts.upload_images --force    # re-uploads everything (e.g. after swapping in real photos)
"""
import json
import os
import sys
from pathlib import Path

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

IMAGES_DIR = Path("product-images")
PRODUCTS_PATH = Path("data/products.json")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> None:
    load_dotenv()  # reads CLOUDINARY_* from .env
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    force = "--force" in sys.argv

    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    # map "p001" -> Path("product-images/p001.jpg")
    files = {f.stem: f for f in IMAGES_DIR.iterdir() if f.suffix.lower() in EXTENSIONS}

    missing, uploaded = [], 0
    for product in products:
        pid = product["id"]
        image = files.get(pid)
        if image is None:
            missing.append(pid)
            continue
        if product.get("image_url") and not force:
            continue  # already uploaded earlier

        result = cloudinary.uploader.upload(
            str(image), public_id=pid, folder="products", overwrite=True
        )
        product["image_url"] = result["secure_url"]
        uploaded += 1
        print(f"uploaded {pid} -> {product['image_url']}")

    # write back, one product per line (same format as before)
    lines = ",\n".join("  " + json.dumps(p, ensure_ascii=False) for p in products)
    PRODUCTS_PATH.write_text("[\n" + lines + "\n]\n", encoding="utf-8")

    print(f"\nDone: {uploaded} uploaded.")
    if missing:
        print("No image file found for:", ", ".join(missing))


if __name__ == "__main__":
    main()