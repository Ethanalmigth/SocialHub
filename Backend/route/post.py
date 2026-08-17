from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from core.engine import get_db
from schema.ReponseAPI import ReponseAPI
from schema.post import PostResponse, PostCreate
from service.post import PostService
from utils.token import controle_access_token

router = APIRouter(prefix="/post",tags=["post"])
@router.post("/",status_code=status.HTTP_201_CREATED,response_model=ReponseAPI[PostResponse])
async def created_post(post:PostCreate,db:AsyncSession=Depends(get_db),payload=Depends(controle_access_token)):
    result= await PostService(db).create(post,payload["id"])
    return ReponseAPI(success=True, message="Post created successfully", data=result)

@router.get("/",response_model=ReponseAPI[List[PostResponse]],status_code=status.HTTP_200_OK)
async def get_all_posts(db:AsyncSession=Depends(get_db),payload=Depends(controle_access_token)):
    result=await PostService(db).get_all_posts(payload["id"])
    return ReponseAPI(success=True, data=result, message="Post list retrieved successfully")

@router.delete("/",status_code=status.HTTP_200_OK,response_model=ReponseAPI[PostResponse])
async def delete_post(post_id:UUID,db:AsyncSession=Depends(get_db),payload=Depends(controle_access_token)):
    print(payload)
    result=await PostService(db).delete_post(post_id,payload["id"])
    return ReponseAPI(success=True, message="Post deleted successfully", data=result)