from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.exception import CustomException

import logging
logger = logging.getLogger(__name__)
async def Custom_exception_handler(request:Request, exc:CustomException):
    return JSONResponse(status_code=exc.status_code,content={"message":exc.message,"success":False,"data":None})

async def Validation_exception_handler(request: Request, exc: RequestValidationError):
   errors= exc.errors()
   first_error=errors[0]
   field='.'.join(str (loc) for loc in first_error['loc'] )
   message=f"{field}: {first_error['msg']} " if field else first_error['msg']

   return JSONResponse(
       status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
       content={"message":message,"success":False,"data":None},
   )

async def Generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message":"Internal server error","success":False,"data":None},
    )


async def Integrity_error_handler(request: Request, exc: IntegrityError):
    logger.exception(f"Database integrity error on {request.method} {request.url}")

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "message": str(exc.orig),  # le message brut de la DB (asyncpg/psycopg)
            "success": False,
            "data": None,
        },
    )