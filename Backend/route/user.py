from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from core.engine import get_db
from schema.ReponseAPI import ReponseAPI
from schema.user import UserCreate, Userout, Userlogin
from service.user import UserService


router = APIRouter(prefix="/user", tags=["user"])
@router.post('/register',status_code=status.HTTP_201_CREATED,response_model=ReponseAPI[Userout])
async def register(user:UserCreate, db:AsyncSession=Depends(get_db)):
    result= await UserService(db).register_user(user)
    return ReponseAPI(success=True,message="user created successfully", data=result)

@router.post('/login',status_code=status.HTTP_200_OK,response_model=ReponseAPI[Userout])
async def login(user:Userlogin,db:AsyncSession=Depends(get_db)):
    result= await UserService(db).login_user(user)
    return ReponseAPI(success=True,message="user login successfully", data=result)

@router.post('/refresh',status_code=status.HTTP_200_OK,response_model=ReponseAPI[Userout])
async def refresh(token:str,db:AsyncSession=Depends(get_db)):
    result= await UserService(db).refresh(token)
    return ReponseAPI(success=True,message="user refresh successfully", data=result)

@router.post('/logout',status_code=status.HTTP_204_NO_CONTENT)
async def logout(id_user:UUID,db:AsyncSession=Depends(get_db)):
    await UserService(db).logout(id_user)
    return ReponseAPI(success=True,message="user logout successfully", data=None)