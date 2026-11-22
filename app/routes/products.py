from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import ServiceDep
from app.schemas import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product])
def list_products(
    svc: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return svc.index.products[offset : offset + limit]


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str, svc: ServiceDep):
    row = svc.index.row_of(product_id)
    if row is None:
        raise HTTPException(404, "Product not found")
    return svc.index.products[row]