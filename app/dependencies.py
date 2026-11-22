from typing import Annotated

from fastapi import Depends, Request

from app.service import RecommendationService


#Give route functions access to the service created at startup.
def get_service(request: Request):
    return request.app.state.service

ServiceDep = Annotated[RecommendationService, Depends(get_service)]