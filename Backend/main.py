from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from core.handler import Custom_exception_handler, Validation_exception_handler, Generic_exception_handler, \
    Integrity_error_handler
from route.user import router as UserRouter
app = FastAPI()
app.include_router(UserRouter, tags=["user"])
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
