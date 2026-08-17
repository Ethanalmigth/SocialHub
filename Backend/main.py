from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from core.handler import Custom_exception_handler, Validation_exception_handler, Generic_exception_handler, \
    Integrity_error_handler
from route.user import router as UserRouter
from route.publication import router as PublicationRouter
from route.post import router as PostRouter
app = FastAPI()
app.include_router(UserRouter)
app.include_router(PublicationRouter)
app.include_router(PostRouter)
app.add_exception_handler(CustomException,Custom_exception_handler)
app.add_exception_handler(RequestValidationError,Validation_exception_handler)
app.add_exception_handler(IntegrityError,Integrity_error_handler)
app.add_exception_handler(Exception,Generic_exception_handler)
@app.get("/")
def read_root():
    return {"Hello": "World"} 
   

"""
@app.get("/db-test")
async def test_db(db: AsyncSession = Depends(get_db)):
    return {"status": "DB connected"}
"""
