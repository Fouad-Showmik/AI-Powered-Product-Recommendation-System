from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    description: str
    rating: float = Field(ge=0, le=5)
    price: float | None = None
    category: str | None = None
    image_url: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int | None = Field(default=None, ge=1, le=100)
    threshold: float | None = Field(default=None, ge=-1.0, le=1.0)
    min_rating: float | None = Field(default=None, ge=0, le=5)


class FieldScores(BaseModel):
    name: float
    description: float
    rating: float | None = None  # only for product-to-product similarity


class RecommendationItem(BaseModel):
    product: Product
    score: float
    field_scores: FieldScores


class RecommendationResponse(BaseModel):
    mode: str  # "query" | "similar"
    threshold: float
    top_k: int
    count: int
    results: list[RecommendationItem]