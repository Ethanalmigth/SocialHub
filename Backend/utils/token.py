from datetime import timezone, datetime, timedelta

from fastapi import Header
from jose import jwt
from starlette import status

from core.exception import CustomException
from core.setting import settings

SECRET_KEY=settings.SECRET_KEY
REFRESH_TOKEN_KEY=settings.REFRESH_TOKEN
ALGORITHM=settings.ALGORITHM
ACCESS_TOKEN_EXPIRES_HOUR = settings.ACCESS_TOKEN_EXPIRES
REFRESH_TOKEN_EXPIRES_DAY = settings.REFRESH_TOKEN_EXPIRES




def create_token(data:dict)->str:
    to_encode = data.copy()
    time=datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRES_HOUR)
    to_encode.update({"exp":time, "type":"access"})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def create_refresh_token(data:dict,expiry:datetime)->str:
    to_encode = data.copy()
    to_encode.update({"exp":expiry, "type":"refresh"})
    return jwt.encode(to_encode,REFRESH_TOKEN_KEY,algorithm=ALGORITHM)

def verify_token(token:str, secret_type:str="access"):
    try:
        secret = REFRESH_TOKEN_KEY if secret_type == "refresh" else SECRET_KEY
        payload= jwt.decode(token,secret,algorithms=[ALGORITHM])
    except Exception as e:
        raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED,message=str(e))

    if payload.get("type") != secret_type:
        raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED,message="Wrong Token type")
    return payload

async def controle_access_token(authorization_code:str=Header(...))->dict:
    token=authorization_code.replace("Beazer ","")
    payload=verify_token(token,secret_type="access")
    return payload
