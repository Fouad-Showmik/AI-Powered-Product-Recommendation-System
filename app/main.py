import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.embeddings import Embedder, EmbeddingError
from app.index import InMemoryIndex
from app.routes import health, products, recommendations
from app.service import RecommendationService, load_catalog

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    embedder = Embedder(s.embedding_api_key, s.embedding_base_url, s.embedding_model)
    products_, name_vecs, desc_vecs = load_catalog(s.catalog_path, s.embedding_model)
    index = InMemoryIndex(products_, name_vecs, desc_vecs)
    app.state.service = RecommendationService(index, embedder, s)
    log.info("ready: %d products loaded from %s", len(index), s.catalog_path)
    yield


app = FastAPI(
    title="Product Recommendation Service",
    lifespan=lifespan,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(recommendations.router)


@app.exception_handler(EmbeddingError)
async def embedding_error_handler(_: Request, exc: EmbeddingError):
    log.error("embedding provider error: %s", exc)
    return JSONResponse(
        status_code=502, content={"detail": "Embedding provider unavailable"}
    )
