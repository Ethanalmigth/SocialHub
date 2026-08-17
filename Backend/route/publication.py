from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.engine import get_db
from schema.ReponseAPI import ReponseAPI
from schema.publication import PublicationCreate, PublicationResponse
from service.publication import PublicationService
from utils.token import controle_access_token

router=APIRouter(prefix="/publication",tags=["publication"])

@router.post("/{post_id}",response_model=ReponseAPI[PublicationResponse],status_code=status.HTTP_201_CREATED)
async def create_publication(publication:PublicationCreate,db:AsyncSession=Depends(get_db),payload=Depends(controle_access_token)):
    result = await PublicationService(db).create(publication,payload["id"])
    return ReponseAPI(message="Publication success",success=True,data=result)

@router.get("/{post_id}",response_model=ReponseAPI[List[PublicationResponse]])
async def get_all_publications(post_id,db:AsyncSession=Depends(get_db),payload=Depends(controle_access_token)):
    result = await PublicationService(db).get_publications_by_post(payload["id"],post_id)
    return ReponseAPI(message="Publication success",success=True,data=result)