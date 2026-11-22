from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    #Embedding API
    embedding_api_key: str
    embedding_base_url: str
    embedding_model: str

    #Files
    products_path: str
    catalog_path:str

    ## Weights for "similar to tapped product" 
    weight_name: float
    weight_description: float
    weight_rating: float

    default_top_k: int
    default_threshold: float

@lru_cache
def get_settings() -> Settings:
    return Settings()