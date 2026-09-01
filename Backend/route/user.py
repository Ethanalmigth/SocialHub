from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from core.engine import get_db
from model import RefreshToken
from schema.ReponseAPI import ReponseAPI
from schema.token import RefreshTokenRequest
from schema.user import UserCreate, Userout, Userlogin
from service.user import UserService
from utils.token import controle_access_token

router = APIRouter(prefix="/user", tags=["user"])
@router.post('/register',status_code=status.HTTP_201_CREATED,response_model=ReponseAPI[Userout],summary="User registration")
async def register(user:UserCreate, db:AsyncSession=Depends(get_db)):
    result= await UserService(db).register_user(user)
    return ReponseAPI(success=True,message="User created successfully", data=result)

@router.post('/login',status_code=status.HTTP_200_OK,response_model=ReponseAPI[Userout],summary="user login")
async def login(user:Userlogin,db:AsyncSession=Depends(get_db)):
    result= await UserService(db).login_user(user)
    return ReponseAPI(success=True,message="User login successfully", data=result)

@router.post('/refresh',status_code=status.HTTP_200_OK,response_model=ReponseAPI[Userout])
async def refresh(token:RefreshTokenRequest,db:AsyncSession=Depends(get_db)):
    result= await UserService(db).refresh(token.refresh_token)
    return ReponseAPI(success=True,message="user refresh successfully", data=result)

@router.post('/logout',status_code=status.HTTP_200_OK,response_model=ReponseAPI[Userout])
async def logout(db:AsyncSession=Depends(get_db),payload=Depends(controle_access_token)):
    result=await UserService(db).logout(payload["id"])
    return ReponseAPI(success=True,message="user logout successfully", data=result)