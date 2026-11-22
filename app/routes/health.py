from fastapi import APIRouter

from app.dependencies import ServiceDep

router = APIRouter(tags=["health"])

@router.get("/health")
@router.head("/health", include_in_schema=False)
def health(svc: ServiceDep):
    return {"status": "ok", "products": len(svc.index), "model": svc.embedder.model}