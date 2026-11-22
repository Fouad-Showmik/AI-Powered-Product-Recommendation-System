from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import ServiceDep
from app.schemas import RecommendationResponse, SearchRequest

router = APIRouter(tags=["recommendations"])


@router.post("/recommendations/search", response_model=RecommendationResponse)
def search(body: SearchRequest, svc: ServiceDep):
    return svc.search(body.query, body.top_k, body.threshold, body.min_rating)


@router.get("/products/{product_id}/similar", response_model=RecommendationResponse)
def similar(
    product_id: str,
    svc: ServiceDep,
    top_k: Annotated[int | None, Query(ge=1, le=100)] = None,
    threshold: Annotated[float | None, Query(ge=-1.0, le=1.0)] = None,
    min_rating: Annotated[float | None, Query(ge=0, le=5)] = None,
):
    result = svc.similar(product_id, top_k, threshold, min_rating)
    if result is None:
        raise HTTPException(404, "Product not found")
    return result